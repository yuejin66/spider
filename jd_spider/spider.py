import json
import re
import time
import logging
from datetime import datetime

from scrapy import Selector
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options

from jd_spider.models import MongoConfig

# 设置日志打印格式
logging.basicConfig(
    format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s',
    level=logging.INFO
)
options = Options()
# 设置无界面模式
options.add_argument("--headless")
# 谷歌文档提到需要加上这个属性来规避一些BUG
options.add_argument("--disable-gpu")
# 设置不加载图片
options.add_argument("blink-settings=imagesEnabled=false")
browser = webdriver.Chrome(
    executable_path="E:/liyuejin_project/spider_chrome_driver/chromedriver.exe",
    options=options
)


def str_to_int(nums_str):
    """
    char数字 -> int数字
    """
    nums = 0
    re_math = re.search("(\d+)", nums_str)
    if re_math:
        nums = int(re_math.group(1))
        if "万" in nums_str:
            nums *= 10000
    return nums


def parse_goods(goods_id):
    logging.info("开始抓取商品的基础信息...")
    browser.get("https://item.jd.com/{}.html".format(goods_id))
    selector = Selector(text=browser.page_source)
    name = "".join(selector.xpath("//div[@class='sku-name']/text()").extract()).strip()
    price = float("".join(selector.xpath("//span[@class='price J-p-{}']/text()".format(goods_id)).extract()).strip())
    content = "".join(selector.xpath("//div[@id='detail']//div[@class='tab-con']").extract()).strip()
    slideshow = json.dumps(selector.xpath("//div[@id='spec-list']//img/@src").extract())  # 商品轮播图
    if selector.xpath("//div[@id='summary-service']/a/text()").extract():
        supplier_info = selector.xpath("//div[@id='summary-service']/a/text()").extract()[0]  # 供应商信息
    else:
        supplier_info = "京东"

    # 模拟点击"规格与包装"
    browser.find_element_by_xpath("//div[@class='tab-main large']//li[contains(text(), '规格与包装')]").click()
    time.sleep(3)  # 等待5s来加载js数据
    selector = Selector(text=browser.page_source)

    # 模拟点击"商品评价"
    browser.find_element_by_xpath("//div[@class='tab-main large']//li[contains(text(), '商品评价')]").click()
    time.sleep(3)
    selector = Selector(text=browser.page_source)
    favorable_rate = int(selector.xpath("//div[@class='percent-con']/text()").extract()[0])  # 点赞数
    summary_as = selector.xpath("//ul[@class='filter-list']/li/a")

    # 获取商品的评价分类
    logging.info("开始抓取商品的评价分类信息...")
    comments_categories = {}
    for summary in summary_as:
        evaluate_name = summary.xpath("./text()").extract()[0]
        nums_str = summary.xpath("./em/text()").extract()[0]
        nums = str_to_int(nums_str)
        if evaluate_name == "晒图":
            comments_categories["has_image_comment_nums"] = nums
        elif evaluate_name == "视频晒单":
            comments_categories["has_video_comment_nums"] = nums
        elif evaluate_name == "追评":
            comments_categories["has_add_comment_nums"] = nums
        elif evaluate_name == "好评":
            comments_categories["good_comment_nums"] = nums
        elif evaluate_name == "中评":
            comments_categories["middle_comment_nums"] = nums
        elif evaluate_name == "差评":
            comments_categories["bad_comment_nums"] = nums
        elif evaluate_name == "全部评价":
            comments_categories["comments_nums"] = nums
    comments_tags = []  # 评价标签
    tag_list = selector.xpath("//div[@class='tag-list tag-available']/span/text()").extract()
    for tag in tag_list:
        re_match = re.match("(.*)\((\d+)\)", tag)
        if re_match:
            tag_name = re_match.group(1)
            tag_nums = int(re_match.group(2))
            comment_summary = {
                "tag_name": tag_name,
                "tag_nums": tag_nums
            }
            comments_tags.append(comment_summary)

    # 获取商品的评价详细信息
    logging.info("开始抓取商品的评价详情信息...")
    has_next_page = True
    comments_details = []
    while has_next_page:
        detail = selector.xpath("//div[@class='comment-item']")
        for item in detail:
            comments_id = item.xpath("./@data-guid").extract()[0]
            user_avatar_url = item.xpath(".//div[@class='user-info']/img/@src").extract()[0]
            user_name = "".join(item.xpath(".//div[@class='user-info']/text()").extract()).strip()
            star = int(item.xpath("./div[2]/div[1]/@class").extract()[0][-1])
            detail_content = "".join(item.xpath("./div[2]/p[1]/text()").extract()[0]).strip()
            image_list = item.xpath("./div[2]//div[@class='pic-list J-pic-list']/a/img/@src").extract()
            video_list = item.xpath("./div[2]//div[@class='J-video-view-wrap clearfix']//video/@src").extract()
            user_praised_nums = int(item.xpath(".//div[@class='comment-op']/a[2]/text()").extract()[0])
            user_comment_nums = int(item.xpath(".//div[@class='comment-op']/a[3]/text()").extract()[0])
            user_order_info = item.xpath(".//div[@class='order-info']/span/text()").extract()
            order_info = json.dumps(user_order_info[:-1])
            order_time = datetime.strptime(user_order_info[-1], "%Y-%m-%d %H:%M")
            user_comment_detail = {  # 用户评论的详情信息
                "comments_id": comments_id,
                "user_avatar_url": user_avatar_url,
                "user_name": user_name,
                "star": star,
                "detail_content": detail_content,
                "image_list": image_list,
                "video_list": video_list,
                "user_praised_nums": user_praised_nums,
                "user_comment_nums": user_comment_nums,
                "order_info": order_info,
                "order_time": order_time,
            }
            comments_details.append(user_comment_detail)
        try:  # 下一页
            next_page = browser.find_element_by_xpath("//div[@id='comment']//a[@class='ui-pager-next']")
            next_page.send_keys("\n")  # click的另一种用法
            time.sleep(1)
            selector = Selector(text=browser.page_source)
        except NoSuchElementException as e:
            has_next_page = False

    # 保存商品的所有信息
    comments = {  # 商品评价
        "comments_categories": comments_categories,
        "comments_tags": comments_tags,
        "comments_details": comments_details,
    }
    goods_info = {  # 商品信息
        "name": name,
        "price": price,
        "content": content,
        "slideshow": slideshow,
        "favorable_rate": favorable_rate,
        "supplier_info": supplier_info,
        "comments": comments,
    }
    logging.info("数据抓取完成，开始进行数据存档...")
    collection = MongoConfig.get_database()["goodsInfo"]
    collection.update_one({"_id": goods_id}, {'$set': {"goodsInfo": goods_info}}, upsert=True)
    logging.info("数据存档成功")


if __name__ == "__main__":
    parse_goods(100012341882)

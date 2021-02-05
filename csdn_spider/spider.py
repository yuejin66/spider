"""
    1. 抓取
    2. 解析
    3. 存储
"""
import re
import ast
import time
from urllib import parse

import requests
from scrapy import Selector
from datetime import datetime

from csdn_spider.models import *

url_list = []
domain = "https://bbs.csdn.net"


#
def get_nodes_json():
    left_menu_text = requests.get("https://bbs.csdn.net/dynamic_js/left_menu.js?csdn").text
    nodes_str_match = re.search("forumNodes: (.*])", left_menu_text)
    if nodes_str_match:
        nodes_str = nodes_str_match.group(1).replace("null", "None")
        nodes_list = ast.literal_eval(nodes_str)
        return nodes_list
    return []


# 将js的格式提取出url到list中
def process_nodes_list(nodes_list):
    for item in nodes_list:
        if "url" in item:
            if item["url"]:
                url_list.append(item["url"])
            if "children" in item:
                process_nodes_list(item["children"])


def get_level1_list(nodes_list):
    level1_url = []
    for item in nodes_list:
        if "url" in item and item["url"]:
            url_list.append(item["url"])
    return level1_url


# 获取最终需要抓取的url
def get_last_urls():
    nodes_list = get_nodes_json()
    process_nodes_list(nodes_list)
    level1_url = get_level1_list(nodes_list)
    last_urls = []
    for url in url_list:
        if url not in level1_url:
            last_urls.append(url)
    # 默认为【待解决】，还有【已解决】和【推荐精华】
    all_urls = []
    for url in last_urls:
        all_urls.append(parse.urljoin(domain, url))
        all_urls.append(parse.urljoin(domain, url + "/recommend"))
        all_urls.append(parse.urljoin(domain, url + "/closed"))
    return all_urls


# 获取帖子的详情以及回复
def parse_topic(topic_url):
    topic_id = topic_url.split("/")[-1]
    res_text = requests.get(topic_url).text
    selector = Selector(text=res_text)
    all_divs = selector.xpath("//div[starts-with(@id, 'post-')]")
    topic_item = all_divs[0]
    # TODO: 如何提取div下的text？要求全部为有格式的String文本
    content = topic_item.xpath(".//div[@class='post_body post_body_min_h']").extract()[0]
    praised_nums = topic_item.xpath(".//label[@class='red_praise digg d_hide']//em/text()").extract()[0]
    jtl_str = topic_item.xpath(".//div[@class='close_topic']/text()").extract()[0]
    jtl = 0
    jtl_match = re.search("(\d+)%", jtl_str)
    if jtl_match:
        jtl = int(jtl_match.group(1))
    existed_topics = Topic.select().where(Topic.id == topic_id)
    if existed_topics:
        topic = existed_topics[0]
        topic.content = content
        topic.jtl = jtl
        topic.praised_nums = praised_nums
        topic.save()
    for answer_item in all_divs[1:]:
        answer = Answer()
        answer.topic_id = topic_id
        author_info = answer_item.xpath(".//div[@class='nick_name']//a[1]/@href").extract()[0]
        author_id = author_info.split("/")[-1]
        create_time_str = answer_item.xpath(".//label[@class='date_time']/text()").extract()[0]
        create_time = datetime.strptime(create_time_str, "%Y-%m-%d %H:%M:%S")
        answer.author = author_id
        answer.create_time = create_time
        praised_nums = topic_item.xpath(".//label[@class='red_praise digg d_hide']//em/text()").extract()[0][-1]
        if praised_nums == " ":
            answer.praised_nums = 0
        else:
            answer.praised_nums = int(praised_nums)
        content = topic_item.xpath(".//div[@class='post_body post_body_min_h']").extract()[0]
        answer.content = content
        answer.save()
    # 下一页
    next_page = selector.xpath("//a[@class='pageliststy next_page']/@href").extract()
    if next_page:
        next_url = parse.urljoin(domain, next_page[0])
        parse_list(next_url)


# TODO: 出现F12页面信息和get到的html不相等情况，以后有空回头再解决
# 获取用户的详情
def parse_author(author_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/88.0.4315.5 Mobile Safari/537.36 '
    }
    res_text = requests.get(author_url, headers=headers).text
    time.sleep(0.5)
    selector = Selector(text=res_text)
    original_nums = selector.xpath("//div[@class='data-info d-flex item-tiling']/dl[1]/dd/a/span/text()").extract()[0]
    first_dls = selector.xpath("//div[@class='data-info d-flex item-tiling']/dl/dd/span/text()").extract()
    follower_nums = first_dls[0]
    praised_nums = first_dls[1]
    comment_nums = first_dls[2]
    second_dls = selector.xpath("//div[@class='grade-box clearfix']/dl/dd/text()").extract()
    PV_nums = second_dls[2]
    integral_nums = second_dls[3]
    total_rankings_nums = second_dls[4].strip()
    pass


# 解析获取到的 url列表内容
def parse_list(list_url):
    res_text = requests.get(list_url).text
    selector = Selector(text=res_text)
    all_trs = selector.xpath(".//table[@class='forums_tab_table']//tr")[2:]  # 从第二个开始取
    for tr in all_trs:
        topic = Topic()
        if tr.xpath(".//td[1]/span/text()").extract():
            topic.status = tr.xpath("//td[1]/span/text()").extract()[0]
        if tr.xpath(".//td[2]/em/text()").extract():
            topic.score = int(tr.xpath("//td[2]/em/text()").extract()[0])
        # TODO: 将这些都用if装起来
        topic_url = parse.urljoin(domain, tr.xpath(".//td[3]/a/@href").extract()[1])
        topic_title = tr.xpath(".//td[3]/a/text()").extract()[0]
        author_url = parse.urljoin(domain, tr.xpath(".//td[4]/a/@href").extract()[0])
        author_id = author_url.split("/")[-1]
        create_time_str = tr.xpath(".//td[4]/em/text()").extract()[0]
        create_time = datetime.strptime(create_time_str, "%Y-%m-%d %H:%M")
        answer_info = tr.xpath(".//td[5]/span/text()").extract()[0]
        answer_nums = answer_info.split("/")[0]
        click_nums = answer_info.split("/")[1]
        last_time_str = tr.xpath(".//td[6]/em/text()").extract()[0]
        last_time = datetime.strptime(last_time_str, "%Y-%m-%d %H:%M")

        topic.id = int(topic_url.split("/")[-1])  # 主键
        topic.title = topic_title
        topic.author = author_id
        topic.click_nums = int(click_nums)
        topic.answer_nums = int(answer_nums)
        topic.create_time = create_time
        topic.last_answer_time = last_time
        existed_topics = Topic.select().where(Topic.id == topic.id)
        # 保存
        if existed_topics:
            topic.save()
        else:
            topic.save(force_insert=True)
        # 帖子详情
        # parse_topic(topic_url)
        # 用户详情
        parse_author(author_url)

        # 下一页
        next_page = selector.xpath("//a[@class='pageliststy next_page']/@href").extract()
        if next_page:
            next_url = parse.urljoin(domain, next_page[0])
            parse_list(next_url)


if __name__ == "__main__":
    last_urls = get_last_urls()
    for url in last_urls:
        parse_list(url)

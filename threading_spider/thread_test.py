from selenium import webdriver
from scrapy import Selector


browser = webdriver.Chrome(executable_path="E:/liyuejin_project/spider_chrome_driver/chromedriver.exe")
browser.get("https://item.jd.com/12585508.html")
selector = Selector(text = browser.page_source)

money = selector.xpath("//span[@class='price J-p-12585508']/text()").extract_first()

click_element = browser.find_element_by_xpath("//li[@clstag='shangpin|keycount|product|shangpinpingjia_3']")
click_element.click()


pass

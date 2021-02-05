import time
from io import BytesIO

from selenium import webdriver
from PIL import Image

url = "https://www.douban.com/"
login_url = "https://accounts.douban.com/passport/login_popup?login_source=anony"
browser = webdriver.Chrome(
    executable_path="E:/liyuejin_project/spider_chrome_driver/chromedriver.exe",
)


def crop_captcha_img(img_file_name):
    """
    截取验证码图片
    """
    # TODO: 在frame嵌套的数据会出现滑动验证码位置变动的情况，从而导致截图不正确
    time.sleep(1)
    browser.switch_to.frame(browser.find_element_by_xpath("//iframe[@id='tcaptcha_iframe']"))
    img = browser.find_element_by_xpath("//div[@id='slideBgWrap']")
    location = img.location
    size = img.size
    upper, lower = location["y"], location["y"] + size["height"]
    left, right = location["x"], location["x"] + size["width"]
    screenshot_png = browser.get_screenshot_as_png()
    screenshot = Image.open(BytesIO(screenshot_png))
    tuple_img = (int(left), int(upper), int(right), int(lower))
    captcha_img = screenshot.crop(tuple_img)
    captcha_img.save(img_file_name)
    return captcha_img


def login():
    username = "13727764936"
    password = "q525130121."
    browser.get(url)
    browser.maximize_window()  # 窗口最大化
    browser.switch_to.frame(browser.find_element_by_xpath("//div[@class='login']/iframe[1]"))  # 跳到frame里面
    browser.find_element_by_xpath("//div[@class='account-body-tabs']/ul[1]/li[2]").click()
    browser.find_element_by_xpath("//input[@id='username']").send_keys(username)
    browser.find_element_by_xpath("//input[@id='password']").send_keys(password)
    browser.find_element_by_xpath("//div[@class='account-tabcon-start']/div[1]/div[5]/a").click()
    # 截取里面的图片
    crop_captcha_img("test.png")


if __name__ == "__main__":
    login()


import binascii
import time
import base64
from urllib.parse import quote_plus

import rsa
import requests

"""
    最近微博强制网页登录需要手机扫码，此项目不更新
"""

# pic = "https://login.sina.com.cn/cgi/pin.php?r=66972280&s=0&p=gz-bd23d4eb7830ce7140b74573433ac26689a0"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/88.0.4315.5 Safari/537.36"
}
index_url = "http://weibo.com/login.php"
# 访问初始页面带上 cookie
session = requests.session()
session.get(index_url, headers=headers, timeout=2)


def get_su(username):
    """
    1. 对账号使用 JavaScript 中的 encodeURIComponent
    2. base64 加密后再 decode
    """
    username_quote = quote_plus(username)
    username_base64 = base64.b64encode(username_quote.encode("utf-8"))
    return username_base64.decode("utf-8")


def get_server_data(su):
    """
    预登录获得 servertime, nonce, pubkey, rsakv 4个参数
    """
    current_time = str(int(time.time() * 1000))
    # pre_url = "https://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&" \
    #           "su=&rsakt=mod&client=ssologin.js(v1.4.19)&_={}".format(current_time)
    pre_url = "https://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su=" \
              "{}&rsakt=mod&client=ssologin.js(v1.4.19)&_={}".format(su, current_time)
    pre_data_res = session.get(pre_url, headers=headers)
    sever_data = eval(pre_data_res.content.decode("utf-8").replace("sinaSSOController.preloginCallBack", ""))
    return sever_data


def get_password(password, servertime, nonce, pubkey):
    """

    """
    rsa_public_key = int(pubkey, 16)
    key = rsa.PublicKey(rsa_public_key, 65537)  # 创建公钥
    message = str(servertime) + '\t' + str(nonce) + '\n' + str(password)  # 拼接明文js加密文件中得到
    message = message.encode("utf-8")
    rsa_password = rsa.encrypt(message, key)  # 加密
    return binascii.b2a_hex(rsa_password)  # 将加密信息转换为16进制。


def login(username, password):
    su = get_su(username)  # su：加密后的用户名
    server_data = get_server_data(su)
    servertime = server_data["servertime"]
    nonce = server_data["nonce"]
    rsakv = server_data["rsakv"]
    pubkey = server_data["pubkey"]
    showpin = server_data["showpin"]
    password_secret = get_password(password, servertime, nonce, pubkey)
    post_data = {
        'entry': 'weibo',
        'gateway': '1',
        'from': '',
        'savestate': '7',
        'useticket': '1',
        'pagerefer': "http://login.sina.com.cn/sso/logout.php?entry=miniblog&r=http%3A%2F%2Fweibo.com%2Flogout.php"
                     "%3Fbackurl",
        'vsnf': '1',
        'su': su,
        'service': 'miniblog',
        'servertime': servertime,
        'nonce': nonce,
        'pwencode': 'rsa2',
        'rsakv': rsakv,
        'sp': password_secret,
        'sr': '1366*768',
        'encoding': 'UTF-8',
        'prelt': '115',
        'url': 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
        'returntype': 'META'
    }


if __name__ == "__main__":
    username = "13727764936"
    password = "lyj525130121."
    login(username, password)

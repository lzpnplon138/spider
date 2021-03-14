import requests
import re

try:
    import cookielib
except:
    import http.cookiejar as cookielib


def zhihu_login(account, password):
    # 知乎登陆
    if re.match('^1\d{10}', account):
        print('手机号码登陆')
        post_url = 'https://www.zhihu.com/login/phone_num'
        post_data = {
            '_xsrf': '',
            'phone_num': account,
            'password': password
        }
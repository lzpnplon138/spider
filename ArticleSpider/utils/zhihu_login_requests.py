import requests
import re

try:
    import cookielib
except:
    import http.cookiejar as cookielib

session = requests.session()
session.cookies = cookielib.LWPCookieJar(filename='cookies.txt')

try:
    session.cookies.load(ignore_discard=True)
except:
    print('cookie未能加载')

agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75 Safari/537.36"
headers = {
    'Host': 'www.zhihu.com',
    'Referer': 'https://www.zhihu.com',
    'User-Agent': agent
}


def get_xsrf():
    """获取xsrf code"""
    response = session.get('https://www.zhihu.com', headers=headers)
    match_obj = re.search('.*<input type="hidden" name="_xsrf" value="(.*?)"/', response.text)

    if match_obj:
        return match_obj.group(1)
    else:
        return ''


def zhihu_login(account, password):
    """知乎登陆"""
    if re.match('^1\d{10}', account):
        print('手机号码登陆')
        post_url = 'https://www.zhihu.com/login/phone_num'
        post_data = {
            '_xsrf': get_xsrf(),
            'phone_num': account,
            'password': password
        }
        response_text = session.post(post_url, data=post_data, headers=headers)
        session.cookies.save()
    else:
        if "@" in account:
            # 判断用户名是否为邮箱
            print("邮箱方式登录")
            post_url = "https://www.zhihu.com/login/email"
            post_data = {
                '_xsrf': get_xsrf(),
                'email': account,
                'password': password
            }
            response_text = session.post(post_url, data=post_data, headers=headers)
            session.cookies.save()


def get_index():
    response = session.get("https://www.zhihu.com", headers=headers)
    with open("index_page.html", "wb") as f:
        f.write(response.text.encode("utf-8"))
    print("ok")


def is_login():
    """通过个人中心页面返回状态码来判断是否为登录状态"""
    inbox_url = "https://www.zhihu.com/question/56250357/answer/148534773"
    response = session.get(inbox_url, headers=headers, allow_redirects=False)
    if response.status_code != 200:
        return False
    else:
        return True


zhihu_login('17757177075', '11250519lnmj.')

# get_index()

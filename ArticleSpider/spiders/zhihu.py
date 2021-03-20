# -*- coding: utf-8 -*-
import re
import time
from PIL import Image
from urllib import parse
import json
import scrapy


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    headers = {
        'Host': 'www.zhihu.com',
        'Referer': 'https://www.zhihu.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75 Safari/537.36'
    }

    # 知乎需要登录才能爬取, 重写scrapy.Spider.start_requests方法
    def start_requests(self):
        t = str(int(time.time() * 1000))
        captcha_url = "https://www.zhihu.com/captcha.gif?r={0}&type=login&lang=en".format(t)
        return [(scrapy.Request(captcha_url, headers=self.headers, callback=self.parse_captcha))]

    def parse_captcha(self, response):
        """保存验证码图片并手动输入"""
        with open("captcha.jpg", "wb") as f:
            f.write(response.body)
            f.close()
        try:
            im = Image.open('captcha.jpg')
            im.show()
            im.close()
        except Exception as e:
            print(e)

        captcha = input("输入验证码\n>")
        return scrapy.Request(url='https://www.zhihu.com/', headers=self.headers, callback=self.login,
                              meta={'captcha': captcha})

    def login(self, response):
        match_obj = re.match('.*name="_xsrf" value="(.*?)"/', response.text, re.DOTALL)
        if match_obj:
            xsrf = match_obj.group(1)
            if xsrf:
                return [scrapy.FormRequest(
                    url='https://www.zhihu.com/login/phone_num',
                    method='POST',
                    formdata={
                        'phone_num': '17757177075',
                        'password': '11250519lnmj.',
                        '_xsrf': xsrf,
                        'captcha_type': 'en',
                        'captcha': response.meta['captcha'],
                    },
                    headers=self.headers,
                    callback=self.check_login
                )]

    def check_login(self, response):
        """验证服务器的返回数据判断是否成功"""
        text_json = json.loads(response.text)
        if 'msg' in text_json and text_json['msg'] == '登录成功':
            for url in self.start_urls:
                yield scrapy.Request(url, dont_filter=True, headers=self.headers)

    def parse(self, response):
        """
        提取出html页面的所有url, 并跟踪这些url进一步爬取,
        如果提取的url中格式为 /question/xxxx 就下载之后直接进入解析函数
        """
        all_urls = response.css('a::attr(href)').extract()
        all_urls = filter(lambda x: True if x.startswith('https') else False,
                          [parse.urljoin(response.url, url) for url in all_urls])
        for url in all_urls:
            match_obj = re.match('(.*zhihu.com/question/(\d+))(/|$).*', url)
            if match_obj:
                request_url = match_obj.group(1)
                question_id = match_obj.group(2)

    def parse_question(self, response):
        pass

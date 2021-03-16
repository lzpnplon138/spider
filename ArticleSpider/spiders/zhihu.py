# -*- coding: utf-8 -*-
import re
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

    def parse(self, response):
        pass

    # 知乎需要登录才能爬取, 重写scrapy.Spider.start_requests方法
    def start_requests(self):
        return [(scrapy.Request('https://www.zhihu.com/#signin', callback=self.login))]

    def login(self, response):
        response = session.get('https://www.zhihu.com', headers=headers)
        match_obj = re.search('.*<input type="hidden" name="_xsrf" value="(.*?)"/', response.text)
        xsrf = ''
        if match_obj:
            xsrf = match_obj.group(1)

        if xsrf:
            post_url = 'https://www.zhihu.com/login/phone_num'
            post_data = {
                '_xsrf': xsrf,
                'phone_num': '1757177075',
                'password': '********'
            }

            return [scrapy.FormRequest(
                url=post_url,
                formdata=post_data,
                headers=self.headers,
                callback=
            )]


    def check_login(self, response):
        """验证服务器的返回数据判断是否成功"""


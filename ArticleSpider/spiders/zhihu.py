# -*- coding: utf-8 -*-
import re
import time
import datetime
from PIL import Image
from urllib import parse
import json
import scrapy
from scrapy.loader import ItemLoader

from ArticleSpider.items import ZhihuAnswerItem, ZhihuQuestionItem


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    # question的第一页answer的请求url
    start_answer_url = 'https://www.zhihu.com/api/v4/questions/{0}/answers?include=data%5B*%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B*%5D.mark_infos%5B*%5D.url%3Bdata%5B*%5D.author.follower_count%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics&offset={2}&limit={1}&sort_by=default'

    headers = {
        'Host': 'www.zhihu.com',
        'Referer': 'https://www.zhihu.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75 Safari/537.36'
    }

    # 设置自己的setting
    custom_settings = {
        'COOKIES_ENABLED': True
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

                yield scrapy.Request(request_url, headers=self.headers, meta={'question_id': int(question_id)},
                                     callback=self.parse_question)
            else:
                yield scrapy.Request(url, headers=self.headers, callback=self.parse)

    def parse_question(self, response):
        """处理问题函数"""
        item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
        item_loader.add_value('zhihu_id', response.meta.get('question_id', ''))
        item_loader.add_css('title', 'h1.QuestionHeader-title::text')
        item_loader.add_css('content', '.QuestionRichText')
        item_loader.add_value('url', response.url)
        item_loader.add_css('answer_num', '.List-headerText span::text')
        item_loader.add_css('comments_num', '.QuestionHeader-Comment > button::text')
        item_loader.add_css('watch_user_num', '.NumberBoard-item .NumberBoard-value::text')
        item_loader.add_css('click_num', '.NumberBoard-item .NumberBoard-value::text')
        item_loader.add_css('topics', '.TopicLink .Popover div::text')

        question_item = item_loader.load_item()

        yield scrapy.Request(self.start_answer_url.format(response.meta.get('question_id', ''), 20, 0),
                             headers=self.headers, callback=self.parse_answer)

        yield question_item
        # 此处也需要对页面进行爬取, 同parse函数

    def parse_answer(self, response):
        """处理问题的回答, 返回json数据"""
        answers = json.loads(response.text)
        is_end = answers['paging']['is_end']
        next_url = answers['paging']['next']

        # 提取answer的具体结构
        for answer in answers['data']:
            answer_item = ZhihuAnswerItem()
            answer_item['zhihu_id'] = answer['id']
            answer_item['url'] = answer['url']
            answer_item['question_id'] = answer['question']['id']
            answer_item['author_id'] = answer['author']['id'] if 'id' in answer['author'] else None
            answer_item['content'] = answer['content'] if 'content' in answer else None
            answer_item['praise_num'] = answer['voteup_count']
            answer_item['comments_num'] = answer['comment_count']
            answer_item['create_time'] = answer['created_time']
            answer_item['update_time'] = answer['updated_time']
            answer_item['crawl_time'] = datetime.datetime.now()

            yield answer_item

        if not is_end:
            yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_answer)

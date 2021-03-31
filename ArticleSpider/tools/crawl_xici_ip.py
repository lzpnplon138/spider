# -*- encoding: utf-8 -*-
import requests
import MySQLdb
from scrapy.selector import Selector
from fake_useragent import UserAgent


class SqlConnection(object):
    __instance = None

    def __init__(self):
        self.conn = MySQLdb.connect(host="192.168.4.40", user="root", passwd="123456", db="article", charset="utf8")

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(SqlConnection, cls).__new__(cls)
        return cls.__instance


def crawl_ips():
    ua = UserAgent()
    conn = SqlConnection().conn
    for i in range(1, 100):
        headers = {"User-Agent": ua.random}
        response = requests.get('http://www.xicidaili.com/nn/{0}'.format(i), headers=headers)
        selector = Selector(text=response.text)

        all_trs = selector.css('#ip_list tr:not(:nth-child(1))')

        for tr in all_trs:
            speed = tr.css('.bar::attr(title)').extract()[0].split('秒')[0]
            speed = float(speed) if speed else 0.0
            ip = tr.css('td:nth-child(2)::text').extract()[0]
            port = tr.css('td:nth-child(3)::text').extract()[0]
            proxy_type = tr.css('td:nth-child(6)::text').extract()[0]
            cursor = conn.cursor()
            cursor.execute(
                """insert proxy_ip(ip, port, speed, proxy_type) 
                    VALUES('{0}', '{1}', {2}, '{3}') 
                    ON DUPLICATE KEY UPDATE ip=VALUES(ip), port=VALUES(port), speed=VALUES(speed), 
                    proxy_type=VALUES(proxy_type)""".format(ip, port, speed, proxy_type)
            )
            conn.commit()

    conn.close()


class GetIP(object):
    def __init__(self):
        self.conn = SqlConnection().conn
        self.cursor = self.conn.cursor()

    def delete_ip(self, ip):
        """从数据库中删除无效的ip"""
        delete_sql = 'delete from proxy_ip where ip={0}'.format(ip)
        self.cursor.execute(delete_sql)
        self.conn.commit()
        self.conn.close()
        return True

    def judge_ip(self, ip, port, proxy_type):
        """判断ip是否可用"""
        http_url = "http://www.baidu.com"
        proxy_url = "{2}://{0}:{1}".format(ip, port, proxy_type)
        try:
            proxy_dict = {
                proxy_type: proxy_url,
            }
            response = requests.get(http_url, proxies=proxy_dict)
        except Exception as e:
            print("invalid ip and port")
            self.delete_ip(ip)
            return False
        else:
            code = response.status_code
            if 200 <= code < 300:
                print("effective ip")
                self.conn.close()
                return True
            else:
                print("invalid ip and port")
                self.delete_ip(ip)
                return False

    def get_random_ip(self):
        """从数据库中随机获取一个可用的ip"""
        random_sql = 'SELECT ip, port, proxy_type FROM proxy_ip ORDER BY RAND() LIMIT 1'

        self.cursor.execute(random_sql)

        for ip_info in self.cursor.fetchall():
            ip = ip_info[0]
            port = ip_info[1]
            proxy_type = ip_info[2]

            judge_re = self.judge_ip(ip, port, proxy_type)
            if judge_re:
                return "{2}://{0}:{1}".format(ip, port, proxy_type)
            else:
                return self.get_random_ip()


if __name__ == '__main__':
    print(GetIP().get_random_ip())
    crawl_ips()

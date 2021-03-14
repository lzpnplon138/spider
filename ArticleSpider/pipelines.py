# -*- coding: utf-8 -*-
import codecs
import json
import MySQLdb
import MySQLdb.cursors
from scrapy.exporters import JsonItemExporter
from twisted.enterprise import adbapi

from scrapy.pipelines.images import ImagesPipeline


class ArticleSpiderPipeline(object):
    def process_item(self, item, spider):
        return item


class JsonWithEncodingPipeline(object):
    # 自定义json文件的导出
    def __init__(self):
        self.file = codecs.open('article.json', 'w', encoding='utf-8')

    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + '\n'
        self.file.write(lines)
        return item

    def close_spider(self, spider):
        self.file.close()


class JsonExporterPipeline(object):
    # 调用scrapy提供的json exporter 导出json文件
    def __init__(self):
        self.file = open('article_exporter.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding='utf-8', ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item


# 后期mysql存储速度跟不上爬取速度, 会阻塞
class MysqlPipeline(object):
    def __init__(self):
        self.conn = MySQLdb.connect(host='192.168.4.40', user='root', password='123456', db='article',
                                    charset='utf8', use_unicode=True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = """
            insert into jobbole_article(title, url, url_object_id, create_date, content)
            VALUES (%s, %s, %s, %s, %s)
        """
        self.cursor.execute(insert_sql,
                            (item['title'], item['url'], item['url_object_id'], item['create_date'], item['content']))
        self.conn.commit()


# 异步插入mysql
class MysqlTwistedPipeline(object):
    def __init__(self, db_pool):
        self.db_pool = db_pool

    @classmethod
    def from_settings(cls, settings):
        db_params = dict(
            host=settings['MYSQL_HOST'],
            user=settings['MYSQL_USER'],
            password=settings['MYSQL_PASSWORD'],
            db=settings['MYSQL_DB'],
            charset='utf8',
            use_unicode=True,
            cursorclass=MySQLdb.cursors.DictCursor
        )
        db_pool = adbapi.ConnectionPool('MySQLdb', **db_params)
        return cls(db_pool)

    def process_item(self, item, spider):
        # 使用twisted将mysql插入变成异步执行
        query = self.db_pool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error)  # 处理异常

    def handle_error(self, failure):
        # 处理异步插入的异常
        print(failure)

    def do_insert(self, cursor, item):
        insert_sql = """
          insert into jobbole_article(title, url, url_object_id, create_date, content)
          VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_sql,
                       (item['title'], item['url'], item['url_object_id'], item['create_date'], item['content']))


class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        if 'front_image_path' in item:
            for stat, value in results:
                image_path = value['path']
            item['front_image_path'] = image_path

        return item

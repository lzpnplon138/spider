# -*- coding: utf-8 -*-
import codecs
import json
import MySQLdb

from scrapy.pipelines.images import ImagesPipeline
from scrapy.exporters import JsonItemExporter


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

    def spider_closed(self, spider):
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



class MysqlPipeline(object):
    def __init__(self):
        self.conn = MySQLdb.connect(host='192.168.4.40', user='root', password='123456')


class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        for stat, value in results:
            image_path = value['path']
        item['front_image_path'] = image_path

        return item

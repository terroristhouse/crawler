# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import pymysql
from scrapy import Request
from scrapy.exceptions import DropItem
from scrapy.pipelines.images import ImagesPipeline

class ScmjwPipeline:
    def process_item(self, item, spider):
        return item

class MysqlPipeline:
    def __init__(self,host,database,user,password):
        self.host = host
        self.database = database
        self.user = user
        self.password = password

    def open_spider(self,spider):
        self.conn = pymysql.connect(self.host,self.user,self.password,self.database,charset='utf8')
        self.cursor = self.conn.cursor()
        # self.old_url = set()
        # search_sql = "select url from scmjw"
        # self.cursor.execute(search_sql)
        # for i in self.cursor.fetchall():
        #     self.old_url.add(i[0])

    def process_item(self,item,spider):
        # if item['url'] in self.old_url:
        #     print('数据已入库',item['title'])
        #     raise DropItem
        print('数据下载中',item['title'])
        data = dict(item)
        keys = ', '.join(data.keys())
        values = ', '.join(['% s'] * len(data))
        sql = 'insert into % s (% s) values (% s)' % (item.table, keys, values)
        self.cursor.execute(sql, tuple(data.values()))
        self.conn.commit()
        return item


    def close_spider(self,spider):
        self.cursor.close()
        self.conn.close()

    @classmethod
    def from_crawler(cls,crawler):
        return cls(
            host=crawler.settings.get('MYSQL_HOST'),
            database=crawler.settings.get('MYSQL_DATABASE'),
            user=crawler.settings.get('MYSQL_USER'),
            password=crawler.settings.get('MYSQL_PASSWORD'),
        )


class ImagePipeline(ImagesPipeline):
    def file_path(self, request, response=None, info=None):
        url = request.url
        file_name = url.split('?')[0].split('/')[-1]
        return file_name

    def item_completed(self, results, item, info):
        image_paths = [x['path'] for ok, x in results if ok]
        if not image_paths:
            raise DropItem('Image Downloaded Failed')
        return item

    def get_media_requests(self, item, info):
        if item['beiyong1']:
            yield Request(item['beiyong1'])

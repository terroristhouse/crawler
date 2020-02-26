# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


class MymultispiderPipeline(object):
    def process_item(self, item, spider):
        if spider.name == 'myspd1':
            print('myspd1的pipelines')
        elif spider.name == 'myspd2':
            print('myspd2的pipelines')
        elif spider.name == 'myspd3':
            print('myspd3的pipelines')
        return item



class Myspd1spiderPipeline(object):
    def process_item(self,item,spider):
        print(item['name'])
        return item

class Myspd2spiderPipeline(object):
    def process_item(self,item,spider):
        print(item['name'])
        return item

class Myspd3spiderPipeline(object):
    def process_item(self,item,spider):
        print(item['name'])
        return item















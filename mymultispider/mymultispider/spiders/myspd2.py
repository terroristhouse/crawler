# -*- coding: utf-8 -*-
import scrapy
from mymultispider.items import Myspd2spiderItem

class Myspd2Spider(scrapy.Spider):
    name = 'myspd2'
    allowed_domains = ['sina.com.cn']
    start_urls = ['http://sina.com.cn/']
    # custom_settings = {
    #     'ITEM_PIPELINES': {'mymultispider.pipelines.Myspd2spiderPipeline': 300},
    # }
    def parse(self, response):
        print('myspd2')
        item = Myspd2spiderItem()
        item['name'] = 'myspd2的pipelines'
        yield item
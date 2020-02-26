# -*- coding: utf-8 -*-
import scrapy
from mymultispider.items import Myspd1spiderItem

class Myspd1Spider(scrapy.Spider):
    name = 'myspd1'
    allowed_domains = ['sina.com.cn']
    start_urls = ['http://sina.com.cn/']
    # custom_settings = {
    #     'ITEM_PIPELINES': {'mymultispider.pipelines.Myspd1spiderPipeline': 300},
    # }

    def parse(self, response):

        print('myspd1')
        item = Myspd1spiderItem()
        item['name'] = 'myspd1的pipelines'
        yield item
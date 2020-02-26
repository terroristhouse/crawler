# -*- coding: utf-8 -*-
import scrapy
from mymultispider.items import Myspd3spiderItem

class Myspd3Spider(scrapy.Spider):
    name = 'myspd3'
    allowed_domains = ['sina.com.cn']
    start_urls = ['http://sina.com.cn/']
    # custom_settings = {
    #     'ITEM_PIPELINES': {'mymultispider.pipelines.Myspd3spiderPipeline': 300},
    # }
    def parse(self, response):
        print('myspd3')
        item = Myspd3spiderItem()
        item['name'] = 'myspd3的pipelines'
        yield item

        # https://github.com/terroristhouse/crawler.git
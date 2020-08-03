# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ScmjwItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    table = 'scmjw'
    url = scrapy.Field()
    category = scrapy.Field()
    title = scrapy.Field()
    auther = scrapy.Field()
    dynasty = scrapy.Field()
    content = scrapy.Field()
    contents = scrapy.Field()
    amount = scrapy.Field()
    beiyong1 = scrapy.Field()

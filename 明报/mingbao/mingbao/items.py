# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class MingbaoItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    URL = scrapy.Field()
    title = scrapy.Field()
    sort2_ID = scrapy.Field()
    standbyID = scrapy.Field()
    content = scrapy.Field()
    publishtime = scrapy.Field()
    LASTUPDATE = scrapy.Field()
    HTMLCONTENT = scrapy.Field()
    authorID = scrapy.Field()
    UniqURL = scrapy.Field()
    ENCODING = scrapy.Field()
    SITE = scrapy.Field()
    CATEGORYCODE = scrapy.Field()
    PARENTID = scrapy.Field()
    PAGETITLE = scrapy.Field()
    CANBEPUBLISHED = scrapy.Field()
    NETRESOURCETYPE = scrapy.Field()
    source = scrapy.Field()
    lang = scrapy.Field()
    zoneID = scrapy.Field()
    columnID = scrapy.Field()
    image_url = scrapy.Field()

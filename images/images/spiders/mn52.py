# -*- coding: utf-8 -*-
import scrapy
import requests
from lxml import etree
from images.items import ImagesItem

class Mn52Spider(scrapy.Spider):
    name = 'mn52'
    # allowed_domains = ['www.mn52.com']
    # start_urls = ['http://www.mn52.com/']

    def start_requests(self):
        response = requests.get('https://www.mn52.com/')
        result = etree.HTML(response.text)
        li_lists = result.xpath('//*[@id="bs-example-navbar-collapse-2"]/div/ul/li')
        for li in li_lists:
            url = li.xpath('./a/@href')[0]
            field_name = li.xpath('./a/text()')[0]
            print('https://www.mn52.com' + url,field_name)
            yield scrapy.Request('https://www.mn52.com' + url,meta={'field_name':field_name},callback=self.parse)

    def parse(self, response):
        field_name = response.meta['field_name']
        div_lists = response.xpath('/html/body/section/div/div[1]/div[2]/div')
        for div_list in div_lists:
            detail_urls = div_list.xpath('./div/a/@href').extract_first()
            detail_name = div_list.xpath('./div/a/@title').extract_first()
            yield scrapy.Request(url='https:' + detail_urls,callback=self.get_image,meta={'detail_name':detail_name,'field_name':field_name})
        url_lists = response.xpath('/html/body/section/div/div[3]/div/div/nav/ul/li')
        for url_list in url_lists:
            next_url = url_list.xpath('./a/@href').extract_first()
            if next_url:
                yield scrapy.Request(url='https:' + next_url,callback=self.parse,meta=response.meta)


    def get_image(self,response):
        field_name = response.meta['field_name']
        image_urls = response.xpath('//*[@id="originalpic"]/img/@src').extract()
        for image_url in image_urls:
            item = ImagesItem()
            item['image_url'] = 'https:' + image_url
            item['field_name'] = field_name
            item['detail_name'] = response.meta['detail_name']
            # print(item['image_url'],item['field_name'],item['detail_name'])
            yield item

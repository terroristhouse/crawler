# -*- coding: utf-8 -*-
import scrapy
from scmjw.items import ScmjwItem

class ScmjSpider(scrapy.Spider):
    name = 'scmj'
    # allowed_domains = ['www.shicimingju.com']
    start_urls = ['http://www.shicimingju.com']

    def parse(self, response):
        list_urls = response.xpath('//div[@id="top_left_menu"]/ul/li')
        for list_url in list_urls:
            main_list = 'http://www.shicimingju.com' + list_url.xpath('./a/@href').extract_first()
            if 'shicimark' in main_list:
                print(main_list)
                yield scrapy.Request(url=main_list,callback=self.get_list)
            if 'category' in main_list:
                print(main_list)
                yield scrapy.Request(url=main_list,callback=self.get_list_cate)

    """爬取分类类别"""
    def get_list(self,response):
        div_lists = response.xpath('//div[@class="mark_card"]')
        for d in div_lists:
            item = ScmjwItem()
            next_url = 'http://www.shicimingju.com' + d.xpath('./a/@href').extract_first()
            images = d.xpath('./a/img/@src').extract_first()
            item['beiyong1'] = images
            yield scrapy.Request(url=next_url,callback=self.get_cate,meta={'item':item})

    def get_cate(self,response):
        item = response.meta['item']
        next_urls = response.xpath('//a[contains(text(), "《") and contains(text(), "》")]')
        item['amount'] = response.xpath('//div[@class="card"]/h1/text()').re_first('\d+')
        for n in next_urls:
            next_url = 'http://www.shicimingju.com' + n.xpath('./@href').extract_first()
            yield scrapy.Request(url=next_url,callback=self.get_detail,meta={'item':item})
        self_urls = response.xpath('//a[contains(text(), "下一页")]/@href').extract_first()
        if self_urls:
            self_url = 'http://www.shicimingju.com' + self_urls
            yield scrapy.Request(url=self_url, callback=self.get_cate, meta={'item': item})

    def get_detail(self,response):
        item = response.meta['item']
        item['url'] = response.request.url
        item['category'] = response.xpath('//div[@class="shici-mark"]/a/text()').extract_first()
        item['title'] = response.xpath('//div[@id="item_div"]/h1/text()').extract_first()
        item['auther'] = response.xpath('//div[@class="niandai_zuozhe"]/a/text()').extract_first()
        item['dynasty'] = response.xpath('//div[@class="niandai_zuozhe"]/text()').extract_first()
        contents = response.xpath('//div[@class="item_content"]//text()').extract()
        content = ''
        for c in contents:
            content += c.strip() + '\n'
        item['content'] = content
        shangxi_contents = response.xpath('//div[@class="shangxi_content"]//text()').extract()
        contents = ''
        for s in shangxi_contents:
            contents += s.strip()
        item['contents'] = contents
        yield item

    """爬取作者类别"""
    def get_list_cate(self,response):
        div_lists = response.xpath('//div[@class="card zuozhe_card"]')
        for d in div_lists:
            next_url = 'http://www.shicimingju.com' + d.xpath('./div[@class="zuozhe_list_item"]/h3/a/@href').extract_first()
            yield scrapy.Request(url=next_url,callback=self.get_zuozhe)
        self_urls = response.xpath('//a[contains(text(), "下一页")]/@href').extract_first()
        if self_urls:
            self_url = 'http://www.shicimingju.com' + self_urls
            yield scrapy.Request(url=self_url, callback=self.get_list_cate)

    def get_zuozhe(self,response):
        item = ScmjwItem()
        item['amount'] = response.xpath('//div[@class="card shici_card"]/h1/text()').re_first('\d+')
        next_urls = response.xpath('//div[@class="shici_list_main"]')
        for n in next_urls:
            next_url = 'http://www.shicimingju.com' + n.xpath('./h3/a/@href').extract_first()
            yield scrapy.Request(url=next_url,callback=self.get_z_detail,meta={'item':item})
        self_urls = response.xpath('//a[contains(text(), "下一页")]/@href').extract_first()
        if self_urls:
            self_url = 'http://www.shicimingju.com' + self_urls
            yield scrapy.Request(url=self_url, callback=self.get_zuozhe)

    def get_z_detail(self,response):
        item = response.meta['item']
        item['url'] = response.request.url
        item['category'] = response.xpath('//div[@class="shici-mark"]/a/text()').extract_first()
        item['title'] = response.xpath('//div[@id="item_div"]/h1/text()').extract_first()
        item['auther'] = response.xpath('//div[@class="niandai_zuozhe"]/a/text()').extract_first()
        item['dynasty'] = response.xpath('//div[@class="niandai_zuozhe"]/text()').extract_first()
        contents = response.xpath('//div[@class="item_content"]//text()').extract()
        content = ''
        for c in contents:
            content += c.strip() + '\n'
        item['content'] = content
        shangxi_contents = response.xpath('//div[@class="shangxi_content"]//text()').extract()
        contents = ''
        for s in shangxi_contents:
            contents += s.strip()
        item['contents'] = contents
        by1 = response.xpath('//div[@id="item_div"]/img/@src').extract_first()
        if by1:
            item['beiyong1'] = by1
        else:
            item['beiyong1'] = ''
        yield item

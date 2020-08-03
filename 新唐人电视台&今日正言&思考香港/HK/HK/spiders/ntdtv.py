# -*- coding: utf-8 -*-
import scrapy
from HK.langconv import *
from HK.settings import today_url
from HK.items import HkItem
import time
class NtdtvSpider(scrapy.Spider):
    name = 'ntdtv'
    # allowed_domains = ['www.ntdtv.com']
    start_urls = ['https://www.ntdtv.com/b5/news']
    custom_settings = {
        'ITEM_PIPELINES': {'HK.pipelines.SqlserverTVPipeline': 300,
                           'HK.pipelines.DowonImageTVPipeline': 302,
                           },
    }
    Q = None
    # 繁体转简体
    def j(self, line):
        line = Converter("zh-hans").convert(line)
        return line

    def parse(self, response):
        # self.Q.put('新唐人电视台开始爬取')
        div_lists = response.xpath('//div[@class="list-episodes"]')
        for div_list in div_lists:
            lists_url = div_list.xpath('./div/a/@href').extract_first()
            # print(lists_url)
            yield scrapy.Request(url=lists_url,callback=self.get_list)

    def get_list(self,response):
        item = HkItem()
        sort2_id = response.xpath('//div[@class="post_list"]/h1/span/text()').extract_first().strip()
        item['sort2_ID'] = self.j(sort2_id)
        detail_urls = response.xpath('//div[@class="list_wrapper"]/div[@class="one_post"]')
        for detail_uri in detail_urls:
            detail_url = detail_uri.xpath('.//a/@href').extract_first()
            yield scrapy.Request(url=detail_url,callback=self.get_detail,meta={'item':item})

    def get_detail(self,response):
        item = response.meta['item']
        publishtime = response.xpath('//div[@class="article_info"]/div[@class="time"]/span/text()').extract_first()
        if publishtime:
            publishtime = publishtime.split(' ')[0]
        if publishtime != today_url:
            return
        ID = 1
        detail_url = response.request.url
        URL = detail_url
        URLFORPUBLISH = ''
        UniqURL = detail_url
        LASTUPDATE = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        ENCODING = 'big5-hkscs'
        SITE = 5
        CATEGORYCODE = '0'
        PARENTID = -1
        PAGETITLES = response.xpath('//title/text()').extract_first()
        PAGETITLE = ''
        if PAGETITLES:
            PAGETITLE = PAGETITLES
        CANBEPUBLISHED = 1
        NETRESOURCETYPE = 256
        # HTMLCONTENT = response.content.decode("utf-8")
        HTMLCONTENT = ''
        STREAMCONTENT = ''
        title = response.xpath('//div[@class="article_title"]/h1/text()').extract_first()

        if title:
            title = title.replace('「', '“').replace('」', '”')

        source = '新唐人电视台'
        # content_lists = response.xpath(
        #     '//div[@id="upper"]/p/text() | //div[@id="lower"]/div[@class="articlelogin"]//p/text() | //div[@id="lower"]/div[@class="articlelogin"]//h2/text() | //div[@id="lower"]/div[@class="articlelogin"]//a/text()').extract()
        content_lists = response.xpath('//div[@class="post_content"]//p')

        content = ''
        for content_list in content_lists:
            content += '　　' + content_list.xpath('string(.)').extract_first().replace('「', '“').replace('」','”') + '\n\n'
        lang = 'TC'
        authorID = ''

        sortID = ''
        layoutID = ''

        standbyIDS = response.xpath('//div[@class="featured_image"]/a/@href|//div[@class="featured_image"]/span/text()').extract()
        if len(standbyIDS) < 2:
            standbyIDS = response.xpath('//div[@class="featured_image"]/a/figure/img/@src|//div[@class="featured_image"]/a/figure/img/@alt').extract()
            if standbyIDS:
                standbyIDS[0],standbyIDS[1] = standbyIDS[1],standbyIDS[0]
        standbyID = ''
        image_url = []

        if standbyIDS:
            standbyID += '〈br〉　　〈img src="http://picture.chinesedata.org/PIC_ZX/%s" border=0〉〈br〉AABIBCC %s CCBIBAA〈/br〉' % (
                standbyIDS[0].split('//')[-1].replace('i.ntdtv.com','i_ntdtv_com'),standbyIDS[1]) + '\n'
            image_url.append(standbyIDS[0])
        #         http://picture.chinesedata.org/PIC_ZX/thinkhk/www_thinkhk_com/d/file/2020-03-12/b47da2a9482c8de2cc28629a366c7ca8.jpg

        zoneID = '香港>'
        columnID = '报纸>综合'
        standby2_ID = ''
        standby3_ID = ''
        UNIQUEID = ''
        AUTOADDCLMN = 1

        item['URL'] = URL
        item['title'] = self.j(title)
        # item['sort2_ID'] = self.j(sort2_ID)
        item['standbyID'] = self.j(standbyID)
        item['content'] = self.j(content)
        item['publishtime'] = publishtime
        item['LASTUPDATE'] = LASTUPDATE
        item['HTMLCONTENT'] = HTMLCONTENT
        item['authorID'] = self.j(authorID)
        item['UniqURL'] = UniqURL
        item['ENCODING'] = ENCODING
        item['SITE'] = SITE
        item['CATEGORYCODE'] = CATEGORYCODE
        item['PARENTID'] = PARENTID
        item['PAGETITLE'] = self.j(PAGETITLE)
        item['CANBEPUBLISHED'] = CANBEPUBLISHED
        item['NETRESOURCETYPE'] = NETRESOURCETYPE
        item['source'] = source
        item['lang'] = lang
        item['zoneID'] = zoneID
        item['columnID'] = columnID
        item['image_url'] = image_url
        # print(content)
        # self.Q.put("数据下载中：{}".format(item['title']))
        yield item

    # def close(spider, reason):
    #     spider.Q.put('新唐人电视台爬取结束')





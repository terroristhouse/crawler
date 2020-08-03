# -*- coding: utf-8 -*-
import scrapy
import time
from HK.items import HkItem
from HK.langconv import *
from HK.settings import today_url

class Todayreview88Spider(scrapy.Spider):
    name = 'todayreview88'
    # allowed_domains = ['www.todayreview88.com']
    start_urls = ['https://todayreview88.com/']
    custom_settings = {
        'ITEM_PIPELINES': {'HK.pipelines.Sqlservertodayipeline': 302,
                           'HK.pipelines.DowonImagetodayPipeline': 402,
                           },
    }
    Q = None

    # 繁体转简体
    def j(self, line):
        line = Converter("zh-hans").convert(line)
        return line

    def parse(self, response):
        # self.Q.put('今日正言开始爬取')
        div_lists = response.xpath('//ul[@class="nav navbar-nav"]/li')
        for div_list in div_lists:
            list_urls = div_list.xpath('./a/@href').extract_first()
            for i in range(1,3):
                yield scrapy.Request(url=list_urls + '?page=%s'%i,callback=self.get_list)

    def get_list(self,response):
        li_lists=  response.xpath('//ul[@class="media-list"]/li')
        for li_list in li_lists:
            detail_url = li_list.xpath('.//div[@class="media-heading"]/a/@href').extract_first()
            yield scrapy.Request(url=detail_url,callback=self.get_detail)


    def get_detail(self,response):
        item = HkItem()
        publishtime = ''
        publishtimes = response.xpath('//section[@class="featured-media"]/img/@src').extract_first()
        if publishtimes:
            publishtime = publishtimes.split('/')[-2]
        # print(publishtime)
        # today = '20200313'
        # if publishtime != today:
        #     return
        if publishtime != time.strftime('%Y%m%d'):
            return
        sort2_ID = response.xpath('//li[@class="active"]/a/text()').extract_first()
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
        title = response.xpath('//h1[@class="post-title"]/text()').extract_first()

        if title:
            title = title.replace('「', '“').replace('」', '”')

        source = '今日正言'
        # content_lists = response.xpath(
        #     '//div[@id="upper"]/p/text() | //div[@id="lower"]/div[@class="articlelogin"]//p/text() | //div[@id="lower"]/div[@class="articlelogin"]//h2/text() | //div[@id="lower"]/div[@class="articlelogin"]//a/text()').extract()
        content_lists = response.xpath('//section[@class="post-content clearfix"]//p')

        content = ''
        for content_list in content_lists:
            content += '　　' + content_list.xpath('string(.)').extract_first().replace('「', '“').replace('」',
                                                                                                        '”') + '\n\n'
        lang = 'TC'
        authorID = ''

        sortID = ''
        layoutID = ''

        standbyIDS = response.xpath(
            '//section[@class="featured-media"]/img/@src|//section[@class="featured-media"]/img/@alt').extract()

        standbyID = ''
        image_url = []

        if standbyIDS:
            standbyID += '〈br〉　　〈img src="http://picture.chinesedata.org/PIC_ZX/%s" border=0〉〈br〉AABIBCC %s CCBIBAA〈/br〉' % (
                standbyIDS[0].split('//')[-1].replace('img.todayreview88.com', 'img_todayreview88_com').rstrip('!s800'), standbyIDS[1]) + '\n'
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
        item['sort2_ID'] = self.j(sort2_ID)
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
        # self.Q.put("数据下载中：{}".format(item['title']))
        yield item

    # def close(spider, reason):
    #     spider.Q.put('今日正言爬取结束')

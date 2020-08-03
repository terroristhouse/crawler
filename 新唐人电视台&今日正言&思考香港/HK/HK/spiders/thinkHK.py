# -*- coding: utf-8 -*-
import scrapy
import time
from HK.items import HkItem
from HK.langconv import *
from HK.settings import today_url


class ThinkhkSpider(scrapy.Spider):
    name = 'thinkHK'
    # allowed_domains = ['www.xxx.com']
    start_urls = ['https://www.thinkhk.com/']
    custom_settings = {
        'ITEM_PIPELINES': {'HK.pipelines.SqlserverPipeline': 300,
                           'HK.pipelines.DowonImagePipeline': 302,
                           },
    }
    Q = None
    # 繁体转简体
    def j(self, line):
        line = Converter("zh-hans").convert(line)
        return line

    def parse(self, response):
        # self.Q.put('思考香港开始爬取')
        div_lists = response.xpath('//div[@class="navBar"]/a[@class="nav"]/@href').extract()
        for div_list in div_lists:
            if div_list != '/':
                list_url = 'https://www.thinkhk.com' + div_list
                yield scrapy.Request(url=list_url, callback=self.get_list)
                # for i in range(1,3):
                #     if i == 1:
                #         yield scrapy.Request(url=list_url, callback=self.get_list)
                #     else:
                #         yield scrapy.Request(url=list_url + '/index_%s.html'%i,callback=self.get_list)

    # 到详情页的url获取
    def get_list(self,response):
        # print(response.url)
        sort2_id = response.xpath('//div[@class="sideTit bgW"]/text()').extract_first()
        if '/bayarea' in response.url:
            sort2_id = '大灣區'
        li_lists = response.xpath('//ul[@class="newsList"]/li')
        item = HkItem()
        item['sort2_ID'] = self.j(sort2_id)
        for li_list in li_lists:
            detail_urls = li_list.xpath('./a/@href').extract_first()
            detail_time = li_list.xpath('//span[@class="gray"]/text()').extract_first()
            # print(detail_time,today_url,detail_time == today_url)
            detail_url = 'https://www.thinkhk.com' + detail_urls
            yield scrapy.Request(url=detail_url,callback=self.get_detail,meta={'item':item})


    def get_detail(self,response):
        item = response.meta['item']
        publishtime = response.xpath('//div[@class="gray font14"]/text()').extract_first()
        if publishtime != today_url:
            return
        # print(response.url)

        # sort2_ID = response.xpath('//div[@class="navBar"]/a[@class="nav dq"]/text()').extract_first()
        # if not sort2_ID:
        #     sort2_ID = ''
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
        title = response.xpath('//div[@class="content"]/h1/text()').extract_first()
        if title:
            title = title.replace('「', '“').replace('」', '”')


        source = '思考香港'
        # content_lists = response.xpath(
        #     '//div[@id="upper"]/p/text() | //div[@id="lower"]/div[@class="articlelogin"]//p/text() | //div[@id="lower"]/div[@class="articlelogin"]//h2/text() | //div[@id="lower"]/div[@class="articlelogin"]//a/text()').extract()
        content_lists = response.xpath('//div[@class="content"]//p|//div[@class="content"]//div[not(@class)]')


        content = ''
        for content_list in content_lists:
            content += '　　' + content_list.xpath('string(.)').extract_first().replace('「','“').replace('」', '”').replace(u'\xa0','') + '\n\n'
        lang = 'TC'
        authorID = ''

        sortID = ''
        layoutID = ''

        standbyIDS = response.xpath('//div[@class="content"]//p//img|//div[@class="content"]//div[not(@class)]//img')
        standbyID = ''
        image_url = []
        for standbyID_1 in standbyIDS:
            standbyID_2 = standbyID_1.xpath('./@src').extract_first()

            if standbyID_2:
                standbyID += '〈br〉　　〈img src="http://picture.chinesedata.org/PIC_ZX/thinkhk/www_thinkhk_com%s" border=0〉〈br〉AABIBCC  CCBIBAA〈/br〉' % (
                    standbyID_2) + '\n'
                image_url.append('https://www.thinkhk.com' + standbyID_2)
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
        # self.Q.put("数据下载中：{}".format(item['title']))
        yield item

    # def close(spider, reason):
    #     spider.Q.put('思考香港爬取结束')




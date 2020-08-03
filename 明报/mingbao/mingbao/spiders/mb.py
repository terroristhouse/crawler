# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request,FormRequest
from mingbao.settings import today_url,UserName,Password
import time,re
from mingbao.langconv import *
from mingbao.items import MingbaoItem
from lxml import etree
import json

class MbSpider(scrapy.Spider):
    name = 'mb'
    # allowed_domains = ['www.news.mingpao.com']
    start_urls = [
            # 要闻
            'https://news.mingpao.com/pns/%E8%A6%81%E8%81%9E/section/{}/s00001'.format(today_url),
            # 港闻
            'https://news.mingpao.com/pns/%E6%B8%AF%E8%81%9E/section/{}/s00002'.format(today_url),
            # 经济
            'https://news.mingpao.com/pns/%E7%B6%93%E6%BF%9F/section/{}/s00004'.format(today_url),
            # 娱乐
            'https://news.mingpao.com/pns/%E5%A8%9B%E6%A8%82/section/{}/s00016'.format(today_url),
            # 社评
            'https://news.mingpao.com/pns/%E7%A4%BE%E8%A9%95/section/{}/s00003'.format(today_url),
            # 观点(部分需登录)(笔阵，闻风笔动)
            'https://news.mingpao.com/pns/%E8%A7%80%E9%BB%9E/section/{}/s00012'.format(today_url),
            # 中国
            'https://news.mingpao.com/pns/%E4%B8%AD%E5%9C%8B/section/{}/s00013'.format(today_url),
            # 国际
            'https://news.mingpao.com/pns/%E5%9C%8B%E9%9A%9B/section/{}/s00014'.format(today_url),
            # 教育(部分需登录)(通通识，常识学堂)
            'https://news.mingpao.com/pns/%E6%95%99%E8%82%B2/section/{}/s00011'.format(today_url),
            # 体育
            'https://news.mingpao.com/pns/%E9%AB%94%E8%82%B2/section/{}/s00015'.format(today_url),
            # 副刊
            'https://news.mingpao.com/pns/%E5%89%AF%E5%88%8A/section/{}/s00005'.format(today_url),
            # 英文
            'https://news.mingpao.com/pns/%E8%8B%B1%E6%96%87/section/{}/s00017'.format(today_url),
            # 作家专栏(需要登录)
            'https://news.mingpao.com/pns/%E4%BD%9C%E5%AE%B6%E5%B0%88%E6%AC%84/section/{}/s00018'.format(today_url),

        ]

    # 繁体转简体
    def j(self, line):
        line = Converter("zh-hans").convert(line)
        return line

    def parse(self, response):

        # exit()
        # 社评
        editorial_detail_url = response.xpath('//div[@id="maincontent"]/div[@class="group"]/div[@class="col span_8_of_12"]/div[starts-with(@class,"headline")]/div[starts-with(@class,"headcontent")]/div[@class="inontent_wrapper"]/div[@class="inontent"]/a/@href').extract_first()
        if editorial_detail_url:
            editorial_detail_url = 'https://news.mingpao.com' + editorial_detail_url.lstrip('..')
            # print(editorial_detail_url)
            yield scrapy.Request(url=editorial_detail_url,callback=self.get_deail,meta={'sort2_ID':''})


        # 获取首个文章url
        first_detail_url = response.xpath('//div[@id="maincontent"]/div[@class="group"]/div[@class="col span_8_of_12"]/div[starts-with(@class,"headline")]/div[starts-with(@class,"right")]/a/@href').extract_first()
        if first_detail_url:
            first_detail_url = 'https://news.mingpao.com' + first_detail_url.lstrip('..')
            # print(first_detail_url)
            yield scrapy.Request(url=first_detail_url, callback=self.get_deail,meta={'sort2_ID':''})


        # 获取列表中的文章url
        div_lists = response.xpath('//div[@id="maincontent"]/div[@class="group"]/div[@class="col span_8_of_12"]/div[starts-with(@class,"cat")]/div[starts-with(@class,"listing")] | //div[@id="maincontent"]/div[@class="group"]/div[@class="col span_8_of_12"]/div[starts-with(@class,"cat")]/div[starts-with(@class,"listing")]/div | //div[@id="maincontent"]/div[@class="group"]/div[@class="col span_8_of_12"]/div[@class="headline2"]/div[starts-with(@class,"cat")]/div[starts-with(@class,"listing")]')
        # print(div_lists)
        for div_list in div_lists:
            sort2_IDs = div_list.xpath('./h2/text()').extract_first()
            if sort2_IDs:
                if sort2_IDs == '港聞二 ' or sort2_IDs == '港聞一 ':
                    sort2_ID = '港聞'
                else:
                    sort2_ID = sort2_IDs
            else:
                sort2_ID = ''
            li_lists = div_list.xpath('./ul/li')
            # print(li_lists)
            for li_list in li_lists:
                detail_url = li_list.xpath('./a/@href').extract_first()
                if detail_url:
                    detail_url = 'https://news.mingpao.com' + detail_url.lstrip('..')
                    # print(detail_url)
                    yield scrapy.Request(url=detail_url, callback=self.get_deail,meta={'sort2_ID':sort2_ID})

    def get_deail(self,response):
        item = MingbaoItem()
        sort2_ID = response.meta['sort2_ID']
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
        title = response.xpath('//*[@id="blockcontent"]/hgroup/h1/text()').extract_first()
        if title:
            title = title.replace('「', '“').replace('」', '”')
        # publishtime = time.strftime('%Y-%m-%d', time.localtime())
        publishtime = today_url
        source = '明报'
        # content_lists = response.xpath(
        #     '//div[@id="upper"]/p/text() | //div[@id="lower"]/div[@class="articlelogin"]//p/text() | //div[@id="lower"]/div[@class="articlelogin"]//h2/text() | //div[@id="lower"]/div[@class="articlelogin"]//a/text()').extract()
        content_lists = response.xpath(
            '//div[@id="upper"]/p | //div[@id="lower"]/div[@class="articlelogin"]//p | //div[@id="lower"]/div[@class="articlelogin"]//h2')


        standbyID_login = ''

        content = ''
        for content_list in content_lists:
            content += '　　' + content_list.xpath('string(.)').extract_first().replace('\\', '').replace('「','“').replace('」','”') + '\n\n'
        lang = 'TC'
        authorID = ''

        #  / ／
        # # 作家专栏中寻找作者
        if '%E4%BD%9C%E5%AE%B6%E5%B0%88%E6%AC%84'.lower() in detail_url:
            if title:
                if '/' in title:
                    authorID = title.split('/')[-1].strip()  # / 谭蕙芸
                    title = title.replace('/ ' + authorID, '').strip()

        # # 观点&经济
        elif '%E8%A7%80%E9%BB%9E'.lower() in detail_url or '%E7%B6%93%E6%BF%9F'.lower() in detail_url:
            if title:
                if '／' in title and '：' in title:
                    authorID = title.split('／')[-1].split('：')[-1]
                    title = title.replace('／文：' + authorID, '').strip()
                elif '：' in title:
                    authorIDs = title.split('：')[0]
                    if len(authorIDs) < 4:
                        authorID = authorIDs
                        title = title.replace(authorID + '：', '').strip()

        # 标题中作者
        elif title:
            if '／' in title and '：' in title:
                authorID = title.split('／')[-1].split('：')[-1]
                title = title.replace('／文：' + authorID, '').strip()
            elif '／' in title:
                authorID = title.split('／')[-1].strip()
                title = title.replace('／' + authorID, '').strip()

        # 内容中作者
        if content:
            authorIDs = re.findall('\n文：(.*?)\n', content)
            if authorIDs:
                authorID = authorIDs[0].strip()
            else:
                authorIDs = re.findall('記者：(.*?)\n', content)
                if authorIDs:
                    authorID = authorIDs[0].strip()

        sortID = ''
        layoutID = ''
        if not sort2_ID:
            sort2_ID = response.xpath('//*[@id="menusection"]//*[@id="current"]/text()').extract_first()
            if sort2_ID:
                sort2_ID = sort2_ID

        standbyIDS = response.xpath('//div[@id="zoomedimg"]/div')
        standbyID = ''
        image_url = []
        for standbyID_1 in standbyIDS:
            standbyID_2 = standbyID_1.xpath('./a/img/@data-original | ./a/img/@alt').extract()
            if standbyID_2:
                standbyID += '〈br〉　　〈img src="http://picture.chinesedata.org/PIC_ZX/mingpao/%s" border=0〉〈br〉AABIBCC %s CCBIBAA〈/br〉' % (
                    standbyID_2[0].split('//')[-1], standbyID_2[1]) + '\n'
                image_url.append(standbyID_2[0])

                # self.download_image(standbyID_2[0].replace('\\', ''))
        if standbyID_login:
            standbyID = standbyID_login

        zoneID = '香港>'
        columnID = '报纸>综合'
        standby2_ID = ''
        standby3_ID = ''
        UNIQUEID = ''
        AUTOADDCLMN = 1

        item['URL'] = URL
        item['title'] = self.j(title.replace("''",'"'))
        item['sort2_ID'] = self.j(sort2_ID)
        item['standbyID'] = self.j(standbyID.replace('fs.mingpao.com', 'fs_mingpao_com'))
        item['content'] = self.j(content.replace("''",'"'))
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


        # 获取会员文章内容
        login_detail_url = detail_url.split('/')[-2]
        log_data = {
            'issue': '%s' % today_url,
            'node': '%s' % login_detail_url
        }
        login_url = 'https://news.mingpao.com/php/login3.php'
        yield scrapy.FormRequest(url=login_url, formdata=log_data, callback=self.login_detail, meta={'cookiejar': 1,'item':item})


    # 旧物遗言 / 刘小花
    def login_detail(self,response):
        item = response.meta['item']
        dict1 = json.loads(response.text)

        content_result = dict1['TextContent']
        log_content = ''
        if content_result:
            res = etree.HTML(content_result)
            contents = res.xpath('//p | //h2')
            for content_list in contents:
                log_content += '　　' + content_list.xpath('string(.)').replace('\\', '').replace('「', '“').replace('」', '”') + '\n\n'
        item['content'] = item['content'] + self.j(log_content.replace("''",'"'))

        image_result = dict1['LargeMedia']
        standbyID = ''
        image_url = []
        if image_result:
            image_res = etree.HTML(image_result)
            image_data = image_res.xpath('//a')
            for image_1 in image_data:
                standbyIDs = image_1.xpath('./img/@data-original | ./img/@alt')
                if standbyIDs:
                    standbyID += '〈br〉　　〈img src="http://picture.chinesedata.org/PIC_ZX/mingpao/%s" border=0〉〈br〉AABIBCC %s CCBIBAA〈/br〉' % (
                        standbyIDs[0].replace('\\', '').split('//')[-1], standbyIDs[1]) + '\n'
                    image_url.append(standbyIDs[0].replace('\\', ''))
                    # self.download_image(standbyIDs[0].replace('\\', ''))
            item['standbyID'] = item['standbyID'] + self.j(standbyID.replace('fs.mingpao.com', 'fs_mingpao_com'))
        if image_url:
            item['image_url'] = image_url
        yield item


    # 重写初始方法，进行模拟登录
    login_url = 'https://news.mingpao.com/php/login2.php'

    def start_requests(self):
        yield Request(url=self.login_url, meta = {'cookiejar':1}, callback=self.login)

    def login(self, response):
        data = {'UserName': UserName, 'Password': Password}
        yield FormRequest(self.login_url, formdata=data,meta = {'cookiejar':response.meta['cookiejar']}, callback=self.parse_login)

    def parse_login(self, response):
        for url in self.start_urls:
            yield Request(url=url,meta={'cookiejar':1},callback=self.parse)


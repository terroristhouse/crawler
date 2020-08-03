import requests
import time
import os ,re ,sys
from lxml import etree
import pyodbc
from langconv import *
import datetime
import threading
from queue import Queue
from urllib.request import quote,unquote
from urllib.parse import urlencode
import random

# 捕获异常装饰器
def robust(actual_do):
    def add_robust(*args, **keyargs):
        try:
            return actual_do(*args, **keyargs)
        except Exception as e:
            # print('Error execute: %s' % actual_do.__name__)
            # print('Error execute: %s' % e)
            with open('error.log' ,'a+' ,encoding='utf-8') as f:
                f.write('%sError execute: %s' % (time.strftime('%Y-%m-%d %H:%M:%S'),actual_do.__name__) + 'Error execute: %s' % e + '\n')
            # traceback.print_exc()
    return add_robust

class XingDao:
    @robust
    def __init__(self):
        self.list_mail = []
        self.lock = threading.Lock()
        self.today_time = time.strftime('%Y-%m-%d', time.localtime())
        self.config = self.get_config()
        self.S = requests.Session()
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
            'referer':'https://hd.stheadline.com/news/realtime/%E5%8D%B3%E6%99%82/'
        }
        self.proxies = {
            'http': self.config['proxies']
        }
        self.download_path = self.config['download_path']
        self.conn = pyodbc.connect(r'DRIVER={SQL Server Native Client 11.0};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s' % (
            self.config['host'], self.config['database'], self.config['user'], self.config['password']))
        self.cursor = self.conn.cursor()

        self.set_detail = set()
        self.search_result = self.search_server()

    # 获取配置文件信息
    @robust
    def get_config(self):
        with open('config.txt' ,'r' ,encoding='utf-8') as f:
            data = f.read()
        return eval(data)

    # 繁体转简体
    @robust
    def j(self, line):
        line = Converter("zh-hans").convert(line)
        return line

    # 获取到列表页的url
    @robust
    def main(self ,url):
        response = requests.get(url=url,headers=self.headers ,proxies=self.proxies)
        result = etree.HTML(response.text)
        div_lists = result.xpath('//div[@class="sections"]/div')
        for div_list in div_lists:
            lists_url = div_list.xpath('./div[@class="heading"]/h3/a/@href')[0]
            list_url = 'https://hd.stheadline.com' + lists_url
            if '娛樂' in list_url:
                print('娱乐特殊')
                # self.get_list_yule(list_url)
                for i in range(1,11):
                    list_url_d = list_url + '?p=%s'%i
                    res = self.get_list_yule(list_url_d)
                    if res == 'false':
                        break
                continue
            self.get_list(list_url)
            data = self.get_data(list_url)
            list_url_d = list_url.replace(list_url.split('/')[-2] + '/', '')
            list_url = list_url_d + quote(list_url.split('/')[-2] + '/')
            for i in range(15):
                self.headers['referer'] = list_url
                self.headers['user-agent'] = self.getheaders()
                data['page'] = str(i)
                # print(data)
                list_url_ajax = 'https://hd.stheadline.com/ajax/getMoreInstantNewsOnList.php?' + urlencode(data)
                res = self.get_list(list_url_ajax,i+1)
                if res == 'false':
                    break

    # 获取请求参数cid为栏目类别page为翻页序号，0为第一页1为第二页
    @robust
    def get_data(self,list_url):
        data = {
            'cid': '',
            'page': ''
        }
        if '港聞' in list_url:
            data = {
                'cid': 'a',
                'page': '0'
            }
        # elif '娛樂' in list_url:
        #     data = {
        #         'cid': 'a',
        #         'page': '2'
        #     }
        elif '中國' in list_url:
            data = {
                'cid': 'e',
                'page': '0'
            }
        elif '國際' in list_url:
            data = {
                'cid': 'b',
                'page': '0'
            }
        elif '地產' in list_url:
            data = {
                'cid': 'h',
                'page': '0'
            }
        elif '財經' in list_url:
            data = {
                'cid': 'd',
                'page': '0'
            }
        elif '體育' in list_url:
            data = {
                'cid': 'c',
                'page': '0'
            }

        return data

    # 获取到详情页的url
    @robust
    def get_list(self, list_url, i=1):
        print(list_url)
        is_break = False
        detail_url_list = []
        response = requests.get(url=list_url, headers=self.headers, proxies=self.proxies)
        result = etree.HTML(response.text)
        detail_urls = result.xpath('//div[@class="col-xs-12 instantnews-list-%s"]' % i)
        for detail_uri in detail_urls:
            detail_url = 'https://hd.stheadline.com' + detail_uri.xpath('./div[@class="topic"]//a/@href')[0]
            publishtime = detail_uri.xpath('.//span[@class="time"]/text()')[0].strip()
            if publishtime:
                publishtime = publishtime.split(' ')[0]
                # print(publishtime)
            old_time = publishtime.split('-')
            if datetime.datetime(int(old_time[0]), int(old_time[1]),
                                 int(old_time[2])).date() > datetime.datetime.now().date() - datetime.timedelta(days=1):
                # self.get_detail(detail_url,publishtime)
                # detail_url_d = detail_url.replace(detail_url.split('/')[-1], '')
                # detail_url = detail_url_d + quote(detail_url.split('/')[-1])
                if detail_url in self.search_result:
                    print('数据已入库')
                    continue
                else:
                    detail_url_list.append((detail_url, publishtime))
            else:
                is_break = True
                continue

        urlQueue = Queue()
        for ur in detail_url_list:
            urlQueue.put(ur)
        threads = []
        threadNum = 4
        for i in range(0, threadNum):
            t = threading.Thread(target=self.get_detail, args=(urlQueue,))
            threads.append(t)
        for t in threads:
            t.start()
        for t in threads:
            # 多线程多join的情况下，依次执行各线程的join方法, 这样可以确保主线程最后退出， 且各个线程间没有阻塞
            t.join()
        if is_break:
            return 'false'

    # 获取娱乐详情页url
    @robust
    def get_list_yule(self,list_url):
        print(list_url)
        is_break = False
        detail_url_list = []
        response = requests.get(url=list_url, headers=self.headers, proxies=self.proxies)
        result = etree.HTML(response.text)
        detail_urls = result.xpath('//div[@class="module-wrap card d-flex justify-content-between flex-row"]')
        for detail_uri in detail_urls:
            detail_url = 'https://hd.stheadline.com' + detail_uri.xpath('./div[@class="card-body"]/h4/a/@href')[0]
            publishtime = detail_uri.xpath('.//span[@class="date"]/text()')[0].strip()
            if publishtime:
                publishtime = publishtime.split(' ')[0]
            # print(publishtime)
            old_time = publishtime.split('/')
            if datetime.datetime(int(old_time[0]), int(old_time[1]),
                                 int(old_time[2])).date() > datetime.datetime.now().date() - datetime.timedelta(days=1):
                # self.get_detail(detail_url,publishtime)
                # detail_url_d = detail_url.replace(detail_url.split('/')[-1],'')
                # detail_url = detail_url_d + quote(detail_url.split('/')[-1])
                if detail_url in self.search_result:
                    print('数据已入库')
                    continue
                else:
                    detail_url_list.append((detail_url, publishtime))
            else:
                is_break = True
                continue

        urlQueue = Queue()
        for ur in detail_url_list:
            urlQueue.put(ur)
        threads = []
        threadNum = 4
        for i in range(0, threadNum):
            t = threading.Thread(target=self.get_detail_yule, args=(urlQueue,))
            threads.append(t)
        for t in threads:
            t.start()
        for t in threads:
            # 多线程多join的情况下，依次执行各线程的join方法, 这样可以确保主线程最后退出， 且各个线程间没有阻塞
            t.join()
        if is_break:
            return 'false'

    # 获取娱乐文章详情
    @robust
    def get_detail_yule(self, urlQueue):
        while True:
            try:
                # 不阻塞的读取队列数据
                url = urlQueue.get_nowait()
                # i = urlQueue.qsize()
            except Exception as e:
                break
            try:
                # print(url)
                self.headers['user-agent'] = self.getheaders()
                response = requests.get(url=url[0], headers=self.headers, proxies=self.proxies)
                result = etree.HTML(response.text)
                PAGETITLES = result.xpath('//title/text()')
                title = PAGETITLES[0].split('|')[0].strip().replace('「', '“').replace('」', '”')
                # title = result.xpath('//span[@class="html-tag"]/text()')
                # if title:
                #     title = title[0].replace('「', '“').replace('」', '”')
                print('正在入库：', title,url[1])
                publishtime = url[1]
                ID = 1
                URL = url[0]
                URLFORPUBLISH = ''
                UniqURL = url[0]
                LASTUPDATE = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                ENCODING = 'big5-hkscs'
                SITE = 5
                CATEGORYCODE = '0'
                PARENTID = -1

                PAGETITLE = ''
                if PAGETITLES:
                    PAGETITLE = PAGETITLES[0]
                CANBEPUBLISHED = 1
                NETRESOURCETYPE = 256
                # HTMLCONTENT = response.content.decode("utf-8")
                HTMLCONTENT = ''
                STREAMCONTENT = ''
                authorID = ''

                # publishtime = time.strftime('%Y-%m-%d', time.localtime())
                sort2_id = result.xpath('//div[@class="heading italic"]/h3/span/a/text()')
                if sort2_id:
                    sort2_ID = '即时' + self.j(sort2_id[0])
                else:
                    sort2_id = result.xpath('//div[@class="entry-crumbs"]/span[2]/text()')
                    sort2_ID = self.j(sort2_id[0])
                source = '头条日报'
                content_lists = result.xpath('//div[@class="content"]//p/text()')
                content = ''
                for content_list in content_lists:
                    # content += '　　' + content_list.xpath('string(.)').replace('「', '“').replace('」','”').strip() + '\n\n'
                    content += '　　' + content_list.replace('「', '“').replace('」', '”').strip() + '\n\n'

                lang = 'TC'

                sortID = ''
                layoutID = ''
                standbyID = ''

                standbyIDS = result.xpath('//a[@data-fancybox="gallery"]')
                for standbyID_1 in standbyIDS:
                    standbyID_2 = standbyID_1.xpath('./@href | ./@data-caption')
                    if standbyID_2:
                        standbyID += '〈br〉　　〈img src="http://picture.chinesedata.org/PIC_ZX/hkheadline/%s" border=0〉〈br〉AABIBCC %s CCBIBAA〈/br〉' % (
                            standbyID_2[0].split('//')[-1].replace('static.stheadline.com',
                                                                   'static_stheadline_com'), standbyID_2[1]) + '\n'
                        self.download_image(standbyID_2[0])
                zoneID = '香港>'
                columnID = '报纸>综合'
                standby2_ID = ''
                standby3_ID = ''
                UNIQUEID = ''
                AUTOADDCLMN = 1

                self.list_mail.append(title)
                data_result = [(
                    URL, self.j(title), self.j(sort2_ID),
                    self.j(standbyID),
                    self.j(content), publishtime, LASTUPDATE,
                    HTMLCONTENT, self.j(authorID), UniqURL, ENCODING, SITE,
                    CATEGORYCODE,
                    PARENTID,
                    self.j(PAGETITLE), CANBEPUBLISHED, NETRESOURCETYPE, source, lang, zoneID,
                    columnID)]

                self.insert_server(data_result)
            except Exception as e:
                # print(e)
                with open('yule.txt', 'a+', encoding='utf-8') as f:
                    f.write(str(url[0]) + '\n')

    # 获取文章详情
    @robust
    def get_detail(self, urlQueue):
        while True:
            try:
                # 不阻塞的读取队列数据
                url = urlQueue.get_nowait()
                # i = urlQueue.qsize()
            except Exception as e:
                break
            try:
                # print(url)
                self.headers['user-agent'] = self.getheaders()
                response = requests.get(url=url[0], headers=self.headers, proxies=self.proxies)
                result = etree.HTML(response.text)

                title = result.xpath('//div[@class="topic"]/h1/text()')
                if title:
                    title = title[0].replace('「', '“').replace('」', '”')
                print('正在入库：', title,url[1])
                publishtime = url[1]
                ID = 1
                URL = url[0]
                URLFORPUBLISH = ''
                UniqURL = url[0]
                LASTUPDATE = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                ENCODING = 'big5-hkscs'
                SITE = 5
                CATEGORYCODE = '0'
                PARENTID = -1
                PAGETITLES = result.xpath('//title/text()')
                PAGETITLE = ''
                if PAGETITLES:
                    PAGETITLE = PAGETITLES[0]
                CANBEPUBLISHED = 1
                NETRESOURCETYPE = 256
                # HTMLCONTENT = response.content.decode("utf-8")
                HTMLCONTENT = ''
                STREAMCONTENT = ''
                authorID = ''

                # publishtime = time.strftime('%Y-%m-%d', time.localtime())
                sort2_id = result.xpath('//div[@class="heading italic"]/h3/span/a/text()')
                if sort2_id:
                    sort2_ID = '即时' + self.j(sort2_id[0])
                else:
                    sort2_id = result.xpath('//div[@class="entry-crumbs"]/span[2]/text()')
                    sort2_ID = self.j(sort2_id[0])
                source = '头条日报'
                content_lists = result.xpath('//div[@id="news-content"]//p/text()|//div[@class="content"]//p/text()')
                content = ''
                for content_list in content_lists:
                    # content += '　　' + content_list.xpath('string(.)').replace('「', '“').replace('」','”').strip() + '\n\n'
                    content += '　　' + content_list.replace('「', '“').replace('」','”').strip() + '\n\n'

                lang = 'TC'

                sortID = ''
                layoutID = ''
                standbyIDS = result.xpath('//a[@class="fancybox image"]')
                standbyID = ''
                for standbyID_1 in standbyIDS:
                    standbyID_2 = standbyID_1.xpath('./@href | ./@title')
                    if standbyID_2:
                        standbyID += '〈br〉　　〈img src="http://picture.chinesedata.org/PIC_ZX/hkheadline/%s" border=0〉〈br〉AABIBCC %s CCBIBAA〈/br〉' % (
                            standbyID_2[0].split('//')[-1].replace('static.stheadline.com', 'static_stheadline_com'),standbyID_2[1]) + '\n'
                        self.download_image(standbyID_2[0])
                if not standbyIDS:
                    standbyIDS = result.xpath('//a[@data-fancybox="gallery"]')
                    for standbyID_1 in standbyIDS:
                        standbyID_2 = standbyID_1.xpath('./@href | ./@data-caption')
                        if standbyID_2:
                            standbyID += '〈br〉　　〈img src="http://picture.chinesedata.org/PIC_ZX/hkheadline/%s" border=0〉〈br〉AABIBCC %s CCBIBAA〈/br〉' % (
                                standbyID_2[0].split('//')[-1].replace('static.stheadline.com',
                                                                       'static_stheadline_com'), standbyID_2[1]) + '\n'
                            self.download_image(standbyID_2[0])
                zoneID = '香港>'
                columnID = '报纸>综合'
                standby2_ID = ''
                standby3_ID = ''
                UNIQUEID = ''
                AUTOADDCLMN = 1

                self.list_mail.append(title)
                data_result = [(
                    URL, self.j(title), self.j(sort2_ID),
                    self.j(standbyID),
                    self.j(content), publishtime, LASTUPDATE,
                    HTMLCONTENT, self.j(authorID), UniqURL, ENCODING, SITE,
                    CATEGORYCODE,
                    PARENTID,
                    self.j(PAGETITLE), CANBEPUBLISHED, NETRESOURCETYPE, source, lang, zoneID,
                    columnID)]

                self.insert_server(data_result)
            except Exception as e:
                # print(e)
                with open('detail.txt', 'a+', encoding='utf-8') as f:
                    f.write(str(url[0]) + '\n')

    # 图片下载
    @robust
    def download_image(self, image_url):

        image_path = self.download_path + '\\PIC_ZX\\hkheadline\\' + image_url.split('//')[-1].replace(
            'static.stheadline.com', 'static_stheadline_com').replace(
            image_url.split('/')[-1], '')
        if not os.path.exists(image_path):
            os.makedirs(image_path)
        response = self.S.get(image_url, headers=self.headers, proxies=self.proxies)
        image_path = self.download_path + '\\PIC_ZX\\hkheadline\\' + image_url.split('//')[-1].replace(
            'static.stheadline.com', 'static_stheadline_com')
        with open(image_path, 'wb') as f:
            f.write(response.content)

    # 数据写入数据库
    @robust
    def insert_server(self, data):
        try:
            self.lock.acquire()
            insert_sql = "INSERT INTO {}(URL,title,sort2_ID,standbyID,content,publishtime,LASTUPDATE,HTMLCONTENT,authorID,UniqURL,ENCODING,SITE,CATEGORYCODE,PARENTID,PAGETITLE,CANBEPUBLISHED,NETRESOURCETYPE,source,lang,zoneID,columnID) VALUES (?, ?, ?, ?, ?, ?, ?, ?,?,?,?,?,?,?,?,?,?,?,?,?,?)".format(
                self.config['table'])
            self.cursor.executemany(insert_sql, data)
            self.conn.commit()
        finally:
            self.lock.release()

    # url查询去重
    @robust
    def search_server(self):
        search_sql = "select URL from %s" % (self.config['table'])
        self.cursor.execute(search_sql)
        old_url = []
        for i in self.cursor.fetchall():
            old_url.append(i[0])
        # print(old_url)
        return old_url


    @robust
    def run(self):
        start_time = time.time()
        url = 'https://hd.stheadline.com/news/realtime/%E5%8D%B3%E6%99%82/'
        self.main(url)
        self.write_log(start_time)

    @robust
    def __del__(self):
        self.cursor.close()
        self.conn.close()

    # 写入日志
    @robust
    def write_log(self,start_time):
        cha = time.time() - start_time
        content = '头条日报-即时 %s 下载数量：%s 用时：%s\n'%(time.strftime('%Y-%m-%d %H:%M:%S'),str(len(self.list_mail)),cha)
        with open('头条日报-即时.txt', 'a+', encoding='utf-8') as f:
            f.write(content)

    # 获取随机请求头
    @robust
    def getheaders(self):
        # 各种PC端
        user_agent_list_2 = [
            # Opera
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60",
            "Opera/8.0 (Windows NT 5.1; U; en)",
            "Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.50",
            "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; en) Opera 9.50",
            # Firefox
            "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0",
            "Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10",
            # Safari
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.57.2 (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2",
            # chrome
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
            "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16",
            # 360
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36",
            "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
            # 淘宝浏览器
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11",
            # 猎豹浏览器
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER",
            "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; LBBROWSER)",
            "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E; LBBROWSER)",
            # QQ浏览器
            "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; QQBrowser/7.0.3698.400)",
            "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
            # sogou浏览器
            "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 SE 2.X MetaSr 1.0",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; SE 2.X MetaSr 1.0)",
            # maxthon浏览器
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Maxthon/4.4.3.4000 Chrome/30.0.1599.101 Safari/537.36",
            # UC浏览器
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 UBrowser/4.0.3214.0 Safari/537.36",
        ]
        # 各种移动端
        user_agent_list_3 = [
            # IPhone
            "Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
            # IPod
            "Mozilla/5.0 (iPod; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
            # IPAD
            "Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; zh-cn) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5",
            "Mozilla/5.0 (iPad; U; CPU OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
            # Android
            "Mozilla/5.0 (Linux; U; Android 2.2.1; zh-cn; HTC_Wildfire_A3333 Build/FRG83D) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
            "Mozilla/5.0 (Linux; U; Android 2.3.7; en-us; Nexus One Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
            # QQ浏览器 Android版本
            "MQQBrowser/26 Mozilla/5.0 (Linux; U; Android 2.3.7; zh-cn; MB200 Build/GRJ22; CyanogenMod-7) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
            # Android Opera Mobile
            "Opera/9.80 (Android 2.3.4; Linux; Opera Mobi/build-1107180945; U; en-GB) Presto/2.8.149 Version/11.10",
            # Android Pad Moto Xoom
            "Mozilla/5.0 (Linux; U; Android 3.0; en-us; Xoom Build/HRI39) AppleWebKit/534.13 (KHTML, like Gecko) Version/4.0 Safari/534.13",
            # BlackBerry
            "Mozilla/5.0 (BlackBerry; U; BlackBerry 9800; en) AppleWebKit/534.1+ (KHTML, like Gecko) Version/6.0.0.337 Mobile Safari/534.1+",
            # WebOS HP Touchpad
            "Mozilla/5.0 (hp-tablet; Linux; hpwOS/3.0.0; U; en-US) AppleWebKit/534.6 (KHTML, like Gecko) wOSBrowser/233.70 Safari/534.6 TouchPad/1.0",
            # Nokia N97
            "Mozilla/5.0 (SymbianOS/9.4; Series60/5.0 NokiaN97-1/20.0.019; Profile/MIDP-2.1 Configuration/CLDC-1.1) AppleWebKit/525 (KHTML, like Gecko) BrowserNG/7.1.18124",
            # Windows Phone Mango
            "Mozilla/5.0 (compatible; MSIE 9.0; Windows Phone OS 7.5; Trident/5.0; IEMobile/9.0; HTC; Titan)",
            # UC浏览器
            "UCWEB7.0.2.37/28/999",
            "NOKIA5700/ UCWEB7.0.2.37/28/999",
            # UCOpenwave
            "Openwave/ UCWEB7.0.2.37/28/999",
            # UC Opera
            "Mozilla/4.0 (compatible; MSIE 6.0; ) Opera/UCWEB7.0.2.37/28/999"
        ]
        # 一部分 PC端的
        user_agent_list_1 = [
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
            "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
            "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
            "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
            "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
        ]
        user_agent_list = user_agent_list_1 + user_agent_list_2 + user_agent_list_3;
        UserAgent = random.choice(user_agent_list)
        headers = {'User-Agent': UserAgent}
        return UserAgent
if __name__ == '__main__':
    X = XingDao()
    X.run()


import requests
import cfscrape
import time
import os
from lxml import etree
import pyodbc
from langconv import *
import threading
from queue import Queue
from datetime import datetime
import logging
from selenium import webdriver

# 声明一个logger对象
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
handler = logging.FileHandler('error.log',encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(lineno)d - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
requests.packages.urllib3.disable_warnings()
# 捕获异常装饰器
def robust(actual_do):
    def add_robust(*args, **keyargs):
        try:
            return actual_do(*args, **keyargs)
        except Exception as e:
            logger.error(actual_do.__name__ + ':' + str(e), exc_info=True)
    return add_robust

class Factwire:
    @robust
    def __init__(self):
        self.start_time = time.time()
        self.list_mail = []
        self.old_url_list = []
        self.lock = threading.Lock()
        # self.today_time = time.strftime('%Y-%m-%d', time.localtime())
        self.today_time = datetime.now().date()
        # self.today_time = datetime(year=2020,month=4,day=16).date()

        self.config = self.get_config()
        self.S = requests.Session()
        # self.headers = {
        #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3853.0 Safari/537.36',
        # }
        self.headers = {

        }
        self.proxies = {
            'http': self.config['proxies']
        }
        self.download_path = self.config['download_path']
        self.conn = pyodbc.connect(r'DRIVER={SQL Server};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s' % (
            self.config['host'], self.config['database'], self.config['user'], self.config['password']))
        self.cursor = self.conn.cursor()

        self.set_detail = set()
        self.search_result = self.search_server()

    # 获取cookie
    def login(self):
        try:
            # 使用cfscrape第三方库获取cookies
            scraper = cfscrape.create_scraper(delay=10)
            response = scraper.get_tokens('http://www.factwire.org/', proxies=self.proxies, verify=False)
            self.headers['User-Agent'] = response[1]
            for i, j in response[0].items():
                self.S.cookies.set(i, j)
        except Exception as e:
            logger.error(e)
            # 使用浏览器获取cookies
            self.headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3853.0 Safari/537.36'
            }
            options = webdriver.ChromeOptions()
            options.add_argument('--disable-gpu')
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_argument("--proxy-server=http://192.168.0.70:80")
            executable_path = self.config['executable_path']
            options.binary_location = self.config['binary_location']
            driver = webdriver.Chrome(executable_path=executable_path,options=options)
            driver.get('https://www.factwire.org/')
            time.sleep(10)
            selenium_cookies = driver.get_cookies()
            for item in selenium_cookies:
                self.S.cookies.set(item["name"], item["value"])
            driver.quit()
        print('获取cookies值')

    # 获取配置文件信息
    @robust
    def get_config(self):
        with open('config.txt', 'r', encoding='utf-8') as f:
            data = f.read()
        return eval(data)


    # 繁体转简体
    @robust
    def j(self, line):
        line = Converter("zh-hans").convert(line)
        return line


    # 获取到列表页的url
    @robust
    def get_index(self):
        # 获取网页源代码
        response = self.S.get(url='https://www.factwire.org/',headers=self.headers,proxies=self.proxies, verify=False)
        if response.status_code != 200:
            logger.error('获取cookie失败')
        result = etree.HTML(response.text)
        ul_lists = result.xpath('//nav[@class="article__nav"]/ul/li')
        for ul_list in ul_lists:
            list_urls = ul_list.xpath('./a/@href')[0]
            sort = ul_list.xpath('./a/text()')[0].strip()
            if sort == '全部':
                continue
            print(list_urls,sort)
            self.get_list(list_urls)

    # 获取到详情页的url
    @robust
    def get_list(self,url):
        details_list = set()
        response = self.S.get(url=url, headers=self.headers, proxies=self.proxies, verify=False)
        result = etree.HTML(response.text)
        # 首个文章
        first_urls = result.xpath('//div[@class="entry article__height"]/h4/a/@href')
        if first_urls:

            if first_urls[0] not in self.search_result and first_urls[0] not in self.old_url_list:
                details_list.add(first_urls[0])
                # self.get_detail(first_urls[0])
                self.old_url_list.append(first_urls[0])
            else:
                print('数据已入库：',first_urls[0])

        # 系列报道
        series_lists = result.xpath('//section[@class="section section--series section--series-loop section-to-load"]//div[@class="series__wrap"]')
        if series_lists:
            for series_list in series_lists:
                series_urls = series_list.xpath('./div/a/@href')
                if series_urls:
                    series = self.get_series(series_urls[0])
                    for s in series:
                        if s not in self.search_result and s not in self.old_url_list:
                            details_list.add(s)
                            # res = self.get_detail(s)
                            # if res:
                            #     break
                            self.old_url_list.append(s)
                        else:
                            print('数据已入库：',s)

        # 最新文章
        div_lists = result.xpath('//section[@class="section section--series section--stories-loop section--grey section-to-load"]//div[@class="series__wrap"]')
        for div_list in div_lists:
            detail_urls = div_list.xpath('./div/a/@href')[0]
            if detail_urls not in self.old_url_list and detail_urls not in self.search_result:
                details_list.add(detail_urls)
                # res = self.get_detail(detail_urls)
                # if res:
                #     break
                self.old_url_list.append(detail_urls)
            else:
                print('数据已入库：',detail_urls)

        # self.get_ajax_list(url)

        ajax_list = self.get_ajax_list(url)
        for ajax_li in ajax_list:
            details_list.add(ajax_li)


        urlQueue = Queue()
        for url in details_list:
            urlQueue.put(url)
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

    # 获取异步加载到详情页的url
    @robust
    def get_ajax_list(self,list_url):
        ajax_list = set()
        data = {
            'action': 'crb_get_next_posts_home',
            'offset': '5',
            'term': '62',
            'type': 'child-stories',
        }
        ajax_url = 'https://www.factwire.org/wp-admin/admin-ajax.php'
        # 社会栏目
        if list_url == 'https://www.factwire.org/crb-category/%e7%a4%be%e6%9c%83/':
            for i in range(5,10,4):
                data['term'] = '62'
                data['offset'] = i
                response = self.S.post(url=ajax_url, headers=self.headers,proxies=self.proxies, data=data, verify=False)
                result = etree.HTML(response.json())
                div_lists = result.xpath(
                    '//section[@class="section section--series section--stories-loop section--grey section-to-load"]//div[@class="series__wrap"]')
                for div_list in div_lists:
                    detail_urls = div_list.xpath('./div/a/@href')[0]
                    if detail_urls not in self.old_url_list and detail_urls not in self.search_result:
                        ajax_list.add(detail_urls)
                        # res = self.get_detail(detail_urls)
                        # if res:
                        #     break
                        self.old_url_list.append(detail_urls)

        # 政府栏目
        elif list_url == 'https://www.factwire.org/crb-category/%e6%94%bf%e5%ba%9c/':
            for i in range(5,10,4):
                data['term'] = '63'
                data['offset'] = i
                response = self.S.post(url=ajax_url, headers=self.headers,proxies=self.proxies, data=data, verify=False)
                result = etree.HTML(response.json())
                div_lists = result.xpath(
                    '//section[@class="section section--series section--stories-loop section--grey section-to-load"]//div[@class="series__wrap"]')
                for div_list in div_lists:
                    detail_urls = div_list.xpath('./div/a/@href')[0]
                    if detail_urls not in self.old_url_list and detail_urls not in self.search_result:
                        ajax_list.add(detail_urls)
                        # res = self.get_detail(detail_urls)
                        # if res:
                        #     break
                        self.old_url_list.append(detail_urls)

        # 企业栏目
        elif list_url == 'https://www.factwire.org/crb-category/%e4%bc%81%e6%a5%ad/':
            for i in range(5, 10, 4):
                data['term'] = '67'
                data['offset'] = i
                response = self.S.post(url=ajax_url, headers=self.headers, proxies=self.proxies, data=data, verify=False)
                result = etree.HTML(response.json())
                div_lists = result.xpath(
                    '//section[@class="section section--series section--stories-loop section--grey section-to-load"]//div[@class="series__wrap"]')
                for div_list in div_lists:
                    detail_urls = div_list.xpath('./div/a/@href')[0]
                    if detail_urls not in self.old_url_list and detail_urls not in self.search_result:
                        ajax_list.add(detail_urls)
                        # res = self.get_detail(detail_urls)
                        # if res:
                        #     break
                        self.old_url_list.append(detail_urls)

        # 环境栏目
        elif list_url == 'https://www.factwire.org/crb-category/%e7%92%b0%e5%a2%83/':
            for i in range(5, 10, 4):
                data['term'] = '68'
                data['offset'] = i
                response = self.S.post(url=ajax_url, headers=self.headers, proxies=self.proxies, data=data, verify=False)
                result = etree.HTML(response.json())
                div_lists = result.xpath(
                    '//section[@class="section section--series section--stories-loop section--grey section-to-load"]//div[@class="series__wrap"]')
                for div_list in div_lists:
                    detail_urls = div_list.xpath('./div/a/@href')[0]
                    if detail_urls not in self.old_url_list and detail_urls not in self.search_result:
                        ajax_list.add(detail_urls)
                        # res = self.get_detail(detail_urls)
                        # if res:
                        #     break
                        self.old_url_list.append(detail_urls)

        # 采访手记栏目
        elif list_url == 'https://www.factwire.org/crb-category/%e6%8e%a1%e8%a8%aa%e6%89%8b%e8%a8%98/':
            for i in range(5, 10, 4):
                data['term'] = '113'
                data['offset'] = i
                response = self.S.post(url=ajax_url, headers=self.headers, proxies=self.proxies, data=data, verify=False)
                result = etree.HTML(response.json())
                div_lists = result.xpath(
                    '//section[@class="section section--series section--stories-loop section--grey section-to-load"]//div[@class="series__wrap"]')
                for div_list in div_lists:
                    detail_urls = div_list.xpath('./div/a/@href')[0]
                    if detail_urls not in self.old_url_list and detail_urls not in self.search_result:
                        ajax_list.add(detail_urls)
                        # res = self.get_detail(detail_urls)
                        # if res:
                        #     break
                        self.old_url_list.append(detail_urls)
        else:
            pass

        return ajax_list


    # 获取到系列文章详情的url
    def get_series(self,url):
        series_url = []
        response = self.S.get(url=url, headers=self.headers, proxies=self.proxies, verify=False)
        result = etree.HTML(response.text)
        # 置顶文章
        first_urls = result.xpath('//div[@class="entry article__height"]/h4/a/@href')
        if first_urls:
            series_url.append(first_urls[0])

        # 列表文章
        series_lists = result.xpath('//section[@class="section section--series section--stories-loop section--grey no-padding section-to-load"]//div[@class="series__wrap"]')
        for series_list in series_lists:
            series_urls = series_list.xpath('./div/a/@href')
            if series_urls:
                series_url.append(series_urls[0])

        return series_url


    # 获取文章详情
    @robust
    def get_detail(self, urlQueue):
        while True:
            try:
                # 不阻塞的读取队列数据
                detail_url = urlQueue.get_nowait()
                # i = urlQueue.qsize()
            except Exception as e:
                break
            try:
                response = self.S.get(url=detail_url, headers=self.headers, proxies=self.proxies, verify=False)
                result = etree.HTML(response.text)
                publishtime = ''
                publishtimes = result.xpath('//div[@class="article__meta"]/p[1]/text()')
                if publishtimes:
                    dtime = publishtimes[0].split(' ')
                    publishtime = self.get_time(dtime[2],dtime[1],dtime[0])
                # print(publishtime,self.today_time)
                if publishtime < self.today_time:
                    print('超出今日',publishtime)
                    return True
                title = result.xpath('//div[@class="article__title"]/h2/text()')
                if title:
                    title = title[0].replace('「', '“').replace('」', '”')
                self.set_detail.add(title)
                ID = 1
                URL = detail_url
                URLFORPUBLISH = ''
                UniqURL = detail_url
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
                sort2_ID = result.xpath('//section[@class="section section--breadcrumbs"]//div[@class="shell"]/p/a/text()')
                if sort2_ID:
                    sort2_ID = sort2_ID[0]
                source = '传真社'
                content_lists = result.xpath('//div[@class="article__title"]/p|//div[@class="article__body"]/div[@class="entry"]//p')
                content = ''
                for content_list in content_lists:
                    content += '　　' + content_list.xpath('string(.)').replace('「', '“').replace('」','”').strip() + '\n\n'
                    # content += '　　' + content_list.replace('「', '“').replace('」','”').strip() + '\n\n'

                lang = 'TC'

                sortID = ''
                layoutID = ''
                standbyID = ''
                # 图片
                standbyIDS = result.xpath('//article//img')
                if standbyIDS:
                    for standbyID_1 in standbyIDS:
                        standbyID_2 = standbyID_1.xpath('./@src')
                        if standbyID_2:
                            if 'factwire.clinksoft.net' in standbyID_2[0]:
                                continue
                            standbyID += '〈br〉　　〈img src="http://picture.chinesedata.org/PIC_ZX/Factwire/%s" border=0〉〈br〉AABIBCC  CCBIBAA〈/br〉'%standbyID_2[0].split('//')[-1] + '\n'
                            self.download_image(standbyID_2[0])

                zoneID = '香港>'
                columnID = '报纸>综合'
                standby2_ID = ''
                standby3_ID = ''
                UNIQUEID = ''
                AUTOADDCLMN = 1


                data_result = [(
                    URL, self.j(title), self.j(sort2_ID),
                    self.j(standbyID.replace('www.factwire.org', 'www_factwire_org')),
                    self.j(content), str(publishtime), LASTUPDATE,
                    HTMLCONTENT, self.j(authorID), UniqURL, ENCODING, SITE,
                    CATEGORYCODE,
                    PARENTID,
                    self.j(PAGETITLE), CANBEPUBLISHED, NETRESOURCETYPE, source, lang, zoneID,
                    columnID)]
                # print(data_result)
                self.insert_server(data_result)
                return data_result
            except Exception as e:
                print(e)

    # 时间格式转换
    @robust
    def get_time(self,y, m, d):
        if m == '一月':
            m = '01'
        elif m == '二月':
            m = '02'
        elif m == '三月':
            m = '03'
        elif m == '四月':
            m = '04'
        elif m == '五月':
            m = '05'
        elif m == '六月':
            m = '06'
        elif m == '七月':
            m = '07'
        elif m == '八月':
            m = '08'
        elif m == '九月':
            m = '09'
        elif m == '十月':
            m = '10'
        elif m == '十一月':
            m = '11'
        elif m == '十二月':
            m = '12'
        # if len(d) < 2:
        #     d = '0' + str(d)
        # return '%s-%s-%s' % (y, m, d)
        return datetime(year=int(y),month=int(m),day=int(d)).date()
    # 图片下载
    @robust
    def download_image(self, image_url):

        image_path = self.download_path + '/PIC_ZX/Factwire/' + image_url.split('//')[-1].replace('www.factwire.org', 'www_factwire_org').replace(image_url.split('/')[-1], '')
        if not os.path.exists(image_path):
            os.makedirs(image_path)
        response = self.S.get(image_url, headers=self.headers, proxies=self.proxies, verify=False)
        image_path = self.download_path + '/PIC_ZX/Factwire/' + image_url.split('//')[-1].replace('www.factwire.org', 'www_factwire_org')
        with open(image_path, 'wb') as f:
            f.write(response.content)

    # 数据写入数据库
    @robust
    def insert_server(self, data):
        self.lock.acquire()
        try:
            insert_sql = "INSERT INTO {}(URL,title,sort2_ID,standbyID,content,publishtime,LASTUPDATE,HTMLCONTENT,authorID,UniqURL,ENCODING,SITE,CATEGORYCODE,PARENTID,PAGETITLE,CANBEPUBLISHED,NETRESOURCETYPE,source,lang,zoneID,columnID) VALUES (?, ?, ?, ?, ?, ?, ?, ?,?,?,?,?,?,?,?,?,?,?,?,?,?)".format(
                self.config['table'])
            self.cursor.executemany(insert_sql, data)
            self.conn.commit()
            self.list_mail.append(data[0][1])
            print('正在入库：', data[0][1], data[0][5])
        finally:
            self.lock.release()

    # url查询去重
    @robust
    def search_server(self):
        # search_sql = "select URL from %s where publishtime='%s'" % (
        search_sql = "select URL from %s where source='传真社'" % (self.config['table'])
        self.cursor.execute(search_sql)
        old_url = []
        for i in self.cursor.fetchall():
            old_url.append(i[0])
        # print(old_url)
        return old_url

    @robust
    def run(self):
        self.login()
        self.get_index()
        self.write_log(self.start_time)


    @robust
    def __del__(self):
        self.cursor.close()
        self.conn.close()

    # 写入日志
    @robust
    def write_log(self,start_time):
        cha = time.time() - start_time
        content = 'factwire %s 下载数量：%s 用时：%s\n'%(time.strftime('%Y-%m-%d %H:%M:%S'),str(len(self.list_mail)),cha)
        with open('factwire.txt', 'a+', encoding='utf-8') as f:
            f.write(content)

if __name__ == '__main__':

    F = Factwire()
    F.run()


# 请求方式post
# netsystem123
# 社会
"""
第一次加载
https://www.factwire.org/wp-admin/admin-ajax.php
action: crb_get_next_posts_home
offset: 5
term: 62
type: child-stories
lang: 
第二次加载
action: crb_get_next_posts_home
offset: 9
term: 62
type: child-stories
lang:
第三次加载
action: crb_get_next_posts_home
offset: 13
term: 62
type: child-stories
lang:
"""
# 政府
"""
第一次加载
https://www.factwire.org/wp-admin/admin-ajax.php
action: crb_get_next_posts_home
offset: 5
type: child-stories
term: 63
lang: 
第二次加载
action: crb_get_next_posts_home
offset: 9
term: 63
type: child-stories
lang: 
第三次加载
action: crb_get_next_posts_home
offset: 13
term: 63
type: child-stories
lang: 
"""
# 企业
"""
action: crb_get_next_posts_home
offset: 5
term: 67
type: child-stories
lang: 

action: crb_get_next_posts_home
offset: 9
term: 67
type: child-stories
lang: 
"""

# 环境
"""
action: crb_get_next_posts_home
offset: 5
term: 68
type: child-stories
lang: 
"""
# 教育-暂无

# 采访手记
"""
action: crb_get_next_posts_home
offset: 5
term: 113
type: child-stories
lang: 
"""

# 视野-暂无


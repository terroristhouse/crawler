import sys, os

if hasattr(sys, 'frozen'):
    os.environ['PATH'] = sys._MEIPASS + ";" + os.environ['PATH']
import pyodbc
import requests
from lxml import etree
import time
import threading
from queue import Queue
import schedule
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, pyqtSignal,QCoreApplication
from langconv import *
from mingbao_ui import Example
import re
import json
requests.packages.urllib3.disable_warnings()

# 装饰器
def robust(actual_do):
    def add_robust(*args, **keyargs):
        try:
            return actual_do(*args, **keyargs)
        except Exception as e:
            with open('error.txt', 'a+') as f:
                f.write('Error execute: %s' % actual_do.__name__ + '\n' + 'Error except: %s' % e + '\n')

    return add_robust


# 爬虫
class EveryDayMingBao(QThread):
    # trigger = pyqtSignal()
    @robust
    def __init__(self, ui, today=None):
        super(EveryDayMingBao, self).__init__()
        self.config = self.get_config()
        self.lock = threading.Lock()
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'
        }
        self.proxies = {
            'http': self.config['proxies']
        }
        self.S = requests.Session()
        self.today = today
        self.today_url = time.strftime('%Y%m%d', time.localtime())
        if self.today:
            self.today_url = self.today
        self.download_path = self.config['download_path']
        self.ui = ui

        self.conn = pyodbc.connect(r'DRIVER={SQL Server};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s' % (
        self.config['host'], self.config['database'], self.config['user'], self.config['password']))
        self.cursor = self.conn.cursor()
        self.login()
        self.search_result = self.search_server()

    # 获取配置参数
    @robust
    def get_config(self):
        with open('config.txt', 'r',encoding='utf-8') as f:
            config = f.read()
        return eval(config)

    # 模拟登录
    @robust
    def login(self):
        login_url = 'https://news.mingpao.com/php/login2.php'
        Form_Data = {
            'UserName': self.config['UserName'],
            'Password': self.config['Password'],
        }
        self.S.post(login_url, data=Form_Data, headers=self.headers, proxies=self.proxies)

    # 获取到详情页url的方法
    @robust
    def index_list(self, urlQueue):
        while True:
            try:
                # 不阻塞的读取队列数据
                link_url = urlQueue.get_nowait()
                # i = urlQueue.qsize()
            except Exception as e:
                break

            # print('栏目的开始', link_url)
            data = []
            response = self.S.get(link_url, headers=self.headers, proxies=self.proxies)
            result = etree.HTML(response.content.decode("utf-8"))

            # 获取社评文章信息
            editorial_detail_url = result.xpath(
                '//div[@id="maincontent"]/div[@class="group"]/div[@class="col span_8_of_12"]/div[starts-with(@class,"headline")]/div[starts-with(@class,"headcontent")]/div[@class="inontent_wrapper"]/div[@class="inontent"]/a/@href')
            if editorial_detail_url:
                editorial_detail_url = 'https://news.mingpao.com' + editorial_detail_url[0].lstrip('..')
                # print(editorial_detail_url)
                if editorial_detail_url not in self.search_result:
                    # self.get_detail(editorial_detail_url)
                    data.append(self.get_detail(editorial_detail_url))

            # 获取首个文章url
            first_detail_url = result.xpath(
                '//div[@id="maincontent"]/div[@class="group"]/div[@class="col span_8_of_12"]/div[starts-with(@class,"headline")]/div[starts-with(@class,"right")]/a/@href')
            if first_detail_url:
                first_detail_url = 'https://news.mingpao.com' + first_detail_url[0].lstrip('..')
                if first_detail_url not in self.search_result:
                    # self.get_detail(first_detail_url)
                    data.append(self.get_detail(first_detail_url))

            # 获取列表中的文章url
            div_lists = result.xpath(
                '//div[@id="maincontent"]/div[@class="group"]/div[@class="col span_8_of_12"]/div[starts-with(@class,"cat")]/div[starts-with(@class,"listing")] | //div[@id="maincontent"]/div[@class="group"]/div[@class="col span_8_of_12"]/div[starts-with(@class,"cat")]/div[starts-with(@class,"listing")]/div | //div[@id="maincontent"]/div[@class="group"]/div[@class="col span_8_of_12"]/div[@class="headline2"]/div[starts-with(@class,"cat")]/div[starts-with(@class,"listing")]')
            # print(div_lists)
            for div_list in div_lists:
                sort2_IDs = div_list.xpath('./h2/text()')
                if sort2_IDs:
                    if sort2_IDs[0] == '港聞二 ' or sort2_IDs[0] == '港聞一 ':
                        sort2_ID = '港聞'
                    else:
                        sort2_ID = sort2_IDs[0]
                else:
                    sort2_ID = ''
                li_lists = div_list.xpath('./ul/li')
                # print(li_lists)
                for li_list in li_lists:
                    detail_url = li_list.xpath('./a/@href')
                    if detail_url:
                        detail_url = 'https://news.mingpao.com' + detail_url[0].lstrip('..')
                        if detail_url not in self.search_result:
                            data.append(self.get_detail(detail_url, sort2_ID))
                            # self.get_detail(detail_url, sort2_ID)
            self.insert_server(data)

    # 获取文章详情的方法
    @robust
    def get_detail(self, detail_url, sort2_ID=None):

        response = self.S.get(detail_url, headers=self.headers, proxies=self.proxies, allow_redirects=False)
        # print(response.encoding)
        result = etree.HTML(response.content.decode("utf-8"))

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
        title = result.xpath('//*[@id="blockcontent"]/hgroup/h1/text()')
        if title:
            title = title[0].replace('「','“').replace('」','”')
        # publishtime = time.strftime('%Y-%m-%d', time.localtime())
        publishtime = self.today_url
        source = '明报'
        # content_lists = result.xpath('//div[@id="upper"]/p/text() | //div[@id="lower"]/div[@class="articlelogin"]//p/text() | //div[@id="lower"]/div[@class="articlelogin"]//h2/text() | //div[@id="lower"]/div[@class="articlelogin"]//a/text()')
        content_lists = result.xpath('//div[@id="upper"]/p | //div[@id="lower"]/div[@class="articlelogin"]//p | //div[@id="lower"]/div[@class="articlelogin"]//h2')


        standbyID_login = ''
        login_result = self.login_detail(detail_url)
        if login_result:
            content_lists.extend(login_result.get('contents', ''))
            standbyID_login = login_result.get('standbyID', '')
        content = ''
        for content_list in content_lists:
            content += '　　' + content_list.xpath('string(.)').replace('\\', '').replace('「','“').replace('」','”') + '\n\n'
        lang = 'TC'
        authorID = ''
        #  / ／
        # # 作家专栏中寻找作者
        if '%E4%BD%9C%E5%AE%B6%E5%B0%88%E6%AC%84'.lower() in detail_url:
            if title:
                if '/' in title:
                    authorID = title.split('/')[-1].strip()# / 谭蕙芸
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
                        title = title.replace(authorID + '：','').strip()

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
            sort2_ID = result.xpath('//*[@id="menusection"]//*[@id="current"]/text()')
            if sort2_ID:
                sort2_ID = sort2_ID[0]

        standbyIDS = result.xpath('//div[@id="zoomedimg"]/div')
        standbyID = ''
        for standbyID_1 in standbyIDS:
            standbyID_2 = standbyID_1.xpath('./a/img/@data-original | ./a/img/@alt')
            if standbyID_2:
                standbyID += '〈br〉　　〈img src="http://picture.chinesedata.org/PIC_ZX/mingpao/%s" border=0〉〈br〉AABIBCC %s CCBIBAA〈/br〉' % (
                    standbyID_2[0].split('//')[-1], standbyID_2[1]) + '\n'
                self.download_image(standbyID_2[0].replace('\\', ''))
        if standbyID_login:
            standbyID = standbyID_login

        zoneID = '香港>'
        columnID = '报纸>综合'
        standby2_ID = ''
        standby3_ID = ''
        UNIQUEID = ''
        AUTOADDCLMN = 1

        # print(detail_url)
        # print(title)
        # print(authorID)
        # print(sort2_ID)
        # print(standbyID)
        # print(content)
        # print(publishtime)
        # print(LASTUPDATE)
        # time.sleep(1)
        # print('文章断点')
        # print(detail_url,title,sort2_ID,standbyID,content,publishtime,LASTUPDATE)
        # exit()
        data_result = (
            URL, self.j(title.replace("'", "’")), self.j(sort2_ID.replace("'", "’")), self.j(standbyID.replace('fs.mingpao.com','fs_mingpao_com')),
            self.j(content.replace("'", "’")), publishtime, LASTUPDATE,
            HTMLCONTENT.replace("'", "’"), self.j(authorID.replace("'", "’")), UniqURL, ENCODING, SITE, CATEGORYCODE,
            PARENTID,
            self.j(PAGETITLE.replace("'", "’")), CANBEPUBLISHED, NETRESOURCETYPE, source, lang, zoneID, columnID)
        # self.insert_server(data_result)
        return data_result

    # 获取异步文章详情
    @robust
    def login_detail(self, detail_url):
        login_detail_url = detail_url.split('/')[-2]
        data = {
            'issue': '%s' % self.today_url,
            'node': '%s' % login_detail_url
        }
        login_url = 'https://news.mingpao.com/php/login3.php'
        response = self.S.post(login_url, data=data, headers=self.headers, proxies=self.proxies, allow_redirects=False)
        dict1 = json.loads(response.content.decode("utf-8"))

        result_dict = {}
        content_result = dict1['TextContent']
        if content_result:
            res = etree.HTML(content_result)
            contents = res.xpath('//p | //h2')
            result_dict['contents'] = contents

        image_result = dict1['LargeMedia']
        standbyID = ''
        if image_result:
            image_res = etree.HTML(image_result)
            image_data = image_res.xpath('//a')
            for image_1 in image_data:
                standbyIDs = image_1.xpath('./img/@data-original | ./img/@alt')
                if standbyIDs:
                    standbyID += '〈br〉　　〈img src="http://picture.chinesedata.org/PIC_ZX/mingpao/%s" border=0〉〈br〉AABIBCC %s CCBIBAA〈/br〉' % (
                        standbyIDs[0].replace('\\', '').split('//')[-1], standbyIDs[1]) + '\n'
                    self.download_image(standbyIDs[0].replace('\\', ''))
        result_dict['standbyID'] = standbyID
        return result_dict

    # 数据写入数据库
    @robust
    def insert_server(self, data):
        self.lock.acquire()
        try:
            insert_sql = "INSERT INTO {}(URL,title,sort2_ID,standbyID,content,publishtime,LASTUPDATE,HTMLCONTENT,authorID,UniqURL,ENCODING,SITE,CATEGORYCODE,PARENTID,PAGETITLE,CANBEPUBLISHED,NETRESOURCETYPE,source,lang,zoneID,columnID) VALUES (?, ?, ?, ?, ?, ?, ?, ?,?,?,?,?,?,?,?,?,?,?,?,?,?)".format(self.config['table'])
            self.cursor.executemany(insert_sql, data)
            self.conn.commit()
        finally:
            self.lock.release()

    # 下载图片方法
    @robust
    def download_image(self, image_url):
        # if not os.path.exists(self.download_path):
        #     os.mkdir(self.download_path)
        # if 'https://fs.mingpao.com' not in image_url:
        #     image_url = 'https://fs.mingpao.com' + image_url
        image_path = self.download_path + '\\PIC_ZX\\mingpao\\' + image_url.split('//')[-1].replace('fs.mingpao.com','fs_mingpao_com').replace(
            image_url.split('/')[-1], '')
        if not os.path.exists(image_path):
            os.makedirs(image_path)
        response = self.S.get(image_url, headers=self.headers, proxies=self.proxies)
        image_path = self.download_path + '\\PIC_ZX\\mingpao\\' + image_url.split('//')[-1].replace('fs.mingpao.com','fs_mingpao_com')
        with open(image_path, 'wb') as f:
            f.write(response.content)

    # 查询去重
    @robust
    def search_server(self):
        search_sql = "select URL from %s where publishtime='%s'" % (self.config['table'],self.today_url)
        self.cursor.execute(search_sql)
        old_url = []
        for i in self.cursor.fetchall():
            old_url.append(i[0])
        return old_url

    # 繁体转简体
    @robust
    def j(self, line):
        line = Converter("zh-hans").convert(line)
        return line

    # main方法
    @robust
    def main(self):
        start_time = time.time()
        self.ui.aoi_lbl2.setText('运行中...')
        QApplication.processEvents()
        urls = [
            # 要闻
            'https://news.mingpao.com/pns/%E8%A6%81%E8%81%9E/section/{}/s00001'.format(self.today_url),
            # 港闻
            'https://news.mingpao.com/pns/%E6%B8%AF%E8%81%9E/section/{}/s00002'.format(self.today_url),
            # 经济
            'https://news.mingpao.com/pns/%E7%B6%93%E6%BF%9F/section/{}/s00004'.format(self.today_url),
            # 娱乐
            'https://news.mingpao.com/pns/%E5%A8%9B%E6%A8%82/section/{}/s00016'.format(self.today_url),
            # 社评
            'https://news.mingpao.com/pns/%E7%A4%BE%E8%A9%95/section/{}/s00003'.format(self.today_url),
            # 观点(部分需登录)(笔阵，闻风笔动)
            'https://news.mingpao.com/pns/%E8%A7%80%E9%BB%9E/section/{}/s00012'.format(self.today_url),
            # 中国
            'https://news.mingpao.com/pns/%E4%B8%AD%E5%9C%8B/section/{}/s00013'.format(self.today_url),
            # 国际
            'https://news.mingpao.com/pns/%E5%9C%8B%E9%9A%9B/section/{}/s00014'.format(self.today_url),
            # 教育(部分需登录)(通通识，常识学堂)
            'https://news.mingpao.com/pns/%E6%95%99%E8%82%B2/section/{}/s00011'.format(self.today_url),
            # 体育
            'https://news.mingpao.com/pns/%E9%AB%94%E8%82%B2/section/{}/s00015'.format(self.today_url),
            # 副刊
            'https://news.mingpao.com/pns/%E5%89%AF%E5%88%8A/section/{}/s00005'.format(self.today_url),
            # 英文
            'https://news.mingpao.com/pns/%E8%8B%B1%E6%96%87/section/{}/s00017'.format(self.today_url),
            # 作家专栏(需要登录)
            'https://news.mingpao.com/pns/%E4%BD%9C%E5%AE%B6%E5%B0%88%E6%AC%84/section/{}/s00018'.format(
                self.today_url),

        ]

        # for url in urls:
        #     self.index_list(url)

        urlQueue = Queue()
        for url in urls:
            urlQueue.put(url)
        threads = []
        threadNum = 2
        for i in range(0, threadNum):
            t = threading.Thread(target=self.index_list, args=(urlQueue,))
            threads.append(t)
        for t in threads:
            t.start()
        for t in threads:
            # 多线程多join的情况下，依次执行各线程的join方法, 这样可以确保主线程最后退出， 且各个线程间没有阻塞
            t.join()
        with open('time.txt','a+') as f:
            f.write(str(time.time()-start_time) + '\n')
        self.ui.aoi_lbl2.setText('运行完毕...')
        QApplication.processEvents()

    # run方法
    @robust
    def run(self):
        self.main()
        self.cursor.close()
        self.conn.close()
        QCoreApplication.quit()
        # schedule.every().day.at(self.config['day_run']).do(self.main)
        # if self.today:
        #     self.main()
        # while True:
        #     schedule.run_pending()
        #     time.sleep(1)

    # def __del__(self):
    #     print('析构方法')
    #     self.cursor.close()
    #     self.conn.close()

# 界面&启动
class Ui_show(Example):
    @robust
    def __init__(self):
        super().__init__()
        self.Work()
        self.hat_btn2.clicked.connect(lambda: self.Work01(self.cal.selectedDate().toString('yyyyMMdd')))

    @robust
    def Work(self):
        self.thread = EveryDayMingBao(self)
        self.thread.start()

    @robust
    def Work01(self, today):
        # print(today)
        self.thread2 = EveryDayMingBao(ui=self, today=today)
        self.thread2.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = Ui_show()
    sys.exit(app.exec_())

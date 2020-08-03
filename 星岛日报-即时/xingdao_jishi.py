
import requests
import time
import os ,re ,sys
from lxml import etree
import pyodbc
from langconv import *
# 邮件发送相关库
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr


# 捕获异常装饰器
def robust(actual_do):
    def add_robust(*args, **keyargs):
        try:
            return actual_do(*args, **keyargs)
        except Exception as e:
            # print('Error execute: %s' % actual_do.__name__)
            # print('Error execute: %s' % e)
            with open('error.log' ,'a+' ,encoding='utf-8') as f:
                f.write('Error execute: %s' % actual_do.__name__ + 'Error execute: %s' % e + '\n')
            # traceback.print_exc()
    return add_robust



class XingDao:
    @robust
    def __init__(self):
        self.list_mail = []
        self.today_time = time.strftime('%Y-%m-%d', time.localtime())
        self.config = self.get_config()
        self.S = requests.Session()
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
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
        self.search_title = self.srarch_title_server()


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


    # 获取到详情页的url
    @robust
    def main(self ,url):
        is_break = False
        for i in range(1,10):
            list_url = url + 'articles/fetchlist/latest/%s/'%i
            print(list_url)
            response = self.S.get(url=list_url,headers=self.headers ,proxies=self.proxies)
            result = etree.HTML(response.text)
            div_lists = result.xpath('//div[@class="module-wrap thumb-pull-right underline"]')
            for i ,li_list in enumerate(div_lists):
                index_url = li_list.xpath('./a/@href')[0]
                publishtime = li_list.xpath('.//div[@class="time"]/text()')[0]
                if self.today_time != publishtime.split(' ')[0]:
                    print('超出今日')
                    is_break = True
                    break
                elif index_url in self.search_result:
                    # print('数据已入库')
                    is_break = True
                    break
                self.get_detail(index_url)
                # self.view_bar(i, len(div_lists) - 1)
            if is_break:
                print('完成')
                break


    # 显示下载进度
    def view_bar(self ,num, total):
        rate = float(num) / float(total)
        rate_num = int(rate * 100)
        r = "\r" +'进度：' + ("=" * (2 * rate_num // 10) + ">") + (" " * (20 - 2 * rate_num // 10)) + '%d%%' % (rate_num,)
        sys.stdout.write(r)
        sys.stdout.flush()  # 刷新缓冲区


    # 获取文章详情
    @robust
    def get_detail(self, detail_url):

        response = self.S.get(url=detail_url, headers=self.headers, proxies=self.proxies)
        result = etree.HTML(response.text)
        # publishtime = ''
        # publishtimes = result.xpath('//div[@class="post-heading supplement-p-h"]/div[@class="date"]/text()')
        # if publishtimes:
        #     publishtime = publishtimes[0].split(' ')[1]
        publishtime = ''
        publishtimes = result.xpath('//div[@class="post-heading supplement-p-h"]/div[@class="date"]/text()')
        for pub in publishtimes:
            publishtime += pub
        publishtime = publishtime.strip().split(' ')[0]

        title = result.xpath('//div[@class="post-heading supplement-p-h"]/h1/text()')
        if title:
            title = title[0].replace('「', '“').replace('」', '”')
        print('正在入库：', title)
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
        sort2_ID = result.xpath('//a[@class="margin-l-r-5"]/text()')
        if sort2_ID:
            sort2_ID = '即时' + sort2_ID[0]
        source = '星岛日报'
        content_lists = result.xpath('//div[@class="paragraph"]//p/text()')
        content = ''
        for content_list in content_lists:
            # content += '　　' + content_list.xpath('string(.)').replace('「', '“').replace('」','”').strip() + '\n\n'
            content += '　　' + content_list.replace('「', '“').replace('」','”').strip() + '\n\n'

        lang = 'TC'

        sortID = ''
        layoutID = ''
        standbyIDS = result.xpath('//a[@class="fancybox-thumb image"]')
        standbyID = ''
        for standbyID_1 in standbyIDS:
            standbyID_2 = standbyID_1.xpath('./@href | ./@title')
            if standbyID_2:
                standbyID += '〈br〉　　〈img src="http://picture.chinesedata.org/PIC_ZX/singtao/%s" border=0〉〈br〉AABIBCC %s CCBIBAA〈/br〉' % (
                    standbyID_2[0].split('//')[-1], standbyID_2[1]) + '\n'
                self.download_image(standbyID_2[0])
        # static.stheadline.com/stheadline/inewsmedia/20200325/_2020032509192690978.jpg
        zoneID = '香港>'
        columnID = '报纸>综合'
        standby2_ID = ''
        standby3_ID = ''
        UNIQUEID = ''
        AUTOADDCLMN = 1

        self.list_mail.append(title)
        data_result = [(
            URL, self.j(title), self.j(sort2_ID),
            self.j(standbyID.replace('static.stheadline.com', 'static_stheadline_com')),
            self.j(content), publishtime, LASTUPDATE,
            HTMLCONTENT, self.j(authorID), UniqURL, ENCODING, SITE,
            CATEGORYCODE,
            PARENTID,
            self.j(PAGETITLE), CANBEPUBLISHED, NETRESOURCETYPE, source, lang, zoneID,
            columnID)]
        # print(data_result)
        self.insert_server(data_result)
        # return data_result

    # 图片下载
    @robust
    def download_image(self, image_url):

        image_path = self.download_path + '\\PIC_ZX\\singtao\\' + image_url.split('//')[-1].replace(
            'static.stheadline.com', 'static_stheadline_com').replace(
            image_url.split('/')[-1], '')
        if not os.path.exists(image_path):
            os.makedirs(image_path)
        response = self.S.get(image_url, headers=self.headers, proxies=self.proxies)
        image_path = self.download_path + '\\PIC_ZX\\singtao\\' + image_url.split('//')[-1].replace(
            'static.stheadline.com', 'static_stheadline_com')
        with open(image_path, 'wb') as f:
            f.write(response.content)

    # 数据写入数据库
    @robust
    def insert_server(self, data):
        insert_sql = "INSERT INTO {}(URL,title,sort2_ID,standbyID,content,publishtime,LASTUPDATE,HTMLCONTENT,authorID,UniqURL,ENCODING,SITE,CATEGORYCODE,PARENTID,PAGETITLE,CANBEPUBLISHED,NETRESOURCETYPE,source,lang,zoneID,columnID) VALUES (?, ?, ?, ?, ?, ?, ?, ?,?,?,?,?,?,?,?,?,?,?,?,?,?)".format(
            self.config['table'])
        self.cursor.executemany(insert_sql, data)
        self.conn.commit()

    # url查询去重
    @robust
    def search_server(self):
        search_sql = "select URL from %s where publishtime='%s'" % (
        self.config['table'], time.strftime('%Y-%m-%d', time.localtime()))
        self.cursor.execute(search_sql)
        old_url = []
        for i in self.cursor.fetchall():
            old_url.append(i[0])
        # print(old_url)
        return old_url

    # 由于文中有大量重复，添加标题去重
    def srarch_title_server(self):
        search_sql = "select title from %s where publishtime='%s'" % (
        self.config['table'], time.strftime('%Y-%m-%d', time.localtime()))
        self.cursor.execute(search_sql)
        old_title = []
        for i in self.cursor.fetchall():
            old_title.append(i[0])
        # print(old_url)
        return old_title

    @robust
    def run(self):
        url = 'https://std.stheadline.com/instant/'
        self.main(url)


    @robust
    def __del__(self):
        self.cursor.close()
        self.conn.close()

    # 写入日志
    @robust
    def write_log(self,start_time):
        cha = time.time() - start_time
        content = '-星岛日报-即时 %s 下载数量：%s 用时：%s\n'%(time.strftime('%Y-%m-%d %H:%M:%S'),str(len(self.list_mail)),cha)
        with open('星岛日报-即时.txt', 'a+', encoding='utf-8') as f:
            f.write(content)

if __name__ == '__main__':
    start_time = time.time()
    X = XingDao()
    X.run()
    X.write_log(start_time)


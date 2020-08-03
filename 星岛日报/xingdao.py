
import requests
import time
import os,re,sys
import json
from queue import Queue
import threading
from lxml import etree
import pyodbc
from langconv import *
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
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
            with open('error.log','a+',encoding='utf-8') as f:
                f.write('Error execute: %s' % actual_do.__name__ + 'Error execute: %s' % e + '\n')
            #traceback.print_exc()
    return add_robust


# 第三方 SMTP 服务
mail_host = "smtp.126.com"  # 设置服务器
mail_user = "q867940410@126.com"  # 用户名
mail_pass = "q867940410"  # 口令

# 发件人
sender = 'q867940410@126.com'
receivers = ['867940410@qq.com']  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱


class XingDao:
    @robust
    def __init__(self):
        self.list_mail = []
        self.config = self.get_config()
        self.S = requests.Session()
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
        }
        self.proxies = {
            'http': self.config['proxies']
        }
        self.download_path = self.config['download_path']
        self.lock = threading.Lock()
        self.conn = pyodbc.connect(r'DRIVER={SQL Server Native Client 11.0};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s' % (
            self.config['host'], self.config['database'], self.config['user'], self.config['password']))
        self.cursor = self.conn.cursor()

        self.set_detail = set()
        self.search_result = self.search_server()
        self.search_title = self.srarch_title_server()
        self.login()

    # 获取配置文件信息
    @robust
    def get_config(self):
        with open('config.txt','r',encoding='utf-8') as f:
            data = f.read()
        return eval(data)


    # 繁体转简体
    @robust
    def j(self, line):
        line = Converter("zh-hans").convert(line)
        return line

    # 发包登录
    def login_post(self):
        pass

    # 模拟登录
    @robust
    def login(self):
        # 初始化浏览器
        chrome_options = Options()
        # 隐藏窗口
        chrome_options.add_argument('--headless')
        # 代理
        chrome_options.add_argument("--proxy-server=http://%s"%self.config['proxies'])
        # 规避bug
        chrome_options.add_argument('--disable-gpu')
        # 设为开发者模式
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        # 禁止打印日志信息
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        # 禁用大量日志信息滚动输出。
        chrome_options.add_argument('log-level=3')
        # chromium
        chrome_options.binary_location = self.config['binary_location']
        # chromedriver
        executable_path = self.config['executable_path']

        driver = webdriver.Chrome(executable_path=executable_path, chrome_options=chrome_options)
        driver.maximize_window()
        login_url = 'http://stepaper.stheadline.com/%E7%99%BB%E5%85%A5'
        driver.get(login_url)
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="username"]').send_keys(self.config['UserName'])
        driver.find_element_by_xpath('//*[@id="psw"]').send_keys(self.config['Password'])
        driver.find_element_by_xpath('//*[@id="login_form"]/button').click()
        time.sleep(2)
        selenium_cookies = driver.get_cookies()
        for item in selenium_cookies:
            self.S.cookies.set(item["name"], item["value"])
        driver.quit()

    # 获取到列表页的url
    @robust
    def main(self,url):
        response = self.S.get(url=url,headers=self.headers,proxies=self.proxies)
        result = etree.HTML(response.text)
        li_lists = result.xpath('//ul[@class="sub-menu"]/li')
        for i,li_list in enumerate(li_lists):
            index_url = li_list.xpath('./a/@href')[0]
            index_name = li_list.xpath('./a/text()')[0]
            # print(li_list)
            if index_name != '主頁':
                self.get_index(index_url)
            # print(index_url,index_name)
            self.view_bar(i,len(li_lists)-1)

    # 显示下载进度
    def view_bar(self,num, total):
        rate = float(num) / float(total)
        rate_num = int(rate * 100)
        r = "\r" +'进度：' + ("=" * (2 * rate_num // 10) + ">") + (" " * (20 - 2 * rate_num // 10)) + '%d%%' % (rate_num,)
        sys.stdout.write(r)
        sys.stdout.flush()  # 刷新缓冲区

    # 获取到详情页的url
    @robust
    def get_index(self,index_url):
        # set1为分页列表url,set2为所有详情url，set3为分页详情url
        urlQueue = Queue()
        set2 = set()
        # set_all = set()
        response = self.S.get(url=index_url,headers=self.headers,proxies=self.proxies)
        result = etree.HTML(response.text)

        # 获取top_news的详情url
        top_news_urls = result.xpath('//div[@class="top-news"]')
        if top_news_urls:
            top_news_url = top_news_urls[0].xpath('.//a/@href')[0]
            if top_news_url not in self.search_result:
                set2.add(top_news_url)
                # self.get_detail(top_news_url)


        # 获取列表内文章的详情url
        list_contents = result.xpath('//div[@class="list-content"]/div')
        if list_contents:
            for list_content in list_contents:
                detail_url = list_content.xpath('./a/@href')[0]
                if detail_url not in self.search_result:
                    set2.add(detail_url)
                    # self.get_detail(detail_url)

        # 遍历分页文章url利用集合去重
        set1 = set()
        pages = result.xpath('//nav[@class="pagination-bar"]/ul/li')
        if pages:
            for page in pages:
                next_url = page.xpath('./a/@href')
                if len(next_url[0]) > 10:
                    # print('下一页',next_url[0])
                    set1.add(next_url[0])
            for url in set1:
                set3 = self.get_index_page(url)
                for s in set3:
                    set2.add(s)

                # self.get_index_page(url)
        for url in set2:
            urlQueue.put(url)
        threads = []
        threadNum = 2
        for i in range(0, threadNum):
            t = threading.Thread(target=self.get_detail, args=(urlQueue,))
            threads.append(t)
        for t in threads:
            t.start()
        for t in threads:
            # 多线程多join的情况下，依次执行各线程的join方法, 这样可以确保主线程最后退出， 且各个线程间没有阻塞
            t.join()

    # 获取分页到详情页的url
    @robust
    def get_index_page(self,index_url):
        set3 = []
        response = self.S.get(url=index_url, headers=self.headers, proxies=self.proxies)
        result = etree.HTML(response.text)
        # 获取列表内文章的详情url
        list_contents = result.xpath('//div[@class="list-content"]/div')
        if list_contents:
            for list_content in list_contents:
                detail_url = list_content.xpath('./a/@href')[0]
                if detail_url not in self.search_result:
                    set3.append(detail_url)
                    # self.get_detail(detail_url)
        return set3

    # 获取文章详情
    @robust
    def get_detail(self,urlQueue):
        while True:
            try:
                # 不阻塞的读取队列数据
                detail_url = urlQueue.get_nowait()
                # i = urlQueue.qsize()
            except Exception as e:
                break
            # 加异常判断，防止一个请求出错时跳出整个函数
            try:
                response = self.S.get(url=detail_url, headers=self.headers, proxies=self.proxies)
                result = etree.HTML(response.text)
                publishtime = ''
                publishtimes = result.xpath('//div[@class="post-heading supplement-p-h"]/div[@class="date"]/text()')
                for pub in publishtimes:
                    publishtime += pub
                publishtime = publishtime.strip()
                # print(publishtime,str(time.strftime('%Y-%m-%d', time.localtime())))
                if str(publishtime) != str(time.strftime('%Y-%m-%d', time.localtime())):
                    continue

                title = result.xpath('//div[@class="post-heading supplement-p-h"]/h1/text()')
                if title:
                    title = title[0].replace('「', '“').replace('」', '”')
                if title in self.set_detail:
                    continue
                if self.j(title.replace("'", "’")) in self.search_title:
                    continue
                self.set_detail.add(title)
                # print('正在下载:', detail_url)
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
                    sort2_ID = sort2_ID[0]
                source = '星岛日报'
                content_lists = result.xpath('//div[@class="paragraph"]/p')
                content = ''
                for content_list in content_lists:
                    content += '　　' + content_list.xpath('string(.)').replace('\\', '').replace('「', '“').replace('」','”').strip() + '\n\n'
                if content_lists and sort2_ID:
                    if sort2_ID == '港聞' or sort2_ID == '要聞':
                        qx = re.findall('招敢 前綫短評',content_lists[-1].xpath('string(.)'))
                        if qx:
                            authorID = '招敢'
                            sort2_ID = '前綫短評'
                            content = content.replace('招敢 前綫短評','')
                        dq = re.findall('杜良謀 大棋盤',content_lists[-1].xpath('string(.)'))
                        if dq:
                            authorID = '杜良謀'
                            sort2_ID = '大棋盤'
                            content = content.replace('杜良謀 大棋盤','')
                        # sp = re.findall('社評',content_lists[-1])
                        # if sp:
                        #     sort2_ID = '社評'
                        wg = re.findall('盧駿 維港會',content_lists[-1].xpath('string(.)'))
                        if wg:
                            authorID = '盧駿'
                            sort2_ID = '維港會'
                            content = content.replace('盧駿 維港會','')



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
                        self.download_image(standbyID_2[0].replace('\\', ''))
                #         http://static.stheadline.com/stheadline/news_res/2020/02/25/156597/i_src_761840215.jpg
                zoneID = '香港>'
                columnID = '报纸>综合'
                standby2_ID = ''
                standby3_ID = ''
                UNIQUEID = ''
                AUTOADDCLMN = 1

                self.list_mail.append(title)
                data_result = [(
                    URL, self.j(title.replace("'", "’")), self.j(sort2_ID.replace("'", "’")),
                    self.j(standbyID.replace('static.stheadline.com', 'static_stheadline_com')),
                    self.j(content.replace("'", "’")), publishtime, LASTUPDATE,
                    HTMLCONTENT.replace("'", "’"), self.j(authorID.replace("'", "’")), UniqURL, ENCODING, SITE, CATEGORYCODE,
                    PARENTID,
                    self.j(PAGETITLE.replace("'", "’")), CANBEPUBLISHED, NETRESOURCETYPE, source, lang, zoneID, columnID)]
                # print(data_result)
                self.insert_server(data_result)
                # return data_result
            except Exception as e:
                pass
    
    # 邮件发送
    @robust
    def send_mail(self):
        content = ''
        for i,j in enumerate(self.list_mail):
            content += str(i) + ':  ' + j + '\n'
        content += '下载数量为：' + str(len(self.list_mail))
        # 邮件内容
        message = MIMEText(content,'plain', 'utf-8')
        # 括号里的对应发件人邮箱昵称、发件人邮箱账号
        message['From'] = formataddr(['深圳利深', sender])
        message['To'] = '867940410@qq.com'

        # 邮件主题
        subject = '刘飞，以下为星岛日报每日下载数据，请查收！！'
        message['Subject'] = Header(subject, 'utf-8')

        try:
            smtpObj = smtplib.SMTP()
            smtpObj.connect(mail_host, 25)  # 25 为 SMTP 端口号
            smtpObj.login(mail_user, mail_pass)
            smtpObj.sendmail(sender, receivers, message.as_string())
            smtpObj.quit()
            print("ok")
        except smtplib.SMTPException:
            print("false")

    # 图片下载
    @robust
    def download_image(self,image_url):

        image_path = self.download_path + '\\PIC_ZX\\singtao\\' + image_url.split('//')[-1].replace('static.stheadline.com', 'static_stheadline_com').replace(
            image_url.split('/')[-1], '')
        if not os.path.exists(image_path):
            os.makedirs(image_path)
        response = self.S.get('http:' + image_url, headers=self.headers, proxies=self.proxies)
        image_path = self.download_path + '\\PIC_ZX\\singtao\\' + image_url.split('//')[-1].replace('static.stheadline.com', 'static_stheadline_com')
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
        finally:
            self.lock.release()

    # url查询去重
    @robust
    def search_server(self):
        search_sql = "select URL from %s where publishtime='%s'" % (self.config['table'], time.strftime('%Y-%m-%d', time.localtime()))
        self.cursor.execute(search_sql)
        old_url = []
        for i in self.cursor.fetchall():
            old_url.append(i[0])
        # print(old_url)
        return old_url

    # 由于文中有大量重复，添加标题去重
    def srarch_title_server(self):
        search_sql = "select title from %s where publishtime='%s'" % (self.config['table'], time.strftime('%Y-%m-%d', time.localtime()))
        self.cursor.execute(search_sql)
        old_title = []
        for i in self.cursor.fetchall():
            old_title.append(i[0])
        # print(old_url)
        return old_title


    @robust
    def run(self):
        url = 'http://stepaper.stheadline.com/'
        self.main(url)
        self.send_mail()

    @robust
    def __del__(self):
        self.cursor.close()
        self.conn.close()


if __name__ == '__main__':
    start_time = time.time()
    X = XingDao()
    X.run()
    cha = time.time()-start_time
    print('下载完成')
    time.sleep(2)
    with open('time.txt','a+',encoding='utf-8') as f:
        f.write(str(cha) + '\n')


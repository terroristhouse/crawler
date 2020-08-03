import requests
import pyodbc
from lxml import etree
import os,json
from datetime import datetime
import time
import logging
# 声明一个logger对象
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
handler = logging.FileHandler('error.log',encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(lineno)d - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def robust(actual_do):
    def add_robust(*args, **keyargs):
        try:
            return actual_do(*args, **keyargs)
        except Exception as e:
            logger.error(actual_do.__name__ + ':' + str(e), exc_info=True)
    return add_robust

class Standard:
    # 初始化
    @robust
    def __init__(self):
        self.config = self.get_config()
        self.list_mail = []
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'
        }
        self.proxy = {
            'http': '%s'%self.config['proxies']
        }

        self.path = '%s'%self.config['path']
        self.start_time = time.time()
        self.now_time = time.strftime('%Y-%m-%d', time.localtime())
        # self.now_time = '2020-01-16'
        # 链接数据库
        self.conn = pyodbc.connect(r'DRIVER={SQL Server};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s'%(self.config['host'],self.config['databases'],self.config['user'],self.config['password']))
        self.cursor = self.conn.cursor()

    # 获取配置文件
    @robust
    def get_config(self):
        with open('config.json','r',encoding='utf-8') as f:
            data = f.read()
        # return eval(data)
        return json.loads(data)

    # 列表页信息
    @robust
    def get_index(self,url):
        response = requests.get(url,headers=self.headers,proxies=self.proxy)
        result = etree.HTML(response.text)
        url_old = self.get_url()
        div_lists = result.xpath('//div[@class="section-top archive clearfix"]')
        for div_list in div_lists:
            li_lists = div_list.xpath('./ul/li')
            for li_list in li_lists:
                next_url = li_list.xpath('./a/@href')
                if next_url[0] in url_old:
                    continue
                createtime = li_list.xpath('./span/text()')
                try:
                    date = datetime.strptime('%s' % createtime[0], '%d %b %Y %I:%M %p')
                    createtime_1 = date.strftime('%Y-%m-%d')
                except Exception:
                    date = datetime.strptime('%s' % createtime[0], '%d %b %Y')
                    createtime_1 = date.strftime('%Y-%m-%d')
                if createtime_1 != self.now_time:
                    continue
                self.get_detail(next_url[0],createtime_1)

    # 文章详情
    @robust
    def get_detail(self,url,publishtime):
        response = requests.get(url,headers=self.headers,proxies=self.proxy)
        # print(response.status_code)
        result = etree.HTML(response.text)
        source = 'The Standard'
        title = result.xpath('//div[@class="heading clearfix"]/h1/text()')
        authorID = ''
        authorIDs = result.xpath('//span[@class="writer"]/text()')
        if authorIDs:
            authorID = authorIDs[0]

        sort2_ID = result.xpath('//div[@class="heading clearfix"]/span/a/text()')
        content = ''
        contents = result.xpath('//div[@class="content"]//p/text()')
        for con in contents:
            content += con + '\n\n'
        images = result.xpath('//div[@id="myCarousel"]/div[@class="carousel-inner"]/div')
        columnID = 'Newspaper> Synthesis'
        lang = 'en'
        zoneID = 'Hong Kong>'
        standbyID = ''
        for image in images:
            image_url = image.xpath('.//img/@src|.//img/@alt')
            # print('图片标记',image_url)
            image_1 = '〈br〉　　〈img src="http://picture.chinesedata.org/PIC_ZX/thestandard/www_thestandard_com_hk/newsImage/%s" border=0〉〈br〉AABIBCC%sCCBIBAA〈/br〉' % (
            image_url[0].split('/')[-2] + '/' + image_url[0].split('/')[-1], image_url[1])
            standbyID += image_1 + '\n'
            self.download_image(image_url[0])
        # print(url,title[0],source,sort2_ID[0],standbyID,content,publishtime,columnID,lang,zoneID)
        print('数据下载中：',title[0].replace(u'\xa0',''))
        data = [(url,title[0],source,sort2_ID[0],standbyID,content,publishtime,columnID,lang,zoneID,authorID)]
        self.insert_server(data)



    # 下载图片
    @robust
    def download_image(self,url):
        image_path = self.path + '/PIC_ZX/thestandard/www_thestandard_com_hk/newsImage/' + url.split('/')[-2]
        if not os.path.exists(image_path):
            os.makedirs(image_path)
        response = requests.get(url,headers=self.headers,proxies=self.proxy)
        with open(image_path + '/' + url.split('/')[-1],'wb') as f:
            f.write(response.content)

    # 文章写入数据库
    @robust
    def insert_server(self,data):
        self.list_mail.append(data)
        insert_sql = "INSERT INTO {}(URL,title,source,sort2_ID,standbyID,content,publishtime,columnID,lang,zoneID,authorID) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)".format(self.config['table'])
        self.cursor.executemany(insert_sql,data)
        self.conn.commit()

    # 查询去重
    @robust
    def get_url(self):
        search_sql = "select URL from %s where publishtime='%s'"%(self.config['table'],self.now_time)
        # print(search_sql)
        self.cursor.execute(search_sql)
        url_data = self.cursor.fetchall()
        url_list = []
        for url in url_data:
            url_list.append(url[0])
        return url_list

    # 启动函数
    @robust
    def run(self):
        url = 'https://www.thestandard.com.hk/archive.php?date=%s'%self.now_time
        print(url)
        self.get_index(url)
        self.write_log(self.start_time)

    # 析构方法
    @robust
    def __del__(self):
        self.cursor.close()
        self.conn.close()


    # 写入日志
    @robust
    def write_log(self, start_time):
        cha = time.time() - start_time
        content = '-TheStandard %s 下载数量：%s 用时：%s\n' % (
        time.strftime('%Y-%m-%d %H:%M:%S'), str(len(self.list_mail)), cha)
        with open('TheStandard.txt', 'a+', encoding='utf-8') as f:
            f.write(content)


if __name__ == '__main__':
    S = Standard()
    S.run()
    del S

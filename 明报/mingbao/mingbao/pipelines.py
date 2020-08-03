# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import pyodbc

from scrapy import Request
from scrapy.exceptions import DropItem
from scrapy.pipelines.images import ImagesPipeline
from mingbao.settings import host,user1,password1,database,table,today_url
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

# print(host,user1,password1,table)
# 第三方 SMTP 服务
mail_host = "smtp.126.com"  # 设置服务器
mail_user = "q867940410@126.com"  # 用户名
mail_pass = "q867940410"  # 口令

# 发件人
sender = 'q867940410@126.com'
receivers = ['867940410@qq.com']  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱
list1 = []

class MingbaoPipeline(object):
    def process_item(self, item, spider):
        return item

class SqlserverPipeline(object):

    def open_spider(self,spider):

        self.conn = pyodbc.connect(r'DRIVER={SQL Server Native Client 11.0};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s'%(host,database,user1,password1))
        # self.conn = pyodbc.connect(r'DRIVER={SQL Server Native Client 11.0};SERVER=127.0.0.1;DATABASE=HKNEWS;UID=sa;PWD=root')
        self.cursor = self.conn.cursor()

        search_sql = "select URL from %s where publishtime='%s'" % (table,today_url)
        # search_sql = "select URL from HKNEWSDATA_CHI_02 where publishtime='%s'" % today_url
        self.cursor.execute(search_sql)
        self.old_url = []
        for i in self.cursor.fetchall():
            self.old_url.append(i[0])

    def process_item(self,item,spider):
        if item['URL'] in self.old_url:
            print('数据已存在',item['title'])
            raise DropItem()
            pass

        else:
            list1.append(item['title'])
            data = [(item['URL'],item['title'],item['sort2_ID'],item['standbyID'],item['content'],item['publishtime'],item['LASTUPDATE'],item['HTMLCONTENT'],item['authorID'],item['UniqURL'],item['ENCODING'],item['SITE'],item['CATEGORYCODE'],item['PARENTID'],item['PAGETITLE'],item['CANBEPUBLISHED'],item['NETRESOURCETYPE'],item['source'],item['lang'],item['zoneID'],item['columnID'])]
            insert_sql = "INSERT INTO {}(URL,title,sort2_ID,standbyID,content,publishtime,LASTUPDATE,HTMLCONTENT,authorID,UniqURL,ENCODING,SITE,CATEGORYCODE,PARENTID,PAGETITLE,CANBEPUBLISHED,NETRESOURCETYPE,source,lang,zoneID,columnID) VALUES (?, ?, ?, ?, ?, ?, ?, ?,?,?,?,?,?,?,?,?,?,?,?,?,?)".format(table)
            # insert_sql = "INSERT INTO HKNEWSDATA_CHI_02(URL,title,sort2_ID,standbyID,content,publishtime,LASTUPDATE,HTMLCONTENT,authorID,UniqURL,ENCODING,SITE,CATEGORYCODE,PARENTID,PAGETITLE,CANBEPUBLISHED,NETRESOURCETYPE,source,lang,zoneID,columnID) VALUES (?, ?, ?, ?, ?, ?, ?, ?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
            self.cursor.executemany(insert_sql, data)
            self.conn.commit()
            print('数据下载中:',item['title'])
        return item
    def close_spider(self,spider):
        self.cursor.close()
        self.conn.close()
        # 邮件内容
        content = ''
        for i,j in enumerate(list1):
            content += str(i) + ':  ' + j + '\n'
        content += '下载数量为：' + str(len(list1))
        message = MIMEText(content,'plain', 'utf-8')
        # message['From'] = 'q867940410@126.com'
        # message['To'] = '867940410@qq.com'
        message['From'] = formataddr(['深圳利深',sender])
        message['To'] = '867940410@qq.com'
        # 邮件主题
        message['Subject'] = Header('刘飞，以下为明报每日下载数据,请查收!!', 'utf-8')
        try:
            smtpObj = smtplib.SMTP()
            smtpObj.connect(mail_host, 25)  # 25 为 SMTP 端口号
            smtpObj.login(mail_user, mail_pass)
            smtpObj.sendmail(sender, receivers, message.as_string())
            smtpObj.quit()
            print("ok")
        except smtplib.SMTPException:
            print("false")

# \PIC_ZX\mingpao\fs_mingpao_com\pns
class DowonImagePipeline(ImagesPipeline):
    def file_path(self, request, response=None, info=None):
        url = request.url
        # file_name = IMAGES_STORE + r'/PIC_ZX/mingpao/fs_mingpao_com/pns' + url.split('/')[-3] + url.split('/')[-2]
        # if not os.path.exists(file_name):
        #     os.makedirs(file_name)
        image_path = '/PIC_ZX/mingpao/fs_mingpao_com/pns' + url.split('pns')[-1]
        return image_path

    def item_completed(self, results, item, info):
        image_paths = [x['path'] for ok, x in results if ok]
        if not image_paths:
            raise DropItem('Image Downloaded Failed')
        return item

    def get_media_requests(self, item, info):
        # print(item['image_url'])
        for url in item['image_url']:
            yield Request(url=url)


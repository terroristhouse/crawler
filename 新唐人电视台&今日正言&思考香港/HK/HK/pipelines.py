# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import pyodbc
import time
from scrapy import Request
from scrapy.exceptions import DropItem
from scrapy.pipelines.images import ImagesPipeline
from HK.settings import host,user1,password1,database,table,today_url

import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr



class HkPipeline(object):
    def process_item(self, item, spider):
        return item

# 思考香港写入数据库
class SqlserverPipeline(object):

    def open_spider(self,spider):
        self.start_time = time.time()
        self.list1 = []
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
            self.list1.append(item['title'])
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
        cha = time.time() - self.start_time
        content = '-思考香港 %s 下载数量：%s 用时：%s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), str(len(self.list1)), cha)
        with open('思考香港.txt', 'a+', encoding='utf-8') as f:
            f.write(content)
        print("thinkHKok")


# 新唐人电视台写入数据库
class SqlserverTVPipeline(object):

    def open_spider(self,spider):
        self.start_time = time.time()
        self.list1 = []
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
            self.list1.append(item['title'])
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
        cha = time.time() - self.start_time
        content = '-新唐人电视台 %s 下载数量：%s 用时：%s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), str(len(self.list1)), cha)
        with open('新唐人电视台.txt', 'a+', encoding='utf-8') as f:
            f.write(content)
        print("ntdtvok")

# 今日正言写入数据库
class Sqlservertodayipeline(object):

    def open_spider(self,spider):
        self.start_time = time.time()
        self.list1 = []
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
            self.list1.append(item['title'])
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
        cha = time.time() - self.start_time
        content = '-今日正言 %s 下载数量：%s 用时：%s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), str(len(self.list1)), cha)
        with open('今日正言.txt', 'a+', encoding='utf-8') as f:
            f.write(content)
        print("todayreview88ok")

# 思考香港图片下载
class DowonImagePipeline(ImagesPipeline):
    def file_path(self, request, response=None, info=None):
        url = request.url
        # file_name = IMAGES_STORE + r'/PIC_ZX/mingpao/fs_mingpao_com/pns' + url.split('/')[-3] + url.split('/')[-2]
        # if not os.path.exists(file_name):
        #     os.makedirs(file_name)
        image_path = '/PIC_ZX/thinkhk/www_thinkhk_com/d/file/' + url.split('file')[-1]
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

# 新唐人电视台图片下载
class DowonImageTVPipeline(ImagesPipeline):
    def file_path(self, request, response=None, info=None):
        url = request.url
        # file_name = IMAGES_STORE + r'/PIC_ZX/mingpao/fs_mingpao_com/pns' + url.split('/')[-3] + url.split('/')[-2]
        # if not os.path.exists(file_name):
        #     os.makedirs(file_name)
        image_path = '/PIC_ZX/%s'%url.split('//')[-1].replace('i.ntdtv.com','i_ntdtv_com')
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

# 今日正言图片下载
class DowonImagetodayPipeline(ImagesPipeline):
    def file_path(self, request, response=None, info=None):
        url = request.url
        # file_name = IMAGES_STORE + r'/PIC_ZX/mingpao/fs_mingpao_com/pns' + url.split('/')[-3] + url.split('/')[-2]
        # if not os.path.exists(file_name):
        #     os.makedirs(file_name)
        image_path = '/PIC_ZX/%s'%url.split('//')[-1].replace('img.todayreview88.com', 'img_todayreview88_com').rstrip('!s800')
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

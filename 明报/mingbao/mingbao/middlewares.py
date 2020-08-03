# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import pyodbc
from scrapy import signals
from mingbao.settings import proxies
from mingbao.settings import host,user1,password1,database,table,today_url
from scrapy.exceptions import IgnoreRequest

class MyProxy(object):
    def process_request(self,request,spider):
        request.meta['proxy'] = 'http://%s'%proxies
        # request.meta['proxy'] = 'http://192.168.0.70:80'


class MingbaoQuchongMiddleware(object):
    def __init__(self):
        # print('数据库链接')
        self.conn = pyodbc.connect(r'DRIVER={SQL Server Native Client 11.0};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s' % (
        host, database, user1, password1))
        # self.conn = pyodbc.connect(r'DRIVER={SQL Server Native Client 11.0};SERVER=127.0.0.1;DATABASE=HKNEWS;UID=sa;PWD=root')
        self.cursor = self.conn.cursor()

        search_sql = "select URL from %s where publishtime='%s'" % (table, today_url)
        # search_sql = "select URL from HKNEWSDATA_CHI_02 where publishtime='%s'" % today_url
        self.cursor.execute(search_sql)
        self.old_url = []
        for i in self.cursor.fetchall():
            self.old_url.append(i[0])

    def process_request(self,request,spider):
        if request.url in self.old_url:
            print('中间件判断，数据库已存在')
            raise IgnoreRequest()
        # print(request.url)


    def __del__(self):
        # print('数据库关闭')
        self.cursor.close()
        self.conn.close()


class MingbaoSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class MingbaoDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)

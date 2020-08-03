
import sys,os
if hasattr(sys, 'frozen'):
    os.environ['PATH'] = sys._MEIPASS + ";" + os.environ['PATH']

import scrapy.spiderloader
import scrapy.statscollectors
import scrapy.logformatter
import scrapy.dupefilters
import scrapy.squeues

import scrapy.extensions.spiderstate
import scrapy.extensions.corestats
import scrapy.extensions.telnet
import scrapy.extensions.logstats
import scrapy.extensions.memusage
import scrapy.extensions.memdebug
import scrapy.extensions.feedexport
import scrapy.extensions.closespider
import scrapy.extensions.debug
import scrapy.extensions.httpcache
import scrapy.extensions.statsmailer
import scrapy.extensions.throttle

import scrapy.core.scheduler
import scrapy.core.engine
import scrapy.core.scraper
import scrapy.core.spidermw
import scrapy.core.downloader

import scrapy.downloadermiddlewares.stats
import scrapy.downloadermiddlewares.httpcache
import scrapy.downloadermiddlewares.cookies
import scrapy.downloadermiddlewares.useragent
import scrapy.downloadermiddlewares.httpproxy
import scrapy.downloadermiddlewares.ajaxcrawl
# import scrapy.downloadermiddlewares.chunked
import scrapy.downloadermiddlewares.decompression
import scrapy.downloadermiddlewares.defaultheaders
import scrapy.downloadermiddlewares.downloadtimeout
import scrapy.downloadermiddlewares.httpauth
import scrapy.downloadermiddlewares.httpcompression
import scrapy.downloadermiddlewares.redirect
import scrapy.downloadermiddlewares.retry
import scrapy.downloadermiddlewares.robotstxt

import scrapy.spidermiddlewares.depth
import scrapy.spidermiddlewares.httperror
import scrapy.spidermiddlewares.offsite
import scrapy.spidermiddlewares.referer
import scrapy.spidermiddlewares.urllength

import scrapy.pipelines

import scrapy.core.downloader.handlers.http
import scrapy.core.downloader.contextfactory
import scrapy.core.downloader.handlers.ftp
import scrapy.core.downloader.handlers.datauri
import scrapy.core.downloader.handlers.file
import scrapy.core.downloader.handlers.s3

from scrapy.http import Request,FormRequest
import re

from lxml import etree
from HK.settings import today_url
import pyodbc
from HK.settings import today_url
from scrapy import Request
from scrapy.exceptions import DropItem
from scrapy.pipelines.images import ImagesPipeline
from HK.items import HkItem
from HK import zh_wiki
from copy import deepcopy
from HK.zh_wiki import zh2Hant, zh2Hans
from HK.settings import host,user1,password1,database,table,proxies
import json
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

# from PyQt5.QtCore import QThread,QCoreApplication
# from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton,QTextBrowser, QHBoxLayout, QVBoxLayout
# from PyQt5.QtGui import QIcon
# from multiprocessing import Process, Manager
# import multiprocessing

import time
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# from HK.spiders.ntdtv import NtdtvSpider
# from HK.spiders.thinkHK import ThinkhkSpider
# from HK.spiders.todayreview88 import Todayreview88Spider


process = CrawlerProcess(get_project_settings())
process.crawl('thinkHK')
process.crawl('ntdtv')
process.crawl('todayreview88')
process.start()


# def crawl(Q):
#     # CrawlerProcess
#     start_time = time.time()
#     process = CrawlerProcess(get_project_settings())
#     process.crawl(NtdtvSpider, Q=Q)
#     process.crawl(ThinkhkSpider, Q=Q)
#     process.crawl(Todayreview88Spider, Q=Q)
#
#     process.start()
#     Q.put('爬取完成,即将关闭页面')
#     with open('time.txt', 'a+', encoding='utf-8') as f:
#         f.write(str(time.time()-start_time) + '\n')
#
#     for j in range(3):
#         i = 3
#         i -= j
#         Q.put(str(i))
#         time.sleep(1)
#     Q.put('爬取结束***')
#
#     # CrawlerRunner
#     """runner = CrawlerRunner(settings={
#         'USER_AGENT': ua,
#         'ROBOTSTXT_OBEY': is_obey
#         # 'HTTPPROXY_ENABLED': False
#         # 在Mac系统上，请加上'HTTPPROXY_ENABLED': False
#     })
#
#     d = runner.crawl(BookSpider, Q=Q)
#     d.addBoth(lambda _: reactor.stop())
#     reactor.run()"""
#
#
# class Demo(QWidget):
#     def __init__(self):
#         super(Demo, self).__init__()
#         self.setWindowTitle('今日正言&新唐人电视台&思考香港')
#         self.setWindowIcon(QIcon(res_path('res/HK.ico')))
#         self.resize(700,400)
#
#         self.log_browser = QTextBrowser(self)            # 日志输出框
#         self.crawl_btn = QPushButton('Python爬虫', self)    # 开始爬取按钮
#
#         # 布局
#         self.h_layout = QHBoxLayout()
#         self.v_layout = QVBoxLayout()
#         self.v_layout.addWidget(QLabel('日志输出框'))
#         self.v_layout.addWidget(self.log_browser)
#         self.v_layout.addWidget(self.crawl_btn)
#         self.setLayout(self.v_layout)
#
#         self.Q = Manager().Queue()
#         self.log_thread = LogThread(self)
#         self.crawl_slot()
#     def crawl_slot(self):
#         self.p = Process(target=crawl, args=(self.Q,))
#         self.p.start()
#         self.log_thread.start()
#
#     def closeEvent(self, event):
#         self.p.terminate()
#         self.log_thread.terminate()
#
#
# class LogThread(QThread):
#     def __init__(self, gui):
#         super(LogThread, self).__init__()
#         self.gui = gui
#
#     def run(self):
#         while True:
#             if not self.gui.Q.empty():
#                 self.gui.log_browser.append(self.gui.Q.get())
#
#                 # 确保滑动条到底
#                 cursor = self.gui.log_browser.textCursor()
#                 pos = len(self.gui.log_browser.toPlainText())
#                 cursor.setPosition(pos)
#                 self.gui.log_browser.setTextCursor(cursor)
#
#                 if '爬取结束***' in self.gui.log_browser.toPlainText():
#                     QCoreApplication.quit()
#                     break
#
#                 # 睡眠10毫秒，否则太快会导致闪退或者显示乱码
#                 self.msleep(10)
#
# # 获取资源绝对路径
# def res_path(relative_path):
#     """获取资源绝对路径"""
#     try:
#         base_path = sys._MEIPASS
#     except Exception:
#         base_path = os.path.abspath(".")
#
#     return os.path.join(base_path, relative_path)
#
# if __name__ == '__main__':
#     multiprocessing.freeze_support()
#     app = QApplication(sys.argv)
#     demo = Demo()
#     demo.show()
#     sys.exit(app.exec_())


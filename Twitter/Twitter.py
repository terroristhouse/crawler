# coding:utf-8

# 数据库
import pyodbc
# 浏览器
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time, os,sys
import requests
import re, random
# 多进程
from multiprocessing import freeze_support,Pool
import multiprocessing
import dateutil.parser
# 邮件发送
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
# 界面
from PyQt5.QtCore import QThread,QCoreApplication
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton,QTextBrowser, QHBoxLayout, QVBoxLayout
from multiprocessing import Process, Manager
from PyQt5.QtGui import QIcon
# 日志记录
import logging

# 日志
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.WARN)
# Formatter
formatter = logging.Formatter('%(asctime)s -%(funcName)s - %(levelname)s - %(lineno)d - %(message)s')
file_handler = logging.FileHandler('error.txt', encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


# 捕获异常装饰器
def robust(actual_do):
    def add_robust(*args, **keyargs):
        try:
            return actual_do(*args, **keyargs)
        except Exception as e:
            logger.error(actual_do.__name__ + ':' + str(e), exc_info=True)
    return add_robust


class Twitter:

    instant = None

    # 使用单例模式，多次调用继续使用第一次调用的地址
    def __new__(cls, *args, **kwargs):
        if cls.instant is None:
            cls.instant = super().__new__(cls)
        return cls.instant

    # 初始化参数
    @robust
    def __init__(self,Q):
        self.Q=Q
        self.config = self.get_config()
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'
        }
        self.proxy = {
            'http': '%s' % self.config['proxies']
        }
        # 创建图片文件夹
        self.path = '%s' % self.config['path']

        if not os.path.exists(self.path):
            os.makedirs(self.path)

    # 读取配置文件
    @robust
    def get_config(self):
        with open(r'confige.txt', 'r', encoding='utf-8') as f:
            config = f.read()
        return eval(config)

    """数据库查询相关"""
    # 获取目标url
    @robust
    def search_url(self):
        conn = pyodbc.connect(r'DRIVER={SQL Server};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s' % (
            self.config['host'], self.config['databases'], self.config['user'], self.config['password']))
        cursor = conn.cursor()
        # 从数据库中读取url
        url_list = []
        cursor.execute("select convert(nvarchar(255),TNAME),TURL from TWITTER_SOURCE")
        urls = cursor.fetchall()
        for url in urls:
            url_list.append([url[0], url[1]])
        cursor.close()
        conn.close()
        return url_list

    # 评论查询去重
    @robust
    def search_comment(self, link_url=None):
        old_list = []
        search_sql = "SELECT URL FROM TWITTER_COMMENTS WHERE link_url='{}'".format(link_url)
        self.comment_cursor.execute(search_sql)
        for i in self.comment_cursor.fetchall():
            old_list.append(i[0])
        return old_list

    # 已抓取的评论数量查询，判断是否增量爬取
    @robust
    def search_old_comment(self, link_url):
        search_sql = "select comments FROM TWITTER where URL='%s'" % link_url
        self.cursor.execute(search_sql)
        return self.cursor.fetchone()[0]

    # 主页信息查询去重
    @robust
    def search_index(self, url):
        link_urls = []
        self.cursor.execute("select top 500 URL FROM TWITTER where SOURCE='%s' ORDER BY AUTOADDCLMN DESC" % url[0])
        for i in self.cursor.fetchall():
            link_urls.append(i[0])
        return link_urls

    """数据获取"""
    # 获取主推信息
    @robust
    def get_index(self, url, key):
        self.driver.execute_script("window.open('%s')"%url[1])
        # self.driver.get(url[1])
        # exit()
        time.sleep(0.5)
        handles = self.driver.window_handles  # 获取当前窗口句柄集合（列表类型）
        time.sleep(0.5)
        self.driver.switch_to.window(handles[1])
        is_break = True
        old_linkurl = []
        index_max = 1500
        try:
            while is_break:
                # try:
                #     self.driver.find_element_by_xpath('//div[starts-with(@class,"css-18t94o4 css-1dbjc4n r-urgr8i r-42olwf")]')
                #     self.driver.delete_all_cookies()
                #     print('限速提醒')
                #     self.Q.put('{}:限速提醒，清除cookies{},重新加入队列'.format(time.strftime('%Y-%m-%d %H:%M:%S'), url[0]))
                #     # self.clear_cookies()
                #     self.driver.quit()
                #     self.q.put(url)
                # except Exception as e:
                #     pass
                # 获取页面所有推文信息
                result = self.wait.until(lambda driver: driver.find_elements_by_xpath(
                    '//div[starts-with(@class,"css-1dbjc4n r-my5ep6 r-qklmqi r-1adg3ll") and not(starts-with(@class,"js-stream-item stream-item stream-item js-pinned"))]'))
                Text_height0 = self.driver.execute_script("var q=document.documentElement.scrollTop;return(q)")
                for i in result:
                    try:
                        try:
                            link_url = i.find_element_by_xpath(
                                './/div[@class="css-1dbjc4n r-1d09ksm r-18u37iz r-1wbh5a2"]/a').get_attribute('href')
                            timestamp0 = i.find_element_by_xpath(
                                './/div[@class="css-1dbjc4n r-1d09ksm r-18u37iz r-1wbh5a2"]/a/time').get_attribute(
                                'datetime')
                            # 评论，转发，点赞
                            try:
                                # action_count = i.find_element_by_xpath('.//div[@class="css-1dbjc4n r-18u37iz r-1wtj0ep r-psjefw r-1mdbhws"]').get_attribute('aria-label')
                                action_count = i.find_element_by_xpath('.//div[starts-with(@class,"css-1dbjc4n r-18u37iz r-1wtj0ep")]').get_attribute('aria-label')
                                # class="css-1dbjc4n r-18u37iz r-1wtj0ep r-156q2ks r-1mdbhws"
                                # class="css-1dbjc4n r-18u37iz r-1wtj0ep r-psjefw r-1mdbhws"
                                #
                                # print(action_count)
                                comments = re.findall('(\d+) replies,', str(action_count), re.S)
                                like = re.findall('(\d+) likes', str(action_count), re.S)
                                retweet = re.findall('(\d+) Retweets,', str(action_count), re.S)
                                if not comments:
                                    comments = re.findall('(\d+) 回复', str(action_count), re.S)
                                if not like:
                                    like = re.findall('(\d+) 喜欢', str(action_count), re.S)
                                if not retweet:
                                    retweet = re.findall('(\d+) 转推', str(action_count), re.S)
                                if comments:
                                    comments = comments[0]
                                else:
                                    comments = 0
                                if retweet:
                                    retweet = retweet[0]
                                else:
                                    retweet = 0
                                if like:
                                    like = like[0]
                                else:
                                    like = 0
                            except Exception:
                                comments = 0
                                retweet = 0
                                like = 0
                            try:
                                cont = int(retweet) * 0.3 + int(comments) * 0.4 + int(like) * 0.4
                            except Exception:
                                cont = 0
                            d = dateutil.parser.parse(timestamp0)
                            timestamp1 = d.strftime('%Y-%m-%d %H:%M:%S')
                            bj_time = time.mktime(time.strptime(timestamp1, '%Y-%m-%d %H:%M:%S')) + 8 * 60 * 60
                            times_file = time.strftime('%Y%m%d', time.localtime(bj_time))
                            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(bj_time))
                            try:
                                i.find_element_by_xpath('.//div[@class="css-1dbjc4n r-obd0qt r-18kxxzh r-5f2r5o"]')
                                is_retweet = '转推'
                            except Exception:
                                is_retweet = ''
                            try:
                                i.find_element_by_xpath('.//div[@class="css-1dbjc4n r-obd0qt r-18kxxzh r-5f2r5o"]')
                                pinnedTweet = '置顶'
                            except Exception:
                                pinnedTweet = ''
                            if not is_retweet and not pinnedTweet:
                                # 推特发表时间大于一天时退出循环
                                if time.time() - bj_time > 86400:
                                    is_break = False
                                    break
                            if link_url in old_linkurl:
                                # print('旧的数据')
                                continue
                            old_linkurl.append(link_url)

                            if link_url.replace('https://twitter.com', '') in self.search_index_:
                                # print('推特内容已抓取', link_url)
                                # 评论增量
                                if int(comments) != 0:
                                    old_comment = self.search_old_comment(link_url.replace('https://twitter.com', ''))
                                    cha = int(old_comment) / int(comments)
                                    if cha < 0.9:
                                        self.Q.put('{}:评论增量:{}'.format(time.strftime('%Y-%m-%d %H:%M:%S'), url[0]))
                                        self.get_detail(i=i, key=key,parent_url=link_url.replace('https://twitter.com', ''))
                                # 更新数据
                                update_data = [retweet,comments,like,cont,link_url.replace('https://twitter.com', '')]
                                self.update_index(update_data)

                                continue

                        except Exception as e:
                            # ActionChains(driver).move_by_offset(5, 5).click().perform()
                            continue

                        # # 创建下一级图片库
                        if not os.path.exists(self.path + '\\%s\\%s' % (key, times_file)):
                            os.makedirs(self.path + '\\%s\\%s' % (key, times_file))
                        # isbreak = False
                        # 推文
                        tweet_text = ''
                        try:
                            # tweet_texts = i.find_elements_by_xpath('.//div[@class="css-901oao r-hkyrab r-1qd0xha r-1b43r93 r-16dba41 r-ad9z0x r-bcqeeo r-bnwqim r-qvutc0"]/span')
                            tweet_texts = i.find_elements_by_xpath('.//div[starts-with(@class,"css-901oao r-hkyrab r-1qd0xha")]/span')
                            # class="css-901oao r-hkyrab r-1qd0xha r-1b43r93 r-16dba41 r-ad9z0x r-bcqeeo r-bnwqim r-qvutc0"
                            # class="css-901oao r-hkyrab r-1qd0xha r-a023e6 r-16dba41 r-ad9z0x r-bcqeeo r-bnwqim r-qvutc0"
                            for tweet in tweet_texts:
                                tweet_text += tweet.get_attribute('textContent')
                        except Exception as e:
                            print(e)

                        try:
                            twimgs = i.find_elements_by_xpath(
                                './/div[starts-with(@class,"css-1dbjc4n r-1p0dtai r-1mlwlqe r-1d2f490")]')
                            # print(twimgs)
                            picture = len(twimgs)
                            twimg = []
                            for img in twimgs:
                                twimg0 = img.find_element_by_xpath('.//img').get_attribute('src')
                                twimg.append(twimg0)
                        except Exception as e:
                            # print(e)
                            picture = 0
                            twimg = []

                        # 下载图片
                        if twimg:
                            for timg, x in zip(twimg, range(len(twimg))):
                                # image_name = timg.split('/')[-1]
                                if x == 0:
                                    down_img = requests.get(timg, headers=self.headers, proxies=self.proxy)
                                    with open(self.path + '\\%s\\%s\\' % (key, times_file) + link_url.split('/')[
                                        -1] + '.jpg', 'wb') as f:
                                        f.write(down_img.content)
                                else:
                                    down_img = requests.get(timg, headers=self.headers, proxies=self.proxy)
                                    with open(self.path + '\\%s\\%s\\' % (key, times_file) + link_url.split('/')[
                                        -1] + '_' + str(int(x) + 1) + '.jpg', 'wb') as f:
                                        f.write(down_img.content)



                        data = [
                            (url[0], link_url.replace('https://twitter.com', ''), link_url.split('/')[-1], timestamp,
                             tweet_text.replace("'", "’"), str(picture), int(retweet), int(comments),
                             int(like), cont)]
                        # print('正在抓取', url[0])
                        self.Q.put('{}:抓取数据:{}'.format(time.strftime('%Y-%m-%d %H:%M:%S'),url[0]))
                        # 推文写入数据库
                        self.insert_server(data)
                        # 评论抓取
                        if int(comments) != 0:
                            self.Q.put('{}:评论抓取:{}'.format(time.strftime('%Y-%m-%d %H:%M:%S'), url[0]))
                            self.get_detail(i=i,key=key,parent_url=link_url.replace('https://twitter.com', ''))


                    except Exception as e:
                        logger.error('遍历推特主文时出错',exc_info=True)

                self.driver.execute_script("window.scrollTo(0, %s);" % index_max)
                time.sleep(2)
                Text_height1 = self.driver.execute_script("var q=document.documentElement.scrollTop;return(q)")

                # print(Text_height0,Text_height1)
                if Text_height0 == Text_height1:
                    # print('到达底线')
                    is_break = False
                index_max += 1500
                time.sleep(2)
        except Exception as e:
            pass
        self.driver.close()
        self.driver.switch_to.window(handles[0])

    # 获取评论信息
    @robust
    def get_detail(self, i=None, key=None, parent_url=None):
        # i.click()
        old_comments_list = self.search_comment(parent_url)
        old_comments_list1 = []
        ActionChains(self.driver).key_down(Keys.CONTROL).click(
            i.find_element_by_xpath('.//div[@class="css-1dbjc4n r-1d09ksm r-18u37iz r-1wbh5a2"]/a')).key_up(
            Keys.CONTROL).perform()
        time.sleep(1)
        handles = self.driver.window_handles  # 获取当前窗口句柄集合（列表类型）
        # print(handles, '1111')
        self.driver.switch_to.window(handles[2])
        comments_break = True
        comments_max = 1500
        # 清除cookies
        self.driver.delete_all_cookies()
        try:
            while comments_break:
                try:
                    # mores = self.driver.find_elements_by_xpath('.//div[@class="css-901oao r-1n1174f r-1qd0xha r-1b43r93 r-16dba41 r-ad9z0x r-bcqeeo r-qvutc0"]')
                    mores = self.driver.find_elements_by_xpath('//div[starts-with(@class,"css-901oao r-1n1174f r-1qd0xha")]')
                    # class="css-901oao r-1n1174f r-1qd0xha r-a023e6 r-16dba41 r-ad9z0x r-bcqeeo r-qvutc0"
                    # class="css-901oao r-1n1174f r-1qd0xha r-1b43r93 r-16dba41 r-ad9z0x r-bcqeeo r-qvutc0"

                    for more in mores:
                        self.driver.execute_script("arguments[0].click();", more)
                    time.sleep(3)
                except Exception as e:
                    pass
                    # print('更多评论点击', e)
                comments_Text_height0 = self.driver.execute_script(
                    "var q=document.documentElement.scrollTop;return(q)")
                # div_lists = self.wait.until(lambda driver: driver.find_elements_by_xpath('//div[@class="css-1dbjc4n r-14mgfza"]/div/section/div/div/div/div'))
                div_lists = self.wait.until(lambda driver: driver.find_elements_by_xpath('//article[starts-with(@class,"css-1dbjc4n r-1loqt21")]'))
                # class="css-1dbjc4n r-1loqt21 r-1udh08x r-o7ynqc r-6416eg"
                # class="css-1dbjc4n r-1loqt21 r-16y2uox r-1wbh5a2 r-1udh08x r-1j3t67a r-o7ynqc r-6416eg"
                for div_list in div_lists:
                    try:
                        # SOURCE = div_list.find_element_by_xpath('.//div[@class="css-901oao css-bfa6kz r-hkyrab r-1qd0xha r-1b43r93 r-vw2c0b r-ad9z0x r-bcqeeo r-3s2u2q r-qvutc0"]/span/span[@class="css-901oao css-16my406 r-1qd0xha r-ad9z0x r-bcqeeo r-qvutc0"]').get_attribute('textContent')
                        SOURCE = div_list.find_element_by_xpath('.//div[starts-with(@class,"css-901oao css-bfa6kz r-hkyrab r-1qd0xha")]/span/span[@class="css-901oao css-16my406 r-1qd0xha r-ad9z0x r-bcqeeo r-qvutc0"]').get_attribute('textContent')
                        # div
                        # class="css-901oao css-bfa6kz r-hkyrab r-1qd0xha r-a023e6 r-vw2c0b r-ad9z0x r-bcqeeo r-3s2u2q r-qvutc0"
                        # class="css-901oao css-bfa6kz r-hkyrab r-1qd0xha r-1b43r93 r-vw2c0b r-ad9z0x r-bcqeeo r-3s2u2q r-qvutc0"

                        # span
                        # class="css-901oao css-16my406 r-1qd0xha r-ad9z0x r-bcqeeo r-qvutc0"
                        # class="css-901oao css-16my406 r-1qd0xha r-ad9z0x r-bcqeeo r-qvutc0"
                        try:
                            # content = div_list.find_element_by_xpath('.//div[@class="css-901oao r-hkyrab r-1qd0xha r-1b43r93 r-16dba41 r-ad9z0x r-bcqeeo r-bnwqim r-qvutc0"]/span').get_attribute('textContent')
                            content = div_list.find_element_by_xpath('.//div[starts-with(@class,"css-901oao r-hkyrab r-1qd0xha")]/span').get_attribute('textContent')
                        # class="css-901oao r-hkyrab r-1qd0xha r-1b43r93 r-16dba41 r-ad9z0x r-bcqeeo r-bnwqim r-qvutc0"
                        # class="css-901oao r-hkyrab r-1qd0xha r-a023e6 r-16dba41 r-ad9z0x r-bcqeeo r-bnwqim r-qvutc0"
                        except Exception:
                            content = ''
                        timestamp0 = div_list.find_element_by_xpath('.//div[@class="css-1dbjc4n r-1d09ksm r-18u37iz r-1wbh5a2"]/a/time').get_attribute('datetime')
                        link_url = div_list.find_element_by_xpath('.//div[@class="css-1dbjc4n r-1d09ksm r-18u37iz r-1wbh5a2"]/a').get_attribute('href')
                        if link_url.replace('https://twitter.com', '') in old_comments_list:
                            # print('此评论已抓取')
                            continue
                        if link_url in old_comments_list1:
                            # print('旧的评论')
                            continue
                        old_comments_list1.append(link_url)
                        d = dateutil.parser.parse(timestamp0)
                        timestamp1 = d.strftime('%Y-%m-%d %H:%M:%S')
                        bj_time = time.mktime(time.strptime(timestamp1, '%Y-%m-%d %H:%M:%S')) + 8 * 60 * 60
                        times_file = time.strftime('%Y%m%d', time.localtime(bj_time))
                        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(bj_time))
                        # 获取评论，喜欢，转推
                        try:
                            action_count = div_list.find_element_by_xpath('.//div[starts-with(@class,"css-1dbjc4n r-18u37iz r-1wtj0ep")]').get_attribute('aria-label')
                            # class="css-1dbjc4n r-18u37iz r-1wtj0ep r-156q2ks r-1mdbhws"
                            # class="css-1dbjc4n r-18u37iz r-1wtj0ep r-psjefw r-1mdbhws"
                            # print(action_count)
                            comments = re.findall('(\d+) replies,', str(action_count), re.S)
                            like = re.findall('(\d+) likes', str(action_count), re.S)
                            retweet = re.findall('(\d+) Retweets,', str(action_count), re.S)
                            if not comments:
                                comments = re.findall('(\d+) 回复', str(action_count), re.S)
                            if not like:
                                like = re.findall('(\d+) 喜欢', str(action_count), re.S)
                            if not retweet:
                                retweet = re.findall('(\d+) 转推', str(action_count), re.S)
                            if comments:
                                comments = comments[0]
                            else:
                                comments = 0
                            if retweet:
                                retweet = retweet[0]
                            else:
                                retweet = 0
                            if like:
                                like = like[0]
                            else:
                                like = 0
                        except Exception:
                            comments = 0
                            retweet = 0
                            like = 0

                        # 获取图片信息
                        try:
                            twimgs = div_list.find_elements_by_xpath(
                                './/div[starts-with(@class,"css-1dbjc4n r-1p0dtai r-1mlwlqe r-1d2f490")]')
                            # print(twimgs)
                            picture = len(twimgs)
                            twimg = []
                            for img in twimgs:
                                twimg0 = img.find_element_by_xpath('.//img').get_attribute('src')
                                twimg.append(twimg0)
                        except Exception as e:
                            # print(e)
                            picture = 0
                            twimg = []
                        # 存储图片
                        # if twimg:
                        # for timg, x in zip(twimg, range(len(twimg))):
                        #     # image_name = timg.split('/')[-1]
                        #     if x == 0:
                        #         down_img = requests.get(timg, headers=self.headers, proxies=self.proxy)
                        #         with open(
                        #                 self.path + '\\%s\\%s\\' % (key, times_file) + link_url.split('/')[-1] + '.jpg',
                        #                 'wb') as f:
                        #             f.write(down_img.content)
                        #     else:
                        #         down_img = requests.get(timg, headers=self.headers, proxies=self.proxy)
                        #         with open(self.path + '\\%s\\%s\\' % (key, times_file) + link_url.split('/')[
                        #             -1] + '_' + str(int(x) + 1) + '.jpg', 'wb') as f:
                        #             f.write(down_img.content)
                        try:
                            cont = int(retweet) * 0.3 + int(comments) * 0.4 + int(like) * 0.4
                        except Exception:
                            cont = 0

                        data = [(SOURCE, link_url.replace('https://twitter.com', ''), link_url.split('/')[-1],
                                 timestamp,
                                 content.replace("'", "’"), str(picture), int(retweet), int(comments), int(like),
                                 cont,
                                 parent_url)]
                        # print(data)
                        self.insert_comment(data)

                    except Exception as e:
                        pass
                        # print('错误',e)

                self.driver.execute_script("window.scrollTo(0, %s);" % comments_max)
                time.sleep(2)
                comments_Text_height1 = self.driver.execute_script("var q=document.documentElement.scrollTop;return(q)")
                # print(Text_height0,Text_height1)
                if comments_Text_height0 == comments_Text_height1:
                    # print('到达底线')
                    self.driver.close()
                    self.driver.switch_to.window(handles[1])
                    comments_break = False
                comments_max += 1500
                time.sleep(3)
        except Exception:
            self.driver.close()
            self.driver.switch_to.window(handles[1])

    # 清除浏览器缓存
    def clear_cookies(self):
        self.driver.execute_script("window.open('chrome://settings/clearBrowserData')")
        time.sleep(1)
        handles = self.driver.window_handles
        self.driver.switch_to.window(handles[3])

    """数据库写入"""
    # 主页信息写入数据库
    def insert_server(self, data):
        try:
            # 获取锁
            self.share_lock.acquire()
            self.email_list.append(data[0][1])
            # print(self.email_list)
            insert_sql = "insert into TWITTER(SOURCE,URL,twitter_id,createtime,content,picture,shares,comments,likes,cont) VALUES(?,?,?,?,?,?,?,?,?,?)"
            self.cursor.executemany(insert_sql, data)
            self.conn.commit()
        except Exception as e:
            logger.error('主推写入数据库出错', exc_info=True)

        finally:
            # 释放锁
            self.share_lock.release()

    # 评论写入数据库
    @robust
    def insert_comment(self, data):
        try:
            # 获取锁
            self.share_lock.acquire()
            insert_sql = "insert into TWITTER_COMMENTS(SOURCE,URL,twitter_id,createtime,content,picture,shares,comments,likes,cont,link_url) VALUES(?,?,?,?,?,?,?,?,?,?,?)"
            self.comment_cursor.executemany(insert_sql, data)
            self.comment_conn.commit()
        except Exception as e:
            logger.error('评论写入数据库出错', exc_info=True)

        finally:
            # 释放锁
            self.share_lock.release()

    # 已抓取url的share,comment,likes,cont更新
    @robust
    def update_index(self,update_data):
        # print('更新数据',update_data[4].split('/')[-1])
        self.email_update_list.append(update_data[4])
        self.Q.put('{}:更新数据:{}'.format(time.strftime('%Y-%m-%d %H:%M:%S'),update_data[4].split('/')[1]))
        update_sql = "update TWITTER set shares=%s,comments=%s,likes=%s,cont=%s where URL='%s'" % (update_data[0],update_data[1],update_data[2],update_data[3],update_data[4])
        self.cursor.execute(update_sql)
        self.conn.commit()

    # 创建下级图片库
    @robust
    def image_path(self, key):
        if not os.path.exists(self.path + '/%s' % key):
            os.makedirs(self.path + '/%s' % key)

    # email
    @robust
    def send_mail(self, start_time):
        # 第三方 SMTP 服务
        mail_host = "smtp.126.com"  # 设置服务器
        mail_user = "q867940410@126.com"  # 用户名
        mail_pass = "q867940410"  # 口令

        # 发件人
        sender = 'q867940410@126.com'
        receivers = ['867940410@qq.com']  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱

        content = '下载数量为：' + str(len(self.email_list)) + '\n' + '更新数量为：' + str(len(self.email_update_list)) + '\n' + '用时:' + str(time.time() - start_time) + '\n'
        # content = '完成一轮抓取\n' + '用时:' + str(time.time() - start_time) + '\n'
        for i, j in enumerate(self.email_list):
            content += str(i) + ':  ' + j + '\n'

        # 邮件内容
        message = MIMEText(content, 'plain', 'utf-8')
        # 括号里的对应发件人邮箱昵称、发件人邮箱账号
        message['From'] = formataddr(['深圳利深', sender])
        message['To'] = '867940410@qq.com'

        # 邮件主题
        subject = '刘飞，Twitter下载数据，请查收。'
        message['Subject'] = Header(subject, 'utf-8')

        try:
            smtpObj = smtplib.SMTP()
            smtpObj.connect(mail_host, 25)  # 25 为 SMTP 端口号
            smtpObj.login(mail_user, mail_pass)
            smtpObj.sendmail(sender, receivers, message.as_string())
            smtpObj.quit()
            # print("ok")
        except smtplib.SMTPException:
            logger.error('email_false', exc_info=True)

    # 启动函数
    # @robust不可用
    def main(self, q):
        self.conn = pyodbc.connect(r'DRIVER={SQL Server};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s' % (self.config['host'], self.config['databases'], self.config['user'], self.config['password']))
        self.cursor = self.conn.cursor()
        self.comment_conn = pyodbc.connect(r'DRIVER={SQL Server Native Client 11.0};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s' % (self.config['comment_host'], self.config['comment_databases'], self.config['comment_user'], self.config['comment_password']))
        self.comment_cursor = self.comment_conn.cursor()

        time.sleep(random.randint(2, 10))
        # 浏览器初始化参数
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--proxy-server=http://%s" % self.config['proxies'])
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        # 禁用大量日志信息滚动输出
        # chrome_options.add_argument('log-level=3')
        # chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.binary_location = self.config['binary_location']
        executable_path = self.config['executable_path']

        self.driver = webdriver.Chrome(executable_path=executable_path, chrome_options=chrome_options)
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 35)
        # self.driver.get('https://www.baidu.com/')
        try:
            while True:
                try:
                    url = q.get_nowait()
                except Exception as e:
                    print(e)
                    break
                self.search_index_ = self.search_index(url)
                # 获取用户标识
                key = url[1].split('/')[-1]
                # 创建下一级图片库
                self.image_path(key=key)
                # 爬虫方法
                self.get_index(url, key)
                # i = os.system('cls')
                # print('抓取完成', url[0])
                self.Q.put('{}:抓取完成:{}'.format(time.strftime('%Y-%m-%d %H:%M:%S'),url[0]))
        except Exception as e:
            logger.error('启动函数', exc_info=True)

        self.driver.quit()
        self.cursor.close()
        self.conn.close()
        self.comment_cursor.close()
        self.comment_conn.close()

    # 运行函数
    @robust
    def run(self):
        self.email_list = multiprocessing.Manager().list()
        self.email_update_list = multiprocessing.Manager().list()
        self.share_lock = multiprocessing.Manager().Lock()
        url_list = self.search_url()
        # url_list = [['特朗普','https://twitter.com/realDonaldTrump']]
        self.q = multiprocessing.Queue()
        for url in url_list:
            self.q.put(url)

        # pool = Pool(maxtasksperchild=1)
        # pool.map(self.main, url_list, chunksize=1)
        # pool.close()

        tmp_process = multiprocessing.Process(target=self.main, args=(self.q,))
        tmp_process.daemon = True
        tmp_process.start()
        tmp_process1 = multiprocessing.Process(target=self.main, args=(self.q,))
        tmp_process1.daemon = True
        tmp_process1.start()
        tmp_process2 = multiprocessing.Process(target=self.main, args=(self.q,))
        tmp_process2.daemon = True
        tmp_process2.start()
        tmp_process3 = multiprocessing.Process(target=self.main, args=(self.q,))
        tmp_process3.daemon = True
        tmp_process3.start()

        tmp_process.join()
        tmp_process1.join()
        tmp_process2.join()
        tmp_process3.join()

# 界面
class Demo(QWidget):

    def __init__(self):
        super(Demo, self).__init__()
        self.setWindowTitle('Twitter')
        self.setWindowIcon(QIcon(res_path('res/twitter.ico')))
        self.resize(700,400)


        self.log_browser = QTextBrowser(self)            # 日志输出框
        self.log_browser.document().setMaximumBlockCount(50)
        self.crawl_btn = QPushButton('Python爬虫', self)    # 开始爬取按钮

        # 布局
        self.h_layout = QHBoxLayout()
        self.v_layout = QVBoxLayout()
        self.v_layout.addWidget(QLabel('日志输出框'))
        self.v_layout.addWidget(self.log_browser)
        self.v_layout.addWidget(self.crawl_btn)
        self.setLayout(self.v_layout)
        self.Q = Manager().Queue()
        self.log_thread = LogThread(self)
        self.crawl_slot()

    def crawl_slot(self):
        self.p = Process(target=crawl, args=(self.Q,))
        self.p.start()
        self.log_thread.start()

    def closeEvent(self, event):
        os.system('taskkill /im chromedriver.exe /F')
        os.system('taskkill /im chrome.exe /F')
        os.system('taskkill /im Twitter.exe /F')
        time.sleep(1.5)
        self.p.terminate()
        self.log_thread.terminate()


# 界面输出
class LogThread(QThread):
    def __init__(self, gui):
        super(LogThread, self).__init__()
        self.gui = gui

    def run(self):
        while True:
            if not self.gui.Q.empty():
                self.gui.log_browser.append(self.gui.Q.get())

                # 确保滑动条到底
                cursor = self.gui.log_browser.textCursor()
                pos = len(self.gui.log_browser.toPlainText())
                cursor.setPosition(pos)
                self.gui.log_browser.setTextCursor(cursor)
                if '爬取结束***' in self.gui.log_browser.toPlainText():
                    os.system('taskkill /im chromedriver.exe /F')
                    os.system('taskkill /im chrome.exe /F')
                    os.system('taskkill /im Twitter.exe /F')
                    QCoreApplication.quit()
                    break
                # 睡眠10毫秒，否则太快会导致闪退或者显示乱码
                self.msleep(10)
            else:
                # 如果程序超过半小时无有效输出，推出程序，等待计算机定时任务再次开启
                res = self.gui.log_browser.toPlainText()
                res = re.findall('\n(.*?):抓取完成:', res)
                if res:
                    timeArray = time.strptime(res[-1], "%Y-%m-%d %H:%M:%S")
                    # 转换为时间戳
                    timeStamp = int(time.mktime(timeArray))
                    if time.time() - timeStamp > 1800:
                        with open('error.log', 'a+', encoding='utf-8') as f:
                            f.write('{}:程序超时退出'.format(time.strftime('%Y-%m-%d %H:%M:%S')) + '\n')
                        os.system('taskkill /im chromedriver.exe /F')
                        os.system('taskkill /im chrome.exe /F')
                        os.system('taskkill /im Twitter.exe /F')
                        time.sleep(1.5)
                        self.gui.p.terminate()
                        # self.gui.log_thread.terminate()
                        QCoreApplication.quit()
                    else:
                        pass
                self.msleep(10)

# 获取资源绝对路径
def res_path(relative_path):
    """获取资源绝对路径"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# 启动爬虫
def crawl(Q):
    # CrawlerProcess
    # while True:
    Q.put('启动中==>>>>>>')
    start_time = time.time()
    S = Twitter(Q)
    S.run()
    S.send_mail(start_time)
    Q.put('等待下轮抓取..')
    with open('time.txt', 'a+', encoding='utf-8') as f:
        f.write(str(time.time()-start_time) + '\n')
    # time.sleep(300)
    for j in range(3):
        i = 3
        i -= j
        Q.put(str(i))
        time.sleep(1)
    Q.put('爬取结束***')


if __name__ == '__main__':
    # 多进程打包exe需要加此方法
    freeze_support()
    app = QApplication(sys.argv)
    demo = Demo()
    demo.show()
    sys.exit(app.exec_())


# 请求频率过快，限制浏览内容
# //div[starts-with(@class,"css-18t94o4 css-1dbjc4n r-urgr8i r-42olwf")]

# 图片处理库
from PIL import Image

# 浏览器驱动库
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException

import re, os,sys
import time
import pyodbc
# 邮件发送相关库
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
# 界面
from PyQt5.QtCore import QThread,QCoreApplication
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton,QTextBrowser, QHBoxLayout, QVBoxLayout
from multiprocessing import Process, Manager
import multiprocessing
from PyQt5.QtGui import QIcon

# 捕获异常装饰器
def robust(actual_do):
    def add_robust(*args, **keyargs):
        try:
            return actual_do(*args, **keyargs)
        # 如果遇到浏览器崩溃等情况，重新启动爬虫程序
        # except WebDriverException as e:
        #     with open('error.txt','a+',encoding='utf-8') as f:
        #         f.write('Error execute: %s' % actual_do.__name__ + 'Error execute: %s' % e + '\n')
        #     F = FaceBook()
        #     F.run()
        except Exception as e:
            # print('Error execute: %s' % actual_do.__name__)
            # print('Error execute: %s' % e)
            with open('error.txt', 'a+', encoding='utf-8') as f:
                f.write('Error execute: %s' % actual_do.__name__ + 'Error execute: %s' % e + '\n')
            # traceback.print_exc()

    return add_robust

# 爬虫
class FaceBook:
    instant = None

    # 使用单例模式，多次调用继续使用第一次调用的地址
    def __new__(cls, *args, **kwargs):
        if cls.instant is None:
            cls.instant = super().__new__(cls)
        return cls.instant

    # 初始化
    @robust
    def __init__(self,Q):
        self.Q=Q
        self.config = self.get_config()
        self.list_mail = []
        self.path = self.config['path']
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        # 连接数据库
        self.conn = pyodbc.connect(r'DRIVER={SQL Server};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s' % (
            self.config['host'], self.config['databases'], self.config['user'], self.config['password']))
        self.cursor = self.conn.cursor()

        # 初始化浏览器
        chrome_options = Options()
        # 隐藏窗口
        # chrome_options.add_argument('--headless')
        # 禁用浏览器弹窗
        prefs = {
            'profile.default_content_setting_values': {
                'notifications': 2
            }
        }
        chrome_options.add_experimental_option('prefs', prefs)
        # 代理
        chrome_options.add_argument("--proxy-server=http://%s" % self.config['proxies'])
        # 规避bug
        chrome_options.add_argument('--disable-gpu')
        # 禁止打印日志
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        # 设为开发者模式
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        # 禁用大量日志信息滚动输出
        chrome_options.add_argument('log-level=3')
        # chromium
        chrome_options.binary_location = self.config['binary_location']
        # chromedriver
        executable_path = self.config['executable_path']

        self.driver = webdriver.Chrome(executable_path=executable_path, chrome_options=chrome_options)
        self.driver.maximize_window()
        # self.driver.set_window_size(700,1000)
        self.wait = WebDriverWait(self.driver, 60)
        # print('启动中...')
        self.login()

    # 获取配置文件信息
    @robust
    def get_config(self):
        with open('config.txt', 'r', encoding='utf-8') as f:
            data = f.read()
        return eval(data)

    # 从数据库中获取所需url
    @robust
    def get_url(self):
        # search_sql = "select profile_url,profile_type from t_fb_profile_src"
        # search_sql = "select top 6 profile_url,profile_type,tag from t_fb_profile_src where profile_type='page'"
        search_sql = "select top 100 profile_url,profile_type,tag from t_fb_profile_src"
        self.cursor.execute(search_sql)
        page_url = []
        for i in self.cursor.fetchall():
            if i[0]:
                page_url.append([i[0], i[1], i[2]])
        return page_url

    # 模拟登录
    @robust
    def login(self):
        self.driver.get('https://www.facebook.com/')
        self.Q.put('{}:模拟登录:https://www.facebook.com/'.format(time.strftime('%Y-%m-%d %H:%M:%S')))
        UserName = self.wait.until(lambda driver: driver.find_element_by_xpath('//*[@id="email"]'))
        UserName.send_keys(self.config['username'])
        time.sleep(1)
        PassWord = self.driver.find_element_by_xpath('//*[@id="pass"]')
        PassWord.send_keys(self.config['password_fb'])
        time.sleep(1)
        self.driver.find_element_by_xpath('//*[@id="loginbutton"]/input').click()

    # 爬取page用户信息
    @robust
    def get_page(self, page_url):
        # print('正在抓取：', page_url)
        self.Q.put('{}:page用户信息爬取:{}'.format(time.strftime('%Y-%m-%d %H:%M:%S'),page_url))
        time.sleep(0.5)
        self.driver.execute_script("window.open('%s')" % page_url)
        time.sleep(0.5)
        handles = self.driver.window_handles
        # print(handles)
        self.driver.switch_to.window(handles[1])
        try:
            like_follower = self.wait.until(lambda driver: driver.find_elements_by_xpath(
                '//div[@class="_4-u2 _6590 _3xaf _4-u8"]/div[@class="_2pi9 _2pi2"]'))
            # 获取t_fb_pages表中的数据
            fbid_y = self.driver.find_element_by_xpath(
                '//*[@id="facebook"]/head/meta[@property="al:android:url"]').get_attribute('content')
            # fb://page/1085139268244384?referrer=app_link
            fbid = fbid_y.split('?')[0].split('//')[1].split('/')[1]
            page_token = page_url.split('/')[-2]
            name = self.driver.find_element_by_xpath('//*[@id="seo_h1_tag"]/a/span').get_attribute('textContent')

            # like_follower = self.driver.find_elements_by_xpath('//div[@class="_4-u2 _6590 _3xaf _4-u8"]/div[@class="_2pi9 _2pi2"]')
            like_counts = like_follower[0].find_element_by_xpath('.//div[@class="_4bl9"]/div').get_attribute(
                'textContent')
            follower_counts = like_follower[1].find_element_by_xpath('.//div[@class="_4bl9"]/div').get_attribute(
                'textContent')
            like_count = ''.join(re.findall('\d+', like_counts))
            follower_count = ''.join(re.findall('\d+', follower_counts))
            talking_about_count = 0
            picture_url = self.driver.find_element_by_xpath('//*[@id="u_0_u"]/div/div/div/a/div/img').get_attribute(
                'src')
            read_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

            page_data = [(fbid, page_token, name, like_count, follower_count, talking_about_count, picture_url)]
            # self.insert_pages(page_data)
            page_data_states = [(fbid, read_time, like_count, follower_count, talking_about_count)]
            self.insert_page_states(page_data_states)
            # print('主页信息',page_data)

            # 爬取t_fb_posts表中的数据
            self.get_posts(fbid, page_url)
            # i = os.system("cls")
            # print('抓取完成',name)

        except Exception as e:
            # print(e)
            pass

        # time.sleep(2)
        self.driver.close()
        time.sleep(0.5)
        self.driver.switch_to.window(handles[0])

    # ********************帖子主页的公用部分提取开始

    # 获取react_all值
    @robust
    def get_react_all(self,div_list):
        try:
            react_alls = div_list.find_element_by_xpath('.//span[@class="_81hb"]').get_attribute(
                'textContent')
            react_all = react_alls.replace(',', '')

            if '萬' in react_alls:
                react_alls = react_alls.replace(u'\xa0', '')
                if '.' in react_alls:
                    react_all = ''.join(re.findall('\d', react_alls)) + '000'
                else:
                    react_all = re.findall('\d', react_alls)[0] + '0000'
            return react_all
        except Exception as e:
            return '0'

    # 增量时获取react_like的值
    @robust
    def get_react_like(self,div_list):
        react = 0
        react_like_d = '0'
        try:
            react = div_list.find_element_by_xpath('.//span[@class="_81hb"]')
            self.driver.execute_script("arguments[0].click();", react)

            time.sleep(3)
        except Exception as e:
            pass

        if react:
            span_lists = self.wait.until(lambda driver: driver.find_elements_by_xpath(
                '//span[@class="_21af _9zc _2p7a"]'))
            for span_list in span_lists:
                desc = span_list.find_element_by_xpath('..').get_attribute('aria-label')
                if '讚好' in desc:
                    react_like_d = span_list.find_element_by_xpath('..').get_attribute(
                        'textContent').replace(',', '')
                    if '萬' in react_like_d:
                        react_like_d = react_like_d.replace(u'\xa0', '')
                        if '.' in react_like_d:
                            react_like_d = ''.join(re.findall('\d', react_like_d)) + '000'
                        else:
                            react_like_d = re.findall('\d', react_like_d)[0] + '0000'
        try:
            self.driver.find_element_by_xpath(
                './/a[@class="_42ft _5upp _50zy layerCancel _1f6 _51-t _50-0 _50z-"]').click()
            # print('点击关闭按钮')
        except Exception as e:
            ActionChains(self.driver).move_by_offset(1, 1).click().perform()
        return react_like_d

    # 获取转发，评论值
    @robust
    def get_share_comment(self,div_list):
        share_commentdict = {'share_count':'0','comment_count':'0'}
        try:
            share_comment = div_list.find_elements_by_xpath('.//div[@class="_4vn1"]/span')
        except Exception as e:
            return share_commentdict
        if share_comment:
            for sh_con in share_comment:
                try:
                    share_countss = sh_con.find_element_by_xpath('./a[@class="_3rwx _42ft"]').get_attribute(
                        'textContent')
                    share_counts = ''.join(re.findall('\d+', share_countss))
                    if '萬' in share_countss:
                        share_countss = share_countss.replace(u'\xa0', '')
                        if '.' in share_countss:
                            share_counts = ''.join(re.findall('\d', share_countss)) + '000'
                        else:
                            share_counts = re.findall('\d', share_countss)[0] + '0000'
                    share_commentdict['share_count'] = share_counts
                except Exception as e:
                    # print(e)
                    pass
                try:
                    comment_countss = sh_con.find_element_by_xpath(
                        './a[@class="_3hg- _42ft"]').get_attribute('textContent')
                    comment_total_count = ''.join(re.findall('\d+', comment_countss))
                    if '萬' in comment_countss:
                        comment_countss = comment_countss.replace(u'\xa0', '')
                        if '.' in comment_countss:
                            comment_total_count = ''.join(re.findall('\d', comment_countss)) + '000'
                        else:
                            comment_total_count = re.findall('\d', comment_countss)[0] + '0000'
                    share_commentdict['comment_count'] = comment_total_count
                except Exception as e:
                    # print(e)
                    pass
        return share_commentdict

    # 获取各react态度数量
    @robust
    def get_react_detail(self,div_list):
        # 点击打开react详情，获取各态度详情
        react = 0
        react_detail = {}
        try:
            react = div_list.find_element_by_xpath('.//span[@class="_81hb"]')
            self.driver.execute_script("arguments[0].click();", react)

            time.sleep(3)
        except Exception as e:
            pass
        if react:
            span_lists = self.wait.until(
                lambda driver: driver.find_elements_by_xpath('//span[@class="_21af _9zc _2p7a"]'))
            for span_list in span_lists:
                desc = span_list.find_element_by_xpath('..').get_attribute('aria-label')
                if '讚好' in desc:
                    react_like = span_list.find_element_by_xpath('..').get_attribute('textContent').replace(
                        ',', '')
                    if '萬' in react_like:
                        react_like = react_like.replace(u'\xa0', '')
                        if '.' in react_like:
                            react_like = ''.join(re.findall('\d', react_like)) + '000'
                        else:
                            react_like = re.findall('\d', react_like)[0] + '0000'
                    react_detail['react_like'] = react_like
                elif '哈哈' in desc:
                    react_haha = span_list.find_element_by_xpath('..').get_attribute('textContent').replace(
                        ',', '')
                    if '萬' in react_haha:
                        react_haha = react_haha.replace(u'\xa0', '')
                        if '.' in react_haha:
                            react_haha = ''.join(re.findall('\d', react_haha)) + '000'
                        else:
                            react_haha = re.findall('\d', react_haha)[0] + '0000'
                    react_detail['react_haha'] = react_haha
                elif '嬲嬲' in desc:
                    react_angry = span_list.find_element_by_xpath('..').get_attribute(
                        'textContent').replace(',', '')
                    if '萬' in react_angry:
                        react_angry = react_angry.replace(u'\xa0', '')
                        if '.' in react_angry:
                            react_angry = ''.join(re.findall('\d', react_angry)) + '000'
                        else:
                            react_angry = re.findall('\d', react_angry)[0] + '0000'
                    react_detail['react_angry'] = react_angry
                elif '嘩' in desc:
                    react_wow = span_list.find_element_by_xpath('..').get_attribute('textContent').replace(
                        ',', '')
                    if '萬' in react_wow:
                        react_wow = react_wow.replace(u'\xa0', '')
                        if '.' in react_wow:
                            react_wow = ''.join(re.findall('\d', react_wow)) + '000'
                        else:
                            react_wow = re.findall('\d', react_wow)[0] + '0000'
                    react_detail['react_wow'] = react_wow
                elif '勁正' in desc:
                    react_love = span_list.find_element_by_xpath('..').get_attribute('textContent').replace(
                        ',', '')
                    if '萬' in react_love:
                        react_love = react_love.replace(u'\xa0', '')
                        if '.' in react_love:
                            react_love = ''.join(re.findall('\d', react_love)) + '000'
                        else:
                            react_love = re.findall('\d', react_love)[0] + '0000'
                    react_detail['react_love'] = react_love
                elif '慘慘' in desc:
                    react_sad = span_list.find_element_by_xpath('..').get_attribute('textContent').replace(
                        ',', '')
                    if '萬' in react_sad:
                        react_sad = react_sad.replace(u'\xa0', '')
                        if '.' in react_sad:
                            react_sad = ''.join(re.findall('\d', react_sad)) + '000'
                        else:
                            react_sad = re.findall('\d', react_sad)[0] + '0000'
                    react_detail['react_sad'] = react_sad
        # print(react_like,react_angry)
        return react_detail

    # ********************帖子主页的公用部分提取结束

    # 爬取page帖子内容
    @robust
    def get_posts(self, from_profile_id, page_url):
        self.Q.put('{}:page帖子内容爬取:{}'.format(time.strftime('%Y-%m-%d %H:%M:%S'), page_url))
        is_break = True
        old_fbids = self.search_posts(from_profile_id)
        download_fbids = set()
        # 点击帖子
        post = self.driver.find_element_by_xpath(
            '//div[@class="_2fvv"]/div[@data-key="tab_posts"]/a/span[@class="_2yav"]')
        self.driver.execute_script("arguments[0].click();", post)
        time.sleep(3)
        # ActionChains(self.driver).move_by_offset(1, 1).click().perform()
        while is_break:
            Text_height0 = self.driver.execute_script("var q=document.documentElement.scrollTop;return(q)")

            div_lists = self.wait.until(
                lambda driver: driver.find_elements_by_xpath('//div[@class="_1xnd"]//div[@class="_4-u2 _4-u8"]'))
            div_lists = div_lists[-10:]
            for div_list in div_lists:
                try:
                    fbid_y = div_list.find_element_by_xpath('.//span[@class="fsm fwn fcg"]/a').get_attribute('href')
                    # //div[@class="_5pcp _5lel _2jyu _232_"]
                    fbid = fbid_y.split('?')[0].split('/')[-2]
                    bb = re.search('\d+', fbid)
                    if not bb:
                        fbid = fbid_y.split('?')[0].split('/')[-1]

                    permalink_url = page_url + 'posts/' + fbid

                    # 内存中去重
                    if fbid in download_fbids:
                        # print('旧的数据')
                        continue
                    download_fbids.add(fbid)

                    data_utime = div_list.find_element_by_xpath('.//span[@class="fsm fwn fcg"]/a/abbr').get_attribute(
                        'data-utime')
                    tooltip = None
                    try:
                        tooltip = div_list.find_element_by_xpath('.//i[@data-hover="tooltip"]')
                    except Exception as e:
                        pass

                    if not tooltip and time.time() - int(data_utime) > 86400:
                        # print('超过一天')
                        is_break = False
                        break

                    # 态度数
                    react_all = self.get_react_all(div_list)
                    # 转发和评论数量
                    share_comment = self.get_share_comment(div_list)
                    share_counts = share_comment.setdefault('share_count','0')
                    comment_total_count = share_comment.setdefault('comment_count','0')

                    if fbid in old_fbids:
                        # print('数据库内已存在')
                        if int(comment_total_count) > 0:
                            old_comment_total_count = self.search_comment_total_count(fbid)
                            cha = int(old_comment_total_count) / int(comment_total_count)
                            # 如果相差大于百分之十，进行评论增量爬取
                            if cha < 0.9:
                                # print('评论增量爬取')
                                self.Q.put('{}:评论增量:{}'.format(time.strftime('%Y-%m-%d %H:%M:%S'), fbid))
                                # 获取react_like
                                react_like_d = self.get_react_like(div_list)

                                comment_counts_d = self.get_post_comment(post_detail_url=permalink_url, post_id=fbid)
                                if comment_counts_d != 0:
                                    interaction = int(comment_counts_d) * 0.4 + int(share_counts) * 0.4 + int(react_like_d.strip()) * 0.2
                                    update_data = [comment_counts_d, comment_total_count, fbid, interaction,react_like_d,share_counts]
                                    self.update_comment(update_data)
                                    self.update_comment_prop(update_data)

                        continue

                    create_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(data_utime)))
                    update_time = create_time

                    content = ''
                    try:
                        contents = div_list.find_elements_by_xpath('.//div[@data-testid="post_message"]//p')
                        for con in contents:
                            content += con.get_attribute('textContent')
                    except Exception as e:
                        pass

                    types = ''
                    link = ''
                    # 判断帖子类别&图片提取scaledImageFitHeight img
                    try:
                        # 后面图片 //img[@class="scaledImageFitHeight img"]
                        pic = div_list.find_element_by_xpath(
                            './/img[@class="scaledImageFitWidth img"]|.//img[@class="scaledImageFitHeight img"]').get_attribute(
                            'src')
                        full_pic = pic
                        types = 'photo'
                        self.download_img(url=pic, from_profile_id=from_profile_id, fbid=fbid)
                        # pics = div_list.find_elements_by_xpath('.//img[@class="scaledImageFitHeight img"]')
                    except Exception as e:
                        pic = ''
                        full_pic = ''
                    try:
                        p = div_list.find_element_by_xpath('.//img[@class="_3chq"]').get_attribute('src')
                        if p:
                            full_pic = pic = p
                            types = 'video'
                        self.download_img(url=p, from_profile_id=from_profile_id, fbid=fbid)
                    except Exception as e:
                        pass
                    try:
                        link = div_list.find_element_by_xpath('.//div[@class="_6ks"]/a').get_attribute('href')

                        types = 'link'

                    except Exception as e:
                        pass

                    react_thankful = '0'
                    react_detial = self.get_react_detail(div_list)
                    react_like = react_detial.setdefault('react_like','0')
                    react_angry = react_detial.setdefault('react_angry','0')
                    react_haha = react_detial.setdefault('react_haha','0')
                    react_love = react_detial.setdefault('react_love','0')
                    react_sad = react_detial.setdefault('react_sad','0')
                    react_wow = react_detial.setdefault('react_wow','0')

                    local_update_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                    # 关闭react详情
                    try:
                        self.driver.find_element_by_xpath('.//a[@class="_42ft _5upp _50zy layerCancel _1f6 _51-t _50-0 _50z-"]').click()
                        # print('点击关闭按钮')
                    except Exception as e:
                        ActionChains(self.driver).move_by_offset(1, 1).click().perform()


                    # 获取评论内容
                    comment_counts = '0'
                    if int(comment_total_count) != 0:
                        self.Q.put('{}:评论内容爬取:{}'.format(time.strftime('%Y-%m-%d %H:%M:%S'), fbid))
                        comment_counts = self.get_post_comment(post_detail_url=permalink_url, post_id=fbid)

                    interaction = int(share_counts.strip()) * 0.4 + int(comment_counts) * 0.4 + int(react_like.strip()) * 0.2
                    # 写入数据库
                    posts_data = [(fbid, from_profile_id, create_time, update_time, content, permalink_url, types, link,
                                   pic, full_pic, int(share_counts.strip()), int(comment_counts),
                                   int(comment_total_count.strip()), int(react_all.strip()), int(react_like.strip()),
                                   int(react_angry.strip()), int(react_haha.strip()), int(react_love.strip()),
                                   int(react_sad.strip()), int(react_thankful.strip()), int(react_wow.strip()),
                                   int(interaction), local_update_time, 3)]
                    self.insert_posts(posts_data)
                    posts_prop_data = [(fbid, from_profile_id, create_time, update_time, int(share_counts.strip()),
                                        int(comment_counts),
                                        int(comment_total_count.strip()), int(react_all.strip()),
                                        int(react_like.strip()),
                                        int(react_angry.strip()), int(react_haha.strip()), int(react_love.strip()),
                                        int(react_sad.strip()), int(react_thankful.strip()), int(react_wow.strip()),
                                        int(interaction))]
                    self.insert_post_prop(posts_prop_data)


                except Exception as e:
                    # print(e)
                    with open('error.txt', 'a+', encoding='utf-8') as f:
                        f.write(
                            str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())) + 'Error execute: %s' % e + '\n')

            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0,999999);")
            time.sleep(9)
            Text_height1 = self.driver.execute_script("var q=document.documentElement.scrollTop;return(q)")

            # print(Text_height0,Text_height1)
            if Text_height0 == Text_height1:
                # print('到达底线')
                is_break = False

    # 爬取page帖子评论内容
    @robust
    def get_post_comment(self, post_detail_url, post_id):
        self.driver.execute_script("window.open('%s')" % post_detail_url)
        time.sleep(1)
        handles = self.driver.window_handles
        # print(handles)
        self.driver.switch_to.window(handles[2])
        comment_len = 0
        try:
            # 获取数据库已有评论
            old_comment_url = self.search_posts_comment(post_id)
            time.sleep(3)
            # 点击事件显示所有评论
            select_div = self.wait.until(
                lambda driver: driver.find_element_by_xpath('//div[@class="_4-u2 _4-u8"]//div[@class="_2plo _1ojy"]'))
            self.driver.execute_script('arguments[0].click()', select_div)
            time.sleep(1)
            click_li = self.wait.until(lambda driver: driver.find_elements_by_xpath('//ul[@class="_54nf"]/li'))
            self.driver.execute_script('arguments[0].click()', click_li[2])
            time.sleep(4)

            comment_liss = self.wait.until(
                lambda driver: driver.find_element_by_xpath('//div[@class="_1xnd"]/div[@class="_4-u2 _4-u8"]'))

            comment_break = True
            while comment_break:
                try:
                    # 展开更多评论
                    more_comments = comment_liss.find_elements_by_xpath('.//a[@class="_4sxc _42ft"]')
                    if more_comments:
                        for mor in more_comments:
                            self.driver.execute_script('arguments[0].click()', mor)
                            time.sleep(3)
                    else:
                        comment_break = False
                except Exception as e:
                    # print(e)
                    comment_break = False

            comment_lis = comment_liss.find_elements_by_xpath('.//ul[@class="_7791"]/li')
            comment_len += len(comment_lis)
            # print(comment_lis)
            for comment_li in comment_lis:
                hover = comment_li.find_element_by_xpath('.//a[@class=" _3mf5 _3mg0"]').get_attribute('data-hovercard')
                author_id = hover.split('=')[-1]
                comment_id = comment_li.find_element_by_xpath('.//a[@class="_6qw7"]').get_attribute('href')
                fbid = post_id + '_' + comment_id.split('=')[-1]
                if fbid in old_comment_url:
                    # print('数据库已存在此评论')
                    continue

                parent_id = ''
                message = ''
                try:
                    messages = comment_li.find_elements_by_xpath('.//span[@class="_3l3x"]/span')
                    for mes in messages:
                        message += mes.get_attribute('textContent')
                except Exception as e:
                    # print('无评论内容')
                    pass
                data_utime = comment_li.find_element_by_xpath('.//abbr[@class="livetimestamp"]').get_attribute(
                    'data-utime')
                created_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(data_utime)))
                updated_time = created_time
                recent_activity_time = created_time
                local_update_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                react_all = 0
                try:
                    react_alls = comment_li.find_element_by_xpath('./div//span[@class="_1lld"]').get_attribute(
                        'textContent')
                    react_all = int(react_alls)
                except Exception as e:
                    pass
                comment_count = 0

                try:
                    # 获取展开的更多评论内容
                    li_lists = comment_li.find_elements_by_xpath('.//div[@class="_2h2j"]/ul/li')
                    if li_lists:
                        comment_len += len(li_lists)
                        comment_count = len(li_lists)
                    parent_id_d = fbid
                    for li_list in li_lists:
                        hover_d = li_list.find_element_by_xpath('.//a[@class=" _3mf5 _3mg1"]').get_attribute(
                            'data-hovercard')
                        author_id_d = hover_d.split('=')[-1]
                        comment_id_d = li_list.find_element_by_xpath('.//a[@class="_6qw7"]').get_attribute('href')
                        fbid_d = post_id + '_' + comment_id_d.split('=')[-1]
                        if fbid_d in old_comment_url:
                            # print('数据库已存在此评论_d')
                            continue

                        message_d = ''
                        try:
                            messages_d = li_list.find_elements_by_xpath('.//span[@class="_3l3x"]/span')
                            for mes in messages_d:
                                message_d += mes.get_attribute('textContent')
                        except Exception as e:
                            # print('无评论内容_d')
                            pass
                        data_utime_d = li_list.find_element_by_xpath('.//abbr[@class="livetimestamp"]').get_attribute(
                            'data-utime')
                        created_time_d = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(data_utime_d)))
                        updated_time_d = created_time_d
                        recent_activity_time_d = created_time_d
                        local_update_time_d = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                        react_all_d = 0
                        try:
                            react_all_ds = li_list.find_element_by_xpath('./div//span[@class="_1lld"]').get_attribute(
                                'textContent')
                            react_all_d = int(react_all_ds)
                        except Exception as e:
                            pass
                        data_d = [(fbid_d, post_id, author_id_d, parent_id_d, message_d, 0, react_all_d, 0, 0, 0, 0, 0,
                                   0, 0, created_time_d, updated_time_d, recent_activity_time_d, local_update_time_d)]
                        self.insert_posts_comment(data_d)
                        # print('更多评论内容',data_d)
                except Exception as e:
                    pass

                data = [(fbid, post_id, author_id, parent_id, message, comment_count, react_all, 0, 0, 0, 0, 0, 0, 0,
                         created_time, updated_time, recent_activity_time, local_update_time)]
                self.insert_posts_comment(data)
                # print('评论内容',data)

        except Exception as e:
            # print(e)
            pass
        self.driver.close()
        self.driver.switch_to.window(handles[1])
        return comment_len

    # *******************************数据库操作相关开始
    # 帖子评论内容查询去重
    @robust
    def search_posts_comment(self, post_id):
        old_list = []
        search_sql = "SELECT fbid FROM t_fb_comments WHERE post_id='{}'".format(post_id)
        self.cursor.execute(search_sql)
        for i in self.cursor.fetchall():
            old_list.append(i[0])
        return old_list

    # 帖子评论信息写入数据库
    @robust
    def insert_posts_comment(self, data):
        # self.Q.put('{}:评论内容爬取:{}'.format(time.strftime('%Y-%m-%d %H:%M:%S'), data[0][0]))
        sql = "INSERT INTO t_fb_comments(fbid,post_id,author_id,parent_id,message,comment_count,react_all,react_like,react_angry,react_haha,react_love,react_sad,react_thankful,react_wow,created_time,updated_time,recent_activity_time,local_update_time) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        self.cursor.executemany(sql, data)
        self.conn.commit()

    # page主页信息写入数据库
    @robust
    def insert_page_states(self, data):
        sql = "INSERT INTO t_fb_page_states(page_id,read_time,like_count,follower_count,talking_about_count) VALUES (?, ?, ?, ?, ?)"
        self.cursor.executemany(sql, data)
        self.conn.commit()

    # pages信息写入数据库
    @robust
    def insert_pages(self, data):
        sql = "INSERT INTO t_fb_pages(fbid,page_token,[name],like_count,follower_count,talking_about_count,picture_url) VALUES (?, ?, ?, ?, ?, ?, ?)"
        self.cursor.executemany(sql, data)
        self.conn.commit()

    # 帖子内容查询去重
    @robust
    def search_posts(self, from_profile_id):
        old_list = []
        search_sql = "SELECT top 500 fbid FROM t_fb_posts WHERE from_profile_id='{}' ORDER BY created_time DESC".format(
            from_profile_id)
        self.cursor.execute(search_sql)
        for i in self.cursor.fetchall():
            old_list.append(i[0])
        return old_list

    # t_fb_posts表更新
    @robust
    def update_comment(self, update_data):
        # self.Q.put('{}:评论增量:{}'.format(time.strftime('%Y-%m-%d %H:%M:%S'), update_data[4]))
        # update_data = [comment_counts_d, comment_total_count, fbid, interaction,react_like_d,share_counts]
        local_update_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        update_sql = "update t_fb_posts set share_count=%s,comment_count=%s,comment_total_count=%s,interaction=%s,local_update_time='%s',react_like=%s where fbid='%s'" % (
            int(update_data[5]),int(update_data[0]), int(update_data[1]), int(update_data[3]), local_update_time, int(update_data[4]),
            update_data[2])
        self.cursor.execute(update_sql)
        self.conn.commit()

    # t_fb_post_props表更新
    @robust
    def update_comment_prop(self, update_data):
        update_sql = "update t_fb_post_props set share_count=%s,comment_count=%s,comment_total_count=%s,interaction=%s,react_like=%s where fbid='%s'" % (
            int(update_data[5]),int(update_data[0]), int(update_data[1]), int(update_data[3]), int(update_data[4]), update_data[2])
        self.cursor.execute(update_sql)
        self.conn.commit()

    # 已抓取帖子的评论数量查询
    @robust
    def search_comment_total_count(self, fbid):
        search_sql = "select comment_total_count from t_fb_posts where fbid='%s'" % fbid
        self.cursor.execute(search_sql)
        return self.cursor.fetchone()[0]

    # 帖子信息写入数据库
    @robust
    def insert_posts(self, data):
        # self.Q.put('{}:帖子内容爬取:{}'.format(time.strftime('%Y-%m-%d %H:%M:%S'), data[0][0]))
        insert_sql = "INSERT INTO t_fb_posts(fbid,from_profile_id,created_time,updated_time,message,permalink_url,[type],link,pic,full_pic,share_count,comment_count,comment_total_count,react_all,react_like,react_angry,react_haha,react_love,react_sad,react_thankful,react_wow,interaction,local_update_time,crawler_version) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        self.cursor.executemany(insert_sql, data)
        self.conn.commit()
        self.list_mail.append(data[0][5])

    # 帖子信息写入t_fb_post_props表
    def insert_post_prop(self, data):
        insert_sql = "INSERT INTO t_fb_post_props(fbid,from_profile_id,created_time,updated_time,share_count,comment_count,comment_total_count,react_all,react_like,react_angry,react_haha,react_love,react_sad,react_thankful,react_wow,interaction) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        self.cursor.executemany(insert_sql, data)
        self.conn.commit()

    # *******************************数据库操作相关结束

    # 帖子图片下载
    @robust
    def download_img(self, url, from_profile_id, fbid):
        self.Q.put('{}:图片下载:{}'.format(time.strftime('%Y-%m-%d %H:%M:%S'), from_profile_id + '_' + fbid))
        self.driver.execute_script("window.open('%s')" % url)
        time.sleep(1)
        handles = self.driver.window_handles
        # print(handles)
        self.driver.switch_to.window(handles[2])
        try:
            self.driver.save_screenshot('full_snap.png')
            page_snap_obj = Image.open('full_snap.png')

            img = self.driver.find_element_by_xpath('//img')
            time.sleep(1)
            location = img.location
            # print(location)
            size = img.size
            left = location['x']
            top = location['y']
            right = left + size['width']
            bottom = top + size['height']

            image_obj = page_snap_obj.crop((left, top, right, bottom))
            # image_obj.show()
            image_path = self.path + '\\' + from_profile_id + '_' + fbid + '_big.jpg'
            image_obj = image_obj.convert('RGB')
            image_obj.save(image_path)
            image_obj.thumbnail((130, 130))
            image_small_path = self.path + '\\' + from_profile_id + '_' + fbid + '_small.jpg'
            image_obj.save(image_small_path)
        except Exception as e:
            # print(e)
            pass
        time.sleep(0.5)
        self.driver.close()
        self.driver.switch_to.window(handles[1])

    # user个人主页帖子获取
    @robust
    def get_user(self, user_url):
        # print('正在抓取:', user_url)
        self.Q.put('{}:user帖子内容爬取:{}'.format(time.strftime('%Y-%m-%d %H:%M:%S'), user_url))
        time.sleep(1)
        self.driver.execute_script("window.open('%s')" % user_url)
        time.sleep(1)
        handles = self.driver.window_handles
        # print(handles)
        self.driver.switch_to.window(handles[1])
        is_user_break = True
        try:
            from_profile_id = self.driver.find_element_by_xpath('//div[@class="cover"]/a').get_attribute(
                'data-referrerid')
            old_fbids = self.search_posts(from_profile_id)
            download_fbids = set()
            while is_user_break:
                Text_height0 = self.driver.execute_script("var q=document.documentElement.scrollTop;return(q)")
                div_lists = self.wait.until(
                    lambda driver: driver.find_elements_by_xpath('//div[@class="_5pcb _4b0l _2q8l"]'))
                div_lists = div_lists[-10:]
                for div_list in div_lists:
                    try:
                        fbids = div_list.find_element_by_xpath('.').get_attribute('id')
                        fbid = fbids.split(':')[-1]

                        permalink_url = user_url + '/posts/' + fbid

                        if fbid in download_fbids:
                            # print('旧的数据')
                            continue
                        download_fbids.add(fbid)

                        data_utime = div_list.find_element_by_xpath('.//span[@class="fsm fwn fcg"]/a/abbr').get_attribute(
                            'data-utime')
                        tooltip = None
                        try:
                            tooltip = div_list.find_element_by_xpath('.//i[@data-hover="tooltip"]')
                        except Exception as e:
                            pass

                        if not tooltip and time.time() - int(data_utime) > 86400:
                            # print('超过一天')
                            is_user_break = False
                            break

                        create_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(data_utime)))
                        update_time = create_time

                        # 态度数
                        react_all = self.get_react_all(div_list)
                        # 转发和评论数量
                        share_comment = self.get_share_comment(div_list)
                        share_counts = share_comment.setdefault('share_count', '0')
                        comment_total_count = share_comment.setdefault('comment_count', '0')

                        # 判断评论是否增量
                        if fbid in old_fbids:
                            # print('数据库内已存在')
                            if int(comment_total_count) > 0:
                                old_comment_total_count = self.search_comment_total_count(fbid)
                                cha = int(old_comment_total_count) / int(comment_total_count)
                                # 如果相差大于百分之十，进行评论增量爬取
                                if cha < 0.9:
                                    # print('评论增量爬取')
                                    # 获取react_like
                                    react_like_d = self.get_react_like(div_list)

                                    comment_counts_d = self.get_user_comment(post_detail_url=permalink_url,post_id=fbid)
                                    if comment_counts_d != 0:
                                        interaction = int(share_counts) * 0.4 + int(
                                            comment_total_count) * 0.4 + int(
                                            react_like_d.strip()) * 0.2
                                        update_data = [comment_counts_d, comment_total_count, fbid, interaction,
                                                       react_like_d,share_counts]
                                        self.update_comment(update_data)
                                        self.update_comment_prop(update_data)

                            continue

                        content = ''
                        try:
                            contents = div_list.find_elements_by_xpath('.//div[@data-testid="post_message"]//p')
                            for con in contents:
                                content += con.get_attribute('textContent')
                        except Exception as e:
                            pass

                        types = ''
                        link = ''
                        # 判断帖子类别&图片提取scaledImageFitHeight img
                        try:
                            # 后面图片 //img[@class="scaledImageFitHeight img"]
                            pic = div_list.find_element_by_xpath(
                                './/img[@class="scaledImageFitWidth img"]|.//img[@class="scaledImageFitHeight img"]|.//img[@class="_46-i img"]').get_attribute(
                                'src')
                            full_pic = pic
                            types = 'photo'
                            self.download_img(url=pic, from_profile_id=from_profile_id, fbid=fbid)
                            # pics = div_list.find_elements_by_xpath('.//img[@class="scaledImageFitHeight img"]')
                        except Exception as e:
                            pic = ''
                            full_pic = ''
                        try:
                            p = div_list.find_element_by_xpath('.//img[@class="_3chq"]').get_attribute('src')
                            if p:
                                full_pic = pic = p
                                types = 'video'
                            self.download_img(url=p, from_profile_id=from_profile_id, fbid=fbid)
                        except Exception as e:
                            pass
                        try:
                            link = div_list.find_element_by_xpath('.//div[@class="_6ks"]/a').get_attribute('href')

                            types = 'link'

                        except Exception as e:
                            pass



                        react_thankful = '0'
                        react_detial = self.get_react_detail(div_list)
                        react_like = react_detial.setdefault('react_like', '0')
                        react_angry = react_detial.setdefault('react_angry', '0')
                        react_haha = react_detial.setdefault('react_haha', '0')
                        react_love = react_detial.setdefault('react_love', '0')
                        react_sad = react_detial.setdefault('react_sad', '0')
                        react_wow = react_detial.setdefault('react_wow', '0')

                        local_update_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                        try:
                            self.driver.find_element_by_xpath(
                                './/a[@class="_42ft _5upp _50zy layerCancel _1f6 _51-t _50-0 _50z-"]').click()
                            # print('点击关闭按钮')
                        except Exception as e:
                            ActionChains(self.driver).move_by_offset(1, 1).click().perform()

                        # 获取评论内容
                        comment_counts = '0'
                        if int(comment_total_count) != 0:
                            comment_counts = self.get_user_comment(post_detail_url=permalink_url, post_id=fbid)
                        interaction = int(share_counts.strip()) * 0.4 + int(comment_total_count) * 0.4 + int(
                            react_like.strip()) * 0.2

                        posts_data = [
                            (fbid, from_profile_id, create_time, update_time, content, permalink_url, types, link,
                             pic, full_pic, int(share_counts.strip()), int(comment_counts),
                             int(comment_total_count.strip()), int(react_all.strip()), int(react_like.strip()),
                             int(react_angry.strip()), int(react_haha.strip()), int(react_love.strip()),
                             int(react_sad.strip()), int(react_thankful.strip()), int(react_wow.strip()),
                             int(interaction), local_update_time, 3)]
                        self.insert_posts(posts_data)
                        posts_prop_data = [(fbid, from_profile_id, create_time, update_time, int(share_counts.strip()),
                                            int(comment_counts),
                                            int(comment_total_count.strip()), int(react_all.strip()),
                                            int(react_like.strip()),
                                            int(react_angry.strip()), int(react_haha.strip()), int(react_love.strip()),
                                            int(react_sad.strip()), int(react_thankful.strip()), int(react_wow.strip()),
                                            int(interaction))]
                        self.insert_post_prop(posts_prop_data)

                    except Exception as e:
                        # print(e)
                        with open('error.txt', 'a+', encoding='utf-8') as f:
                            f.write(str(
                                time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())) + 'Error execute: %s' % e + '\n')

                time.sleep(1)
                self.driver.execute_script("window.scrollTo(0,999999);")
                time.sleep(9)
                Text_height1 = self.driver.execute_script("var q=document.documentElement.scrollTop;return(q)")

                # print(Text_height0, Text_height1)
                if Text_height0 == Text_height1:
                    # print('到达底线')
                    is_user_break = False
        except Exception as e:
            # print(e)
            pass
        self.driver.close()
        time.sleep(1)
        # i = os.system("cls")
        self.driver.switch_to.window(handles[0])

    # 获取user&group主页评论
    @robust
    def get_user_comment(self, post_detail_url, post_id):
        self.Q.put('{}:评论内容爬取:{}'.format(time.strftime('%Y-%m-%d %H:%M:%S'), post_id))
        self.driver.execute_script("window.open('%s')" % post_detail_url)
        time.sleep(1)
        handles = self.driver.window_handles
        # print(handles)
        self.driver.switch_to.window(handles[2])
        comment_len = 0
        try:
            # 获取数据库已有评论
            old_comment_url = self.search_posts_comment(post_id)

            comment_lis = self.wait.until(
                lambda driver: driver.find_elements_by_xpath('//ul[@class="_7791"]/li'))

            comment_len += len(comment_lis)
            # print(comment_lis)
            for comment_li in comment_lis:
                hover = comment_li.find_element_by_xpath('.//a[@class=" _3mf5 _3mg0"]').get_attribute('data-hovercard')
                author_id = hover.split('=')[-1]
                comment_id = comment_li.find_element_by_xpath('.//a[@class="_6qw7"]').get_attribute('href')
                fbid = post_id + '_' + comment_id.split('=')[-1]
                if fbid in old_comment_url:
                    # print('数据库已存在此评论')
                    continue

                parent_id = ''
                message = ''
                try:
                    messages = comment_li.find_elements_by_xpath('.//span[@class="_3l3x"]/span')
                    for mes in messages:
                        message += mes.get_attribute('textContent')
                except Exception as e:
                    # print('无评论内容')
                    pass
                data_utime = comment_li.find_element_by_xpath('.//abbr[@class="livetimestamp"]').get_attribute(
                    'data-utime')
                created_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(data_utime)))
                updated_time = created_time
                recent_activity_time = created_time
                local_update_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                react_all = 0
                try:
                    react_alls = comment_li.find_element_by_xpath('./div//span[@class="_1lld"]').get_attribute(
                        'textContent')
                    react_all = int(react_alls)
                except Exception as e:
                    pass
                comment_count = 0

                data = [(fbid, post_id, author_id, parent_id, message, comment_count, react_all, 0, 0, 0, 0, 0, 0, 0,
                         created_time, updated_time, recent_activity_time, local_update_time)]
                self.insert_posts_comment(data)
                # print('评论内容', data)

        except Exception as e:
            # print(e)
            pass
        self.driver.close()
        self.driver.switch_to.window(handles[1])
        return comment_len

    # 获取group帖子内容
    @robust
    def get_group(self, group_url):
        # print('正在抓取:', group_url)
        self.Q.put('{}:group帖子内容爬取:{}'.format(time.strftime('%Y-%m-%d %H:%M:%S'), group_url))
        time.sleep(1)
        self.driver.execute_script("window.open('%s')" % group_url)
        time.sleep(1)
        handles = self.driver.window_handles
        # print(handles)
        self.driver.switch_to.window(handles[1])
        is_user_break = True
        try:
            from_profile_id = group_url.split('/')[-2]
            old_fbids = self.search_posts(from_profile_id)
            download_fbids = set()
            while is_user_break:
                Text_height0 = self.driver.execute_script("var q=document.documentElement.scrollTop;return(q)")
                div_lists = self.wait.until(
                    lambda driver: driver.find_elements_by_xpath('//div[@class="_5pcb"]/div[1]/div'))
                div_listss = self.wait.until(lambda driver: driver.find_elements_by_xpath(
                    '//div[@class="_4-u2 mbm _4mrt _5jmm _5pat _5v3q _7cqq _4-u8"]'))
                div_lists.extend(div_listss)
                # print(len(div_lists),div_lists)
                div_lists = div_lists[-20:]
                for div_list in div_lists:
                    try:
                        fbids = div_list.find_element_by_xpath('.').get_attribute('id')
                        fbid = fbids.split('_')[-1].split(':')[0]
                        permalink_url = group_url + 'permalink/' + fbid
                        if fbid in download_fbids:
                            # print('旧的数据')
                            continue
                        download_fbids.add(fbid)

                        data_utime = div_list.find_element_by_xpath('.//span[@class="fsm fwn fcg"]/a/abbr').get_attribute(
                            'data-utime')
                        tooltip = None
                        try:
                            tooltip = div_list.find_element_by_xpath('.//i[@data-hover="tooltip"]')
                        except Exception as e:
                            pass

                        if not tooltip and time.time() - int(data_utime) > 86400:
                            # print('超过一天')
                            is_user_break = False
                            break

                        # 态度数
                        react_all = self.get_react_all(div_list)
                        # 转发和评论数量
                        share_comment = self.get_share_comment(div_list)
                        share_counts = share_comment.setdefault('share_count', '0')
                        comment_total_count = share_comment.setdefault('comment_count', '0')

                        if fbid in old_fbids:
                            # print('数据库内已存在')
                            if int(comment_total_count) > 0:
                                old_comment_total_count = self.search_comment_total_count(fbid)
                                cha = int(old_comment_total_count) / int(comment_total_count)
                                # 如果相差大于百分之十，进行评论增量爬取
                                if cha < 0.9:
                                    # print('评论增量爬取')
                                    # 获取react_like
                                    react_like_d = self.get_react_like(div_list)


                                    comment_counts_d = self.get_user_comment(post_detail_url=permalink_url,
                                                                             post_id=fbid)
                                    if comment_counts_d != 0:
                                        interaction = int(share_counts) * 0.4 + int(
                                            comment_total_count) * 0.4 + int(
                                            react_like_d.strip()) * 0.2
                                        update_data = [comment_counts_d, comment_total_count, fbid, interaction,
                                                       react_like_d,share_counts]
                                        self.update_comment(update_data)
                                        self.update_comment_prop(update_data)

                            continue

                        create_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(data_utime)))
                        update_time = create_time

                        content = ''
                        try:
                            contents = div_list.find_elements_by_xpath('.//div[@data-testid="post_message"]//p')
                            for con in contents:
                                content += con.get_attribute('textContent')
                        except Exception as e:
                            pass

                        types = ''
                        link = ''
                        # 判断帖子类别&图片提取scaledImageFitHeight img
                        try:
                            # 后面图片 //img[@class="scaledImageFitHeight img"]
                            pic = div_list.find_element_by_xpath(
                                './/img[@class="scaledImageFitWidth img"]|.//img[@class="scaledImageFitHeight img"]|.//img[@class="_46-i img"]').get_attribute(
                                'src')
                            full_pic = pic
                            types = 'photo'
                            self.download_img(url=pic, from_profile_id=from_profile_id, fbid=fbid)
                            # pics = div_list.find_elements_by_xpath('.//img[@class="scaledImageFitHeight img"]')
                        except Exception as e:
                            pic = ''
                            full_pic = ''
                        try:
                            p = div_list.find_element_by_xpath('.//img[@class="_3chq"]').get_attribute('src')
                            if p:
                                full_pic = pic = p
                                types = 'video'
                            self.download_img(url=p, from_profile_id=from_profile_id, fbid=fbid)
                        except Exception as e:
                            pass
                        try:
                            link = div_list.find_element_by_xpath('.//div[@class="_6ks"]/a').get_attribute('href')

                            types = 'link'

                        except Exception as e:
                            pass

                        react_thankful = '0'
                        react_detial = self.get_react_detail(div_list)
                        react_like = react_detial.setdefault('react_like', '0')
                        react_angry = react_detial.setdefault('react_angry', '0')
                        react_haha = react_detial.setdefault('react_haha', '0')
                        react_love = react_detial.setdefault('react_love', '0')
                        react_sad = react_detial.setdefault('react_sad', '0')
                        react_wow = react_detial.setdefault('react_wow', '0')

                        local_update_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                        try:
                            self.driver.find_element_by_xpath(
                                './/a[@class="_42ft _5upp _50zy layerCancel _1f6 _51-t _50-0 _50z-"]').click()
                            # print('点击关闭按钮')
                        except Exception as e:
                            ActionChains(self.driver).move_by_offset(1, 1).click().perform()

                        # 获取评论内容
                        comment_counts = '0'
                        if int(comment_total_count) != 0:
                            comment_counts = self.get_user_comment(post_detail_url=permalink_url, post_id=fbid)
                        interaction = int(share_counts.strip()) * 0.4 + int(comment_counts) * 0.4 + int(
                            react_like.strip()) * 0.2

                        posts_data = [
                            (fbid, from_profile_id, create_time, update_time, content, permalink_url, types, link,
                             pic, full_pic, int(share_counts.strip()), int(comment_counts),
                             int(comment_total_count.strip()), int(react_all.strip()), int(react_like.strip()),
                             int(react_angry.strip()), int(react_haha.strip()), int(react_love.strip()),
                             int(react_sad.strip()), int(react_thankful.strip()), int(react_wow.strip()),
                             int(interaction), local_update_time, 3)]
                        self.insert_posts(posts_data)
                        posts_prop_data = [(fbid, from_profile_id, create_time, update_time, int(share_counts.strip()),
                                            int(comment_counts),
                                            int(comment_total_count.strip()), int(react_all.strip()),
                                            int(react_like.strip()),
                                            int(react_angry.strip()), int(react_haha.strip()), int(react_love.strip()),
                                            int(react_sad.strip()), int(react_thankful.strip()), int(react_wow.strip()),
                                            int(interaction))]
                        self.insert_post_prop(posts_prop_data)

                    except Exception as e:
                        # print(e)
                        with open('error.txt', 'a+', encoding='utf-8') as f:
                            f.write(str(
                                time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())) + 'Error execute: %s' % e + '\n')

                time.sleep(1)
                self.driver.execute_script("window.scrollTo(0,999999);")
                time.sleep(9)
                Text_height1 = self.driver.execute_script("var q=document.documentElement.scrollTop;return(q)")

                # print(Text_height0, Text_height1)
                if Text_height0 == Text_height1:
                    # print('到达底线')
                    is_user_break = False
        except Exception as e:
            # print(e)
            pass
        self.driver.close()
        time.sleep(1)
        # i = os.system("cls")
        self.driver.switch_to.window(handles[0])

    # email
    @robust
    def send_email(self):
        # 第三方 SMTP 服务
        mail_host = "smtp.126.com"  # 设置服务器
        mail_user = "q867940410@126.com"  # 用户名
        mail_pass = "q867940410"  # 口令

        # 发件人
        sender = 'q867940410@126.com'
        receivers = ['867940410@qq.com']  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱

        content = '下载数量为：' + str(len(self.list_mail)) + '\n' + '用时:' + str(time.time() - self.start_time) + '\n'
        for i, j in enumerate(self.list_mail):
            content += str(i) + ':  ' + j + '\n'

        # 邮件内容
        message = MIMEText(content, 'plain', 'utf-8')
        # 括号里的对应发件人邮箱昵称、发件人邮箱账号
        message['From'] = formataddr(['深圳利深', sender])
        message['To'] = '867940410@qq.com'

        # 邮件主题
        subject = '刘飞，Facebook下载数据，请查收。'
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

    # 主函数
    @robust
    def main(self, url):
        with open('get.txt', 'a+', encoding='utf-8') as f:
            f.write(str(url[0]) + '\n')
        if url[1] == 'page':
            self.get_page(url[0])
        elif url[1] == 'user':
            self.get_user(url[0])
        elif url[1] == 'group':
            self.get_group(url[0])

    # run方法
    @robust
    def run(self):
        # while True:

        self.start_time = time.time()
        # url_lists = self.get_url()
        # print(url_lists)
        url_lists = [
            # ['https://www.facebook.com/pg/headlinehk/','page'],
            ['https://www.facebook.com/pg/standnewshk/','page'],
            # ['https://www.facebook.com/pg/hk.nextmedia/', 'page'],
            ['https://www.facebook.com/victoryeung2019', 'user'],
            ['https://www.facebook.com/raymond.yukman', 'user'],
            ['https://www.facebook.com/sora.neverforget8964.org', 'user'],
            ['https://www.facebook.com/ayykj', 'user'],
            ['https://www.facebook.com/groups/1445500605709812/', 'group'],
            ['https://www.facebook.com/groups/1411363592456571/', 'group'],
            ['https://www.facebook.com/groups/242109779246677/', 'group'],
        ]
        for url in url_lists:
            self.main(url)
        self.send_email()
        with open('time.txt', 'a+', encoding='utf-8') as f:
            f.write(str(time.time() - self.start_time) + '\n')
        self.driver.quit()

    # # 析构方法
    # @robust
    # def __del__(self):
    #     self.driver.quit()


# 界面
class Demo(QWidget):
    def __init__(self):
        super(Demo, self).__init__()
        self.setWindowTitle('Facebook')
        self.setWindowIcon(QIcon(res_path('res/f.ico')))
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
        os.system('taskkill /im Facebook.exe /F')
        time.sleep(1.5)
        self.p.terminate()
        self.log_thread.terminate()


# 日志输出
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
                    QCoreApplication.quit()
                    break

                # 睡眠10毫秒，否则太快会导致闪退或者显示乱码
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
    # while True:
    Q.put('启动中==>>>>>>')
    start_time = time.time()
    S = FaceBook(Q)
    S.run()
    Q.put('等待下轮抓取..')
    with open('time.txt', 'a+', encoding='utf-8') as f:
        f.write(str(time.time()-start_time) + '\n')
    # time.sleep(600)
    for j in range(3):
        i = 3
        i -= j
        Q.put(str(i))
        time.sleep(1)
    Q.put('爬取结束***')


if __name__ == '__main__':
    # # for i in range(0, 2):
    # F = FaceBook()
    # F.run()
    # print('等待下轮抓取')
    # time.sleep(300)
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    demo = Demo()
    demo.show()
    sys.exit(app.exec_())

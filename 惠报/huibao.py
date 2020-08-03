
import requests
import pyodbc
from lxml import etree
import os
from langconv import *

conn = pyodbc.connect(r'DRIVER={SQL Server};SERVER=localhost;DATABASE=HKNEWS;UID=sa;PWD=root')
cursor = conn.cursor()

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'
}

proxy = {
    'http':'192.168.0.70'
}

def J(line):          #繁体转简体
    line=Converter("zh-hans").convert(line)
    return line

# 捕获异常装饰器
def robust(actual_do):
    def add_robust(*args, **keyargs):
        try:
            return actual_do(*args, **keyargs)
        except Exception as e:
            print('Error execute: %s' % actual_do.__name__)
            print('Error execute: %s' % e)
            with open('error.log','a+',encoding='utf-8') as f:
                f.write('Error execute: %s' % actual_do.__name__ + 'Error execute: %s' % e + '\n')
            #traceback.print_exc()
    return add_robust
@robust
def get_all(url):
    response = requests.get(url,headers=headers,proxies=proxy)
    result = etree.HTML(response.text)
    tbody_lists = result.xpath('//tbody[@class="alternate_bg"]')
    path = './pdf/LFHQYH/www_gld_gov_hk'
    if not os.path.exists(path):
        os.makedirs(path)
    for tbody_list in tbody_lists:
        tr_lists = tbody_list.xpath('./tr')
        for tr_list in tr_lists:
            try:
                url = 'https://www.gld.gov.hk/' + tr_list.xpath('./td[2]/a/@href')[0].lstrip('../../..')
                # https://www.gld.gov.hk/egazette/pdf/20192348/cgn201923487176.pdf
                title = tr_list.xpath('./td[2]/a/text()')[0]
                title = J(title)
                pdf_path = path + url.split('//')[1].replace('www.gld.gov.hk','').replace(url.split('/')[-1],'')
                urlforpublish = pdf_path.replace('./pdf','') + url.split('/')[-1]
                if not os.path.exists(pdf_path):
                    os.makedirs(pdf_path)
                source = '2019年10月31日区议会选举'
                publishtime = '2019-10-31'
                # print(url,title,urlforpublish)
                img_response = requests.get(url,headers=headers,proxies=proxy)
                with open('./pdf'+urlforpublish,'wb') as f:
                    f.write(img_response.content)
                print(url,urlforpublish,title,source,publishtime)
                data = [(url,urlforpublish,title,source,publishtime)]

                insert_sql = 'insert into HUIBAO(url,urlforpublish,title,source,publishtime) values(?,?,?,?,?)'
                cursor.executemany(insert_sql,data)
                conn.commit()
            except Exception as e:
                print(e,url)

url = 'https://www.gld.gov.hk/egazette/tc_chi/gazette/volume.php?year=2019&vol=23&no=47&extra=1&type=0'
get_all(url)
cursor.close()
conn.close()


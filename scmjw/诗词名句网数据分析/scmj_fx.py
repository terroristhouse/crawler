import numpy as np
import pandas as pd
from sqlalchemy import create_engine
import matplotlib as mpl
from matplotlib import pyplot as plt
import warnings


'''
明确分析目标
1.诗词分类前十及占比
2.写诗词数量最多的作者前十分类及占比
3.诗词数量最多的朝代及占比
4.有注释的诗词
5.有图片的诗词
'''

'''设置正常显示中文和‘-’号'''
# 设置正常显示中文
plt.rcParams['font.sans-serif'] = 'SimHei'
# 设置正常显示‘-’号
plt.rcParams['axes.unicode_minus'] = False
# 去除顶部轴
plt.rcParams['axes.spines.top'] = False
# 去除右部轴
plt.rcParams['axes.spines.right'] = False
# 屏蔽warning警告
warnings.filterwarnings("ignore")


class Scmj:
    def __init__(self):
        self.conn = create_engine("mysql+pymysql://root:root@127.0.0.1:3306/lf_01?charset=utf8mb4")
        self.df = pd.read_sql('select * from scmjw',self.conn)
        self.conn.dispose()
        # print(self.df.head())
        print(self.df.info())
        # print(self.df.describe())

    '''获取一些描述性信息'''
    def get_ty(self):
        # 数据总量
        self.scmj_all = self.df.shape[0]
        print('数据总量为:',self.scmj_all)

    '''诗词分类前十及占比'''
    def category_top10(self):
        category = self.df.groupby('category')
        category_top10 = category.count()['id'].sort_values(ascending=False)[:10]
        print('分类前十:\n',category_top10)
        # 折线图
        pic = plt.figure(figsize=(12,12),dpi=100)
        pic.add_subplot(2,2,1)
        plt.title('诗词分类前十折线图')
        plt.xlabel('诗词分类')
        plt.ylabel('数量')
        plt.xticks(rotation=90)
        plt.yticks([i for i in range(0,200,10)])
        plt.plot(category_top10)
        # 条形图
        pic.add_subplot(2,2,2)
        plt.title('诗词分类前十条形图')
        plt.xlabel('诗词分类')
        plt.ylabel('数量')
        x = range(10)
        plt.bar(x,height=category_top10.values,width=0.7)
        for i in range(len(category_top10)):
            # print(category_top10.values[i])
            plt.text(i,category_top10.values[i],'{}首'.format(category_top10.values[i]),va='bottom',ha='center')
        plt.xticks(x,category_top10.index,rotation=90)
        # 饼图
        pic.add_subplot(2,2,3)
        plt.title('诗词分类前十饼图')
        plt.pie(category_top10,autopct='%1.1f%%',labels=category_top10.index,explode=[0.01 for i in range(10)])
        # 箱线图
        pic.add_subplot(2,2,4)
        plt.title('诗词分类前十箱线图')
        plt.boxplot(category_top10)

        plt.savefig('./诗词分类前十统计图.png')
        plt.show()

    '''写诗词数量最多的作者前十及占比'''
    def auther_top10(self):
        auther_top10 = self.df['auther'].value_counts().iloc[:10]
        print('写诗词数量前十作者',auther_top10)
        fig = plt.figure(figsize=(12,12),dpi=100)
        # 折线图
        fig.add_subplot(2,2,1)
        plt.title('折线图')
        plt.xlabel('作者')
        plt.ylabel('写作数量')
        for i,j in zip(auther_top10.index,auther_top10.values):
            plt.text(i,j,j,ha='center', va='bottom',)
        plt.plot(auther_top10)
        # 条形图
        fig.add_subplot(2,2,2)
        x = range(len(auther_top10))
        plt.title('条形图')
        plt.xlabel('作者')
        plt.ylabel('写作数量')
        plt.xticks(x,auther_top10.index)
        plt.bar(x=x,height=auther_top10.values,width=0.7)
        for i in range(len(auther_top10)):
            plt.text(i,auther_top10.values[i],auther_top10.values[i],va='bottom',ha='center')
        # 饼图
        fig.add_subplot(2,2,3)
        plt.title('饼图')
        plt.pie(auther_top10.values,autopct='%1.1f%%',labels=auther_top10.index,explode=[0.01 for i in range(len(auther_top10))])
        # 散点图
        fig.add_subplot(2,2,4)
        plt.title('散点图')
        plt.xlabel('作者')
        plt.ylabel('写作数量')
        plt.scatter(x=auther_top10.index,y=auther_top10.values)
        plt.savefig('写诗词数量前十作者统计图.png')
        plt.show()

    '''诗词数量最多的朝代及占比'''
    def dynasty_top10(self):
        df1 = self.df
        df1[df1['dynasty'] == ' [] '] = None
        df1.dropna(subset=['dynasty'])
        dynasty = df1['dynasty'].value_counts()[:10]
        fig = plt.figure(dpi=100,figsize=(12,12))
        # 折线图
        fig.add_subplot(2, 2, 1)
        plt.title('折线图')
        plt.xlabel('朝代')
        plt.ylabel('写作数量')
        for i,j in zip(dynasty.index,dynasty.values):
            plt.text(i,j,j,ha='center',va='bottom')
        plt.plot(dynasty)
        # 条形图
        fig.add_subplot(2,2,2)
        plt.title('条形图')
        plt.xlabel('朝代')
        plt.ylabel('写作数量')
        plt.bar(x=dynasty.index,height=dynasty.values,width=0.8)
        for i,j in zip(dynasty.index,dynasty.values):
            plt.text(i,j,j,va='bottom',ha='center')
        # 饼图
        fig.add_subplot(2,2,3)
        plt.title('饼图')
        plt.pie(x=dynasty,autopct='%1.1f%%',labels=dynasty.index,explode=[0.01 for i in range(len(dynasty))])
        # 散点图
        fig.add_subplot(2,2,4)
        plt.title('散点图')
        plt.xlabel('朝代')
        plt.ylabel('写作数量')
        plt.scatter(x=dynasty.index,y=dynasty.values)
        for i,j in zip(dynasty.index,dynasty.values):
            plt.text(i,j,j,ha='center',va='center')
        plt.savefig('./诗词数量最多的朝代前十及占比.png')
        plt.show()

    '''有注释&图片的诗词'''
    def contents_images(self):
        df1 = self.df
        df1[df1['contents'] == ''] = None
        contents = df1.dropna(subset=['contents']).shape[0]
        print('有注释的诗词数量为:',contents)
        df2 = self.df
        df2[df2['beiyong1'] == ''] = None
        images = df2.dropna(subset=['beiyong1']).shape[0]
        print('有图片的诗词数量为:',images)
        '''饼图'''
        explode = [0.01,0.01]
        fig = plt.figure(figsize=(8,8),dpi=100)
        fig.add_subplot(1,2,1)
        plt.title('有注释的诗词占比')
        x = [self.scmj_all,contents]
        labels = ['无注释','有注释']
        plt.pie(x=x,autopct='%1.1f%%',labels=labels,explode=explode)
        fig.add_subplot(1,2,2)
        plt.title('有图片的诗词占比')
        x = [self.scmj_all,images]
        labels = ['无图片','有图片']
        plt.pie(x=x,autopct='%1.1f%%',labels=labels,explode=explode)
        plt.savefig('./图片&诗词占比.png')
        plt.show()


    def run(self):
        self.get_ty()
        self.category_top10()
        self.auther_top10()
        self.dynasty_top10()
        self.contents_images()

    def __del__(self):
        pass


if __name__ == '__main__':
    S = Scmj()
    S.run()


# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import scrapy
import os
# 导入scrapy 框架里的 管道文件的里的图像 图像处理的专用管道文件
from scrapy.pipelines.images import ImagesPipeline
# 导入图片路径名称
from images.settings import IMAGES_STORE as images_store

class Image_down(ImagesPipeline):
    def get_media_requests(self, item, info):
        yield scrapy.Request(url=item['image_url'])

    def item_completed(self, results, item, info):
        print(results)
        image_url = item['image_url']
        image_name = image_url.split('/')[-1]
        old_name_list = [x['path'] for t, x in results if t]
        # 真正的原图片的存储路径
        old_name = images_store + old_name_list[0]
        image_path = images_store + item['field_name'] + '/' + item['detail_name'] + '/'
        # 判断图片存放的目录是否存在
        if not os.path.exists(image_path):
            # 根据当前页码创建对应的目录
            os.makedirs(image_path)
        # 新名称
        new_name = image_path + image_name
        # 重命名
        os.rename(old_name, new_name)
        return item


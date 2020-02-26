from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

process = CrawlerProcess(get_project_settings())

# belle是爬虫名
process.crawl('myspd1')
process.crawl('myspd2')
process.crawl('myspd3')

process.start()















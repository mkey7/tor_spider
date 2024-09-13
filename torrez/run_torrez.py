# -*- coding:utf-8 -*-
from scrapy import cmdline
# quotes 对应的是爬虫名 在cmd运行 scrapy crawl quotes 同步


cmdline.execute("scrapy crawl torrez".split())

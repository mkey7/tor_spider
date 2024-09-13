# Scrapy settings for torrez project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import os
from pathlib import Path

BOT_NAME = "torrez"

SPIDER_MODULES = ["torrez.spiders"]
NEWSPIDER_MODULE = "torrez.spiders"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 16

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 2
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = True

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# 爬取时，0表示深度优先Lifo(默认)；1表示广度优先FiFo
DEPTH_PRIORITY = 0

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh,zh-CN;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
}

# Enable or disable spider dwMiddlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    "dwSpider.dwMiddlewares.DwspiderSpiderMiddleware": 543,
# }

# Enable or disable downloader dwMiddlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
    'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 400,  # 开启
    'scrapy_fake_useragent.middleware.RetryUserAgentMiddleware': 401,
    "torrez.dwMiddlewares._proxy.ProxyMiddleware": 450,
    "torrez.dwMiddlewares.login.ToRReZLoginMiddleware": 556,
    'torrez.dwMiddlewares._selenium_midd.SeleniumMiddleware': 800,
}

FAKEUSERAGENT_PROVIDERS = [
    'scrapy_fake_useragent.providers.FakeUserAgentProvider',  # this is the first provider we'll try
    'scrapy_fake_useragent.providers.FakerProvider',
    # if FakeUserAgentProvider fails, we'll use faker to generate a user-agent string for us
    'scrapy_fake_useragent.providers.FixedUserAgentProvider',  # fall back to USER_AGENT value
]

USER_AGENT = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2226.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.4; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2225.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2225.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2224.3 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 4.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36",
    "Mozilla/5.0 (X11; OpenBSD i386) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1944.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.3319.102 Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.2309.372 Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.2117.157 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1866.237 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.137 Safari/4E423F",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.116 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.517 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1664.3 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1664.3 Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.16 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1623.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.17 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.62 Safari/537.36",
    "Mozilla/5.0 (X11; CrOS i686 4319.74.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.57 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.2 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1468.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1467.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1464.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1500.55 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.90 Safari/537.36",
    "Mozilla/5.0 (X11; NetBSD) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.116 Safari/537.36",
    "Mozilla/5.0 (X11; CrOS i686 3912.101.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.116 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.60 Safari/537.17",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1309.0 Safari/537.17"
]

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
# ITEM_PIPELINES = {
#    "dwSpider.pipelines.DwspiderPipeline": 300,
# }
ITEM_PIPELINES = {
    # "scrapy_redis.pipelines.RedisPipeline": 299,
    # "torrez.dwPipelines.page_pipeline.PagePipeline": 299,
    "torrez.dwPipelines.dwImages.DwImagesPipeline": 300,
    "torrez.pipelines.ToRRezPipeline": 301,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

Proxy = 'socks5h://43.154.195.176:9050'
# Proxy = 'http://47.92.119.44:8118'

tor_proxy_config = {
    "http": "socks5h://127.0.0.1:9050",  # Tor代理地址
    "https": "socks5h://127.0.0.1:9050"  # Tor代理地址
}

tor_proxy_server = "socks5h://127.0.0.1:9050"


# # 教授提供
# # 公网
IMAGES_STORE = "s3://dw-bucket/"
AWS_ENDPOINT_URL = 'http://43.154.182.55:9000'
AWS_REGION_NAME = 'ap-southeast-1'
AWS_ACCESS_KEY_ID = 'tsdb1CvWIFRlC4D9ypBO'
AWS_SECRET_ACCESS_KEY = 'yDNV4LMZnMhoqiAePIvMYdrlcQMwhPAt9cZqVAC6'
AWS_USE_SSL = False  # 根据你的OSS设置
AWS_VERIFY = False  # 根据你的OSS设置
MEDIA_ALLOW_REDIRECTS = True
MINIO_ENDPOINT = '43.154.182.55:9000'
MINIO_SECURE = False

MYSQL_HOST = "43.154.182.55"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWD = "123456"
MYSQL_DB_NAME = "dw_spider"
MYSQL_CHARSET = "utf8mb4"

REDIS_HOST = "43.154.182.55"
REDIS_PORT = 6379
REDIS_DB = 4
REDIS_PARAMS = {
    "password": "spider",
}
REDIS_ENCODING = "utf-8"

# 内网
# IMAGES_STORE = "s3://dw-bucket/"
# AWS_ENDPOINT_URL = 'http://172.19.0.2:9000'
# AWS_REGION_NAME = 'ap-southeast-1'
# AWS_ACCESS_KEY_ID = 'Ww0kDlABN5CUWMrl7sOD'
# AWS_SECRET_ACCESS_KEY = 'wKCYTDsLDvGscTJBUX7azeMO9nbhE3RhfzeEjFoY'
# AWS_USE_SSL = False  # 根据你的OSS设置
# AWS_VERIFY = False  # 根据你的OSS设置
# MEDIA_ALLOW_REDIRECTS = True
# MINIO_ENDPOINT = '172.19.0.2:9000'
# MINIO_SECURE = False

# MYSQL_HOST = "172.19.0.2"
# MYSQL_PORT = 3306
# MYSQL_USER = "root"
# MYSQL_PASSWD = "-DW2468spider1357-"
# MYSQL_DB_NAME = "dw_spider"
# MYSQL_CHARSET = "utf8mb4"

# REDIS_HOST = "172.19.0.2"
# REDIS_PORT = 6379
# REDIS_DB = 4
# REDIS_PARAMS = {
#    "password": "spider",
# }
# `REDIS_ENCODING = "utf-8"



# 使用scrapy-redis组件自己的调度器(核心代码共享调度器)
SCHEDULER = "scrapy_redis.scheduler.Scheduler"
# 默认使用优先级队列（默认），其他：PriorityQueue（有序集合），FifoQueue（列表）、LifoQueue（列表）
SCHEDULER_QUEUE_CLASS = 'scrapy_redis.queue.PriorityQueue'
# 是否在开始之前清空 调度器和去重记录，True=清空，False=不清空
SCHEDULER_FLUSH_ON_START = True
# 去调度器中获取数据时，如果为空，最多等待时间（最后没数据，未获取到）
# SCHEDULER_IDLE_BEFORE_CLOSE = 10
# 爬虫停止后，保留／清理Redis中的请求队列以及去重集合 True：保留，False：清理，默认为False
SCHEDULER_PERSIST = True
# # 去重规则对应处理的类， 优先使用DUPEFILTER_CLASS，如果么有就是用SCHEDULER_DUPEFILTER_CLASS
# SCHEDULER_DUPEFILTER_CLASS = 'scrapy_redis.dupefilter.RFPDupeFilter'
# 调度器中请求存放在redis中的key
SCHEDULER_QUEUE_KEY = '%(spider)s:requests'
# 对保存到redis中的数据进行序列化，默认使用pickle
SCHEDULER_SERIALIZER = "scrapy_redis.picklecompat"

# 使用scrapy-redis组件的去重队列（过滤）
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"

# 在redis中保存item数据的key的名字
# REDIS_ITEMS_KEY = '%(spider)s:items'
# start_url储存在redis中的key的名字, 该值在会绑定在spider对象的redis_key属性上
REDIS_START_URLS_KEY = '%(name)s:start_urls'
REDIS_START_URLS_AS_SET = True

# 哈希函数的个数，默认为6，可以自行修改
BLOOMFILTER_HASH_NUMBER = 6
# bloomfilter的bit参数，默认30，占用128MB，去重量级一亿
BLOOMFILTER_BIT = 30

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, '../logs')
IMAGE_PATH = os.path.join(BASE_DIR, '../images')
LOG_LEVEL = 'INFO'

# chrome options
SELENIUM_DRIVER_ARGUMENTS = ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu',
                             '--disable-software-rasterizer', '--disable-incognito', '--ignore-certificate-errors',
                             '--allow-third-party-cookies', '--allow-insecure-localhost', '--disable-web-security',
                             '--allow-running-insecure-content', '--disable-site-isolation-trials',
                             '--disable-features=InsecureDownloadWarnings',
                             '--disable-blink-features=AutomationControlled',
                             # '-headless', 'lang=en_US',
                             # 不安全来源，多个域名要用逗号分隔开
                             '--unsafely-treat-insecure-origin-as-secure=http://envoyyvazgz2wbkq65md7dcqsgmujmgksowhx2446yep7tgnpfvlxbqd.onion',
                             ]
# chrome experimental options
SELENIUM_DRIVER_EXP_ARGUMENTS = {'excludeSwitches': ['enable-automation'],
                                 "useAutomationExtension": False,
                                 "prefs": {"credentials_enable_service": False,  # 添加去掉密码弹窗管理
                                           "profile.password_manager_enabled": False,
                                           "download.default_directory": IMAGE_PATH,
                                           # 设置下载目录(当前目录，可设置其他目录) download_path = './'
                                           "safebrowsing.enabled": True,  # 去掉"此文件类型可能会损害您的计算机”的提示
                                           "download.prompt_for_download": False,  # 开启自动下载
                                           "download.directory_upgrade": True,  # 取消浏览器下载时保存路径弹框
                                           "profile.default_content_setting_values.cookies": 1,
                                           "profile.block_third_party_cookies": False,
                                           "profile.content_settings.exceptions.cookies.*.setting": 1}
                                 }

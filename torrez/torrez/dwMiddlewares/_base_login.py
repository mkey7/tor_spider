from scrapy import signals
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from webdriver_manager.chrome import ChromeDriverManager

from torrez.settings import *
from torrez.utils.log import logger
from torrez.utils.redis import RedisTool


class BaseLoginMiddleware:
    def __init__(self):
        self.cookie = {}
        self.redis_conn = RedisTool().redis_conn
        self.driver = None

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def login_logic(self, spider, web):
        pass

    def process_request(self, request, spider):
        if spider.name == self.target_spider:
            if not request.cookies:
                request.cookies = self.cookie
            if self.driver is not None:
                request.meta['driver'] = self.driver

    def spider_opened(self, spider):
        logger.info("Spider opened: %s" % spider.name)
        if spider.name == self.target_spider:
            self.login_logic(spider)

    def process_response(self, request, response, spider):
        logger.info("response url: %s" % response.url)
        # logger.info("response text: %s" % response.text)
        return response

    def setup_webdriver(self, spider, url):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.accept_insecure_certs = True
        chrome_options.add_argument(f'--proxy-server={Proxy}')

        chrome_options.add_argument('--headless')

        for argument in SELENIUM_DRIVER_ARGUMENTS:
            chrome_options.add_argument(argument)
        for exp_arg_key, exp_arg_value in SELENIUM_DRIVER_EXP_ARGUMENTS.items():
            chrome_options.add_experimental_option(exp_arg_key, exp_arg_value)

        # 是禁止弹出所有窗口(慎用)
        # prefs.update({"profile.default content settings·popups": 0})

        # service = Service("/usr/bin/chromedriver")
        service = Service(ChromeDriverManager().install())
        web = webdriver.Chrome(service=service, options=chrome_options)
        # web = webdriver.Chrome(options=chrome_options)
        web.maximize_window()

        with open('./torrez/utils/stealth.min.js') as f:
            js = f.read()
            web.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": js})

        # 查看特征是否隐藏
        # web.get('https://bot.sannysoft.com/')

        web.get(url)
        return web

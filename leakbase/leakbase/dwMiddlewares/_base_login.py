import logging

from fake_useragent import UserAgent
from scrapy import signals
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from webdriver_manager.chrome import ChromeDriverManager

from leakbase.settings import *
from leakbase.utils.redis_util import RedisTool

logger = logging.getLogger(__name__)


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
        logger.debug("response url: %s" % response.url)
        # logger.info("response text: %s" % response.text)
        return response

    def setup_webdriver(self, spider, url):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.accept_insecure_certs = True
        # chrome_options.add_argument(f'--proxy-server={Proxy}')
        ua = UserAgent()
        chrome_options.add_argument(f'--user-agent={ua.random}')
        chrome_options.add_argument('--headless')

        if not SHOW_BROWSER:
            chrome_options.add_argument('--headless')

        for argument in SELENIUM_DRIVER_ARGUMENTS:
            chrome_options.add_argument(argument)
        for exp_arg_key, exp_arg_value in SELENIUM_DRIVER_EXP_ARGUMENTS.items():
            chrome_options.add_experimental_option(exp_arg_key, exp_arg_value)

        # 是禁止弹出所有窗口(慎用)
        # prefs.update({"profile.default content settings·popups": 0})
        service = Service(ChromeDriverManager().install())
        # service = Service("/usr/bin/chromedriver")
        web = webdriver.Chrome(service=service, options=chrome_options)
        web.maximize_window()

        with open('./leakbase/utils/stealth.min.js') as f:
            js = f.read()
            web.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": js})

        # 查看特征是否隐藏
        # web.get('https://bot.sannysoft.com/')

        web.get(url)
        return web

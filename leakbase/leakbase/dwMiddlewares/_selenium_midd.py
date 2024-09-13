from scrapy import signals
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service

from webdriver_manager.chrome import ChromeDriverManager

from leakbase.settings import Proxy
from leakbase.utils.request import SeleniumRequest


class SeleniumMiddleware:
    def __init__(self, driver_arguments, driver_exp_arguments):

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument(f'--proxy-server={Proxy}')
        chrome_options.add_argument('--headless')

        for argument in driver_arguments:
            chrome_options.add_argument(argument)
        for exp_arg_key, exp_arg_value in driver_exp_arguments.items():
            chrome_options.add_experimental_option(exp_arg_key, exp_arg_value)

        # service = Service("/usr/bin/chromedriver")
        # self.driver = webdriver.Chrome(service=service, options=chrome_options)
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        with open('./leakbase/utils/stealth.min.js') as f:
            js = f.read()
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": js})

    @classmethod
    def from_crawler(cls, crawler):
        driver_arguments = crawler.settings.get('SELENIUM_DRIVER_ARGUMENTS')
        driver_exp_arguments = crawler.settings.get('SELENIUM_DRIVER_EXP_ARGUMENTS')
        middleware = cls(driver_arguments=driver_arguments, driver_exp_arguments=driver_exp_arguments)

        crawler.signals.connect(middleware.spider_closed, signals.spider_closed)
        return middleware

    def process_request(self, request, spider):
        # cookies = request.cookies
        if not isinstance(request, SeleniumRequest):
            if request.url == spider.start_url:
                request = SeleniumRequest(url=request.url, screenshot=True, script=None,
                                          method=request.method, meta=request.meta, wait_time=10,
                                          wait_until=EC.visibility_of_element_located(
                                              (By.CLASS_NAME, 'p-nav-smallLogo')))
            else:
                return None

        # 查看特征是否隐藏
        # self.driver.get('https://bot.sannysoft.com/')
        # self.driver.save_screenshot('images/sannysoft.png')

        # 如果request meta里面有driver，则使用
        # 否则用新初始化的并且 访问一次url，要不然后续的cookie设置报错
        if request.meta['driver'] is not None:
            self.driver = request.meta['driver']
        else:
            self.driver.get(request.url)
            self.driver.implicitly_wait(3)

        # self.driver.delete_all_cookies()
        # for name, value in cookies.items():
        #     # 加上转换判断，防止首次登录的时候转换报错
        #     name_converted = name if isinstance(name, str) else str(name, encoding='utf-8')
        #     value_converted = value if isinstance(value, str) else str(value, encoding='utf-8')
        #     if name_converted == 'ar_debug':
        #         domain = '.www.google-analytics.com'
        #     elif name_converted.startswith('xf_'):
        #         domain = 'leakbase.io'
        #     else:
        #         domain = '.leakbase.io'
        #     https_only_keys = ['ar_debug', 'session', 'xf_session', 'xf_user']
        #     secure_keys = ['ar_debug', 'session', 'xf_csrf', 'xf_session', 'xf_user']
        #     https_only = True if name_converted in https_only_keys else False
        #     secure = True if name_converted in secure_keys else False
        #     cookies_dict = {'domain': domain, 'name': name_converted, 'value': value_converted,
        #                     'httpOnly': https_only, 'secure': secure}
        #     if name_converted == 'session':
        #         cookies_dict['same_site'] = 'Lax'
        #     elif name_converted == 'ar_debug':
        #         cookies_dict['same_site'] = 'None'
        #     self.driver.add_cookie(cookies_dict)

        self.driver.get(request.url)

        if request.wait_until:
            WebDriverWait(self.driver, request.wait_time).until(request.wait_until)

        if request.screenshot:
            request.meta['screenshot'] = self.driver.get_screenshot_as_png()

        if request.script:
            self.driver.execute_script(request.script)

        body = str.encode(self.driver.page_source)

        # Expose the driver via the "meta" attribute
        request.meta.update({'driver': self.driver})

        return HtmlResponse(
            self.driver.current_url,
            body=body,
            encoding='utf-8',
            request=request
        )

    def spider_closed(self):
        self.driver.quit()

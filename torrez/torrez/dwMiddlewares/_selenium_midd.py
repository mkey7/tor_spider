from scrapy import signals
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service

from webdriver_manager.chrome import ChromeDriverManager

from torrez.settings import Proxy
from torrez.utils.request import SeleniumRequest


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
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        # self.driver = webdriver.Chrome(options=chrome_options)

        with open('./torrez/utils/stealth.min.js') as f:
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
        if not isinstance(request, SeleniumRequest):
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

        self.driver.delete_all_cookies()
        for name, value in request.cookies.items():
            self.driver.add_cookie({'name': str(name, encoding='utf-8'), 'value': str(value, encoding='utf-8')})

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

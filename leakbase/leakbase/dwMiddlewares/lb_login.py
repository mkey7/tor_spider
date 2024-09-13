from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tenacity import retry, retry_if_result

from leakbase.dwMiddlewares._base_login import *


class LeakBaseLoginMiddleware(BaseLoginMiddleware):
    target_spider = 'leakbase'
    login_url = "https://leakbase.io"

    def login_logic(self, spider):
        cookie = RedisTool().get_cookie(spider.name)
        if cookie:
            self.cookie = cookie
            logger.info("Using existing cookie from Redis.")
            web = self.setup_webdriver(spider, self.login_url)
            self.driver = web
            WebDriverWait(web, 15).until(EC.visibility_of_element_located((By.CLASS_NAME, 'p-nav-smallLogo')))

            self.driver.implicitly_wait(3)
            return

        web = self.setup_webdriver(spider, self.login_url)
        self.driver = web
        WebDriverWait(web, 15).until(EC.visibility_of_element_located((By.CLASS_NAME, 'p-nav-smallLogo')))
        self.process_login_validation(web)

    def should_retry(result):
        return result is None

    @retry(retry=retry_if_result(should_retry))
    def process_login_validation(self, web):
        # 登录页登录操作
        user_name = "dark2dark2"
        passwd = "Aaaa1111$"
        user_input_element = web.find_element(By.ID, "ctrl_loginWidget_login")
        passwd_input_element = web.find_element(By.ID, "ctrl_loginWidget_password")
        user_input_element.send_keys(user_name)
        passwd_input_element.send_keys(passwd)

        button_element = web.find_element(By.CLASS_NAME, 'button--icon--login')
        button_element.click()

        # 等待dashboard页面出来后，保存cookie
        try:
            WebDriverWait(web, 30).until(EC.visibility_of_element_located((By.CLASS_NAME, 'p-navgroup--member')))
        except TimeoutException as te:
            logger.info("failed to find the validation error hints information!")
            return None

        self.get_store_cookie(web)

        return "login_success"

    # 获取token，存redis
    def get_store_cookie(self, web):
        self.cookie = {item['name']: item['value'] for item in web.get_cookies()}
        logger.info("web get cookies:%s", web.get_cookies())
        logger.info("self cookie:%s", self.cookie)
        # RedisTool().set_cookie(self.target_spider, self.cookie, -1)

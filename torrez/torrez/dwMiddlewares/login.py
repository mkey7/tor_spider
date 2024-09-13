from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tenacity import retry, retry_if_result

from torrez.dwMiddlewares._base_login import BaseLoginMiddleware
from torrez.utils.log import logger


class ToRReZLoginMiddleware(BaseLoginMiddleware):
    target_spider = 'torrez'
    login_url = "http://mmd32xdcmzrdlpoapkpf43dxig5iufbpkkl76qnijgzadythu55fvkqd.onion/login"
    cookie_name = 'torrez_cookie'
    dashboard_url = "http://mmd32xdcmzrdlpoapkpf43dxig5iufbpkkl76qnijgzadythu55fvkqd.onion/home"

    def login_logic(self, spider):
        if self.redis_conn.exists(self.cookie_name):
            print("Using existing cookie from Redis.")
            self.cookie = self.redis_conn.hgetall(self.cookie_name)
            self.driver = self.setup_webdriver(spider, self.dashboard_url)
            self.driver.implicitly_wait(3)
            return

        web = self.setup_webdriver(spider, self.login_url)

        WebDriverWait(web, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "titleHeader")))
        self.process_login_validation(web, self.cookie_name)
        self.driver = self.setup_webdriver(spider, self.dashboard_url)
        self.driver.implicitly_wait(3)

    def should_retry(result):
        return result is None

    @retry(retry=retry_if_result(should_retry))
    def process_login_validation(self, web, cookie_name):
        user_name = "xiaoxiaolengyu"
        passwd = "Aaaa1111$"
        user_input_element = web.find_element(By.ID, "username")
        passwd_input_element = web.find_element(By.ID, "password")
        user_input_element.send_keys(user_name)
        passwd_input_element.send_keys(passwd)

        # todo 连接接码平台
        # 等待用户输入验证码
        captcha_input = input("请输入验证码: ")
        captcha_input_element = web.find_element(By.ID, "inputCaptcha")
        captcha_input_element.send_keys(captcha_input)
        button_element = web.find_element(By.CSS_SELECTOR, '[class="btn btn-primary"]')

        button_element.click()

        # 等待dashboard页面出来后，保存cookie
        try:
            WebDriverWait(web, 30).until(EC.url_contains("home"))
        except TimeoutException as te:
            logger.info("failed to find the validation error hints information!")
            return None

        self.get_store_cookie(web)

        return "login_success"

    # 获取token，存redis
    def get_store_cookie(self, web):
        # self.cookie = captcha_input = input("请输入验证码: ")
        self.cookie = {item['name']: item['value'] for item in web.get_cookies()}
        print(web.get_cookies())
        print(self.cookie)
        self.redis_conn.hmset(self.cookie_name, self.cookie)

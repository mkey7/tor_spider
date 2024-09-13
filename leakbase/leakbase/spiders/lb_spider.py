import hashlib
import json
import logging
import re
from copy import deepcopy
from datetime import datetime

import scrapy
from bs4 import BeautifulSoup
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.utils.python import to_unicode
from scrapy_redis.spiders import RedisSpider
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from twisted.internet.error import TimeoutError, TCPTimedOutError, DNSLookupError
from w3lib.url import canonicalize_url

from leakbase.dwItems.page_item import PageItem
from leakbase.dwItems.post_item import PostItem
from leakbase.dwItems.site_item import SiteItem
from leakbase.dwItems.user_item import UserItem
from leakbase.utils.minio_util import MinioUtil
from leakbase.utils.redis_util import RedisTool
from leakbase.utils.request import SeleniumRequest

logger = logging.getLogger(__name__)


class LeakBaseSpider(RedisSpider):
    name = 'leakbase'
    redis_key = "leakbase:start_urls"

    page_url_base = "https://leakbase.io"
    start_url = "https://leakbase.io"
    start_url_base = "https://leakbase.io"

    # 版块列表，可并行执行，也可以单线程执行，配置settings：CONCURRENT_REQUESTS = 1，否则爬回来的顺序是乱的
    start_urls = [start_url]
    border_list = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.failed_urls = []
        redis_conn = RedisTool().redis_conn
        redis_conn.sadd(self.redis_key, *self.start_urls)

    # 进入首页
    def parse(self, response):
        if response.status != 200:
            self.crawler.stats.inc_value('failed_url_count')
            self.failed_urls.append(response.url)

        soup = BeautifulSoup(response.text, 'lxml')
        site_item = SiteItem()
        screenshot_raw = response.meta['screenshot']
        self.set_item_site(site_item, response.encoding, response.url, soup, screenshot_raw)
        yield site_item

        # 主题列表获取
        boards = []
        category_els = soup.find_all('div', class_='block--category')
        for category_el in category_els:
            inner_boards = category_el.find_all(name='h3', attrs={'class': 'node-title'})
            boards.extend(inner_boards)
        for border in boards:
            # for border in boards[1:2]:  # 测试代码
            border_url_path = border.find('a').get('href')
            border_name = border.find('a').get_text()
            if border_name == 'Leak News':  # 忽略leak new页面
                continue
            self.border_list.append(border_name)
            border_url = self.page_url_base + border_url_path
            # 访问板块页面
            yield SeleniumRequest(url=border_url, method='GET', dont_filter=True,
                                  callback=self.parse_border_page, errback=self.request_errback,
                                  meta={'border_name': border_name},
                                  wait_time=10,
                                  wait_until=EC.visibility_of_element_located((By.CLASS_NAME, 'p-nav-smallLogo')),
                                  screenshot=True)

    def parse_border_page(self, response):
        border_name = response.meta['border_name']
        soup = BeautifulSoup(response.text, 'lxml')
        screenshot_raw = response.meta['screenshot']
        page_item = PageItem()
        self.set_item_default(page_item)
        self.set_item_original_default(page_item, response.encoding, response.url, soup, screenshot_raw)
        yield page_item

        page_nav_main_el = soup.find('ul', class_='pageNav-main')
        if page_nav_main_el is None:
            page_count = 1
        else:
            page_nav_els = page_nav_main_el.find_all('li', class_='pageNav-page')
            page_last = page_nav_els[-1].get_text()
            page_count = int(page_last)

        for page in range(page_count, 0, -1):
            # for page in range(2, 0, -1):  # 测试代码
            page_url = response.url + "page-" + str(page)
            dont_filter = True if page == 1 else False
            logger.debug("page_url: %s", page_url)
            # 最后一页总是不过滤，保证可以每次都爬取最后一页
            yield SeleniumRequest(url=page_url, method='GET', dont_filter=dont_filter,
                                  callback=self.parse_post_list, errback=self.request_errback,
                                  meta={'border_name': border_name},
                                  wait_time=10,
                                  wait_until=EC.visibility_of_element_located((By.CLASS_NAME, 'p-nav-smallLogo')),
                                  screenshot=True)

    def parse_post_list(self, response):
        border_name = response.meta['border_name']
        soup = BeautifulSoup(response.text, 'lxml')
        screenshot_raw = response.meta['screenshot']
        page_item = PageItem()
        self.set_item_default(page_item)
        self.set_item_original_default(page_item, response.encoding, response.url, soup, screenshot_raw)
        yield page_item

        try:
            posts = soup.find('div', class_='structItemContainer-group').find_all('div', class_='structItem')
            for post in posts:
                title_el = post.find('div', class_='structItem-title')
                title_text = title_el.find('a').get_text()
                post_url_path = title_el.find('a').get('href')
                post_url = self.page_url_base + post_url_path
                struct_item_minor_els = post.find('ul', class_='structItem-parts').find_all('li')
                if struct_item_minor_els[0].find('a') is not None:
                    post_author_name = struct_item_minor_els[0].find('a').get_text()
                    author_url_path = struct_item_minor_els[0].find('a').get('href')
                    user_id = author_url_path.split('/')[-2]
                else:
                    post_author_name = struct_item_minor_els[0].get_text()
                    user_id = 'None:' + post_author_name
                post_time = struct_item_minor_els[1].find('time').get('datetime')
                post_reply_count = post.find('dl', class_='pairs pairs--justified').find('dd').get_text()
                post_view_count = post.find('dl', class_='pairs pairs--justified structItem-minor').find(
                    'dd').get_text()
                post_update_time = post.find('time', class_='structItem-latestDate u-dt').get('datetime')
                post_id = post_url_path.split('/')[-2]

                label_dict = {self.TAG_BORDER: border_name}
                extra_info_el = post.find('ul', class_='structItem-extraInfo')
                if extra_info_el is not None:
                    labels = []
                    label_els = post.find('ul', class_='structItem-extraInfo').find('li').find_all('a')
                    for label_el in label_els:
                        labels.append(label_el.find('span').get_text())
                    if len(labels) > 0:
                        label_dict[self.TAG_POST] = json.dumps(labels)

                # 组装post_item
                post_item = PostItem()
                self.set_item_default(post_item)
                post_item['post_id'] = post_id
                post_item['user_id'] = user_id
                post_item['user_name'] = post_author_name
                post_item['title'] = title_text
                post_item['publish_time'] = self.convert_datetime(post_time)
                post_item['update_time'] = self.convert_datetime(post_update_time)
                post_item['commented_count'] = post_reply_count
                if 'K' in post_view_count:
                    post_view_count = int(post_view_count.replace('K', '')) * 1000
                post_item['clicks_times'] = post_view_count
                post_item['topic_id'] = post_url_path
                post_item['url'] = post_url
                post_item['topic_type'] = self.POST_TYPE_TOPIC
                post_item['label'] = json.dumps(label_dict)

                yield SeleniumRequest(url=post_url, method='GET', dont_filter=True,
                                      callback=self.parse_post_page, errback=self.request_errback,
                                      meta={'post_item': deepcopy(post_item)},
                                      wait_time=10,
                                      wait_until=EC.visibility_of_element_located((By.CLASS_NAME, 'p-nav-smallLogo')),
                                      screenshot=True)
        except Exception as e:
            self.remove_fingerprint(response.url)
            logger.error("parse_user_detail error:", e)

    # 帖子分页处理
    def parse_post_page(self, response):
        post_item = response.meta['post_item']
        soup = BeautifulSoup(response.text, 'lxml')
        screenshot_raw = response.meta['screenshot']
        page_item = PageItem()
        self.set_item_default(page_item)
        self.set_item_original_default(page_item, response.encoding, response.url, soup, screenshot_raw)
        yield page_item

        page_nav_main_el = soup.find('ul', class_='pageNav-main')
        if page_nav_main_el is None:
            page_count = 1
        else:
            page_nav_els = page_nav_main_el.find_all('li', class_='pageNav-page')
            page_last = page_nav_els[-1].get_text()
            page_count = int(page_last)

        for page in range(page_count):
            page_url = response.url + "page-" + str(page + 1)
            logger.debug("page_url: %s", page_url)
            yield SeleniumRequest(url=page_url, method='GET', dont_filter=True,
                                  callback=self.parse_post_detail, errback=self.request_errback,
                                  meta={'post_item': deepcopy(post_item),
                                        'page_num': (page + 1)},
                                  wait_time=10,
                                  wait_until=EC.visibility_of_element_located((By.CLASS_NAME, 'p-nav-smallLogo')),
                                  screenshot=True)

    # 帖子详情
    def parse_post_detail(self, response):
        post_item = response.meta['post_item']
        page_num = response.meta['page_num']
        soup = BeautifulSoup(response.text, 'lxml')
        screenshot_raw = response.meta['screenshot']
        page_item = PageItem()
        self.set_item_default(page_item)
        self.set_item_original_default(page_item, response.encoding, response.url, soup, screenshot_raw)
        yield page_item

        articles = soup.find_all('article', class_='message--post')

        user_dict = {}
        for index, article in enumerate(articles):
            post_author = article.find('h4', class_='message-name')
            post_author_link_el = post_author.find('a')
            if post_author_link_el is not None:
                post_author_link_url = post_author_link_el.get('href')
                user_name = post_author_link_el.find('span').get_text()
                user_id = post_author_link_el.get('href').split('/')[-2]
                user_dict[user_id] = post_author_link_url
            else:
                user_name = post_author.find('span').get_text()
                user_id = 'None:' + user_name

            like_link_el = article.find('a', class_='reactionsBar-link')
            thumbs_up = None
            if like_link_el is not None:
                if 'others' in like_link_el.get_text():
                    logger.debug("like_link_el.get_text(): %s", like_link_el.get_text())
                    thumbs_up_num = int(like_link_el.get_text().split(' ')[-2].strip())
                    thumbs_up_visible = len(like_link_el.find_all('bdi'))
                    thumbs_up = str(thumbs_up_num + thumbs_up_visible)
                else:
                    tus = len(like_link_el.find_all('bdi'))
                    thumbs_up = '1' if tus == 0 else tus

            post_num = article.find('ul', class_='message-attribution-opposite').find_all('li')[2].get_text(strip=True)
            # TODO 回复帖子查看隐藏内容

            if post_num == '#1':  # 采集主题信息, 第一页第一条
                # 第一个post_body是主贴信息
                message_body_el = article.find('article', class_='message-body')
                if message_body_el is not None:
                    post_topic = message_body_el.find('div', class_='bbWrapper')
                    post_item['content'] = post_topic.get_text()
                    if thumbs_up is not None:
                        post_item['thumbs_up'] = thumbs_up
                    try:
                        image_list = post_topic.find_all('img')
                        images_dict = {}
                        for image in image_list:
                            filename = image.get('alt')
                            image_url = image.get('src')
                            if filename is not None and filename != '':
                                if image_url.startswith('http'):
                                    images_dict[filename] = image_url
                                else:
                                    if not image_url.startswith('data:image/gif'):
                                        images_dict[filename] = self.start_url_base + image_url
                        # 下载图片文件，然后存放到images_obs_dict字典中, 在ImagesPipeline中处理
                        if len(images_dict) > 0:
                            post_item['images'] = json.dumps(images_dict)
                    except:
                        logger.info("no image found")
                else:
                    post_item['content'] = ""
                post_item['uuid'] = hashlib.sha1(
                    (post_item['platform'] + '_' + post_item['post_id']).encode('utf-8')).hexdigest()
                # 重新改写 user_id 为 user表的uuid
                post_item['user_id'] = hashlib.sha1((post_item['platform'] + '_' + user_id).encode('utf-8')).hexdigest()

                logger.debug("leakbase forums spider, post_item data:%s", post_item)
                yield post_item
            else:  # 采集评论
                reply_item = PostItem()
                self.set_item_default(reply_item)
                message_body_el = article.find('article', class_='message-body')
                if message_body_el is not None:
                    reply_item['content'] = message_body_el.find('div', class_='bbWrapper').get_text()
                else:
                    reply_item['content'] = ""
                reply_item['post_id'] = article.get('data-content')
                publish_time = article.find('time').get('datetime')
                reply_item['publish_time'] = self.convert_datetime(publish_time)
                reply_item['user_id'] = user_id
                reply_item['user_name'] = user_name
                reply_item['topic_id'] = post_item['post_id']

                post_quote = article.find('blockquote', class_='bbCodeBlock')
                if post_quote is not None and post_quote.find('div', class_='bbCodeBlock-title') is not None:
                    quote_comment_href = post_quote.find('div', class_='bbCodeBlock-title').find('a')
                    if quote_comment_href is not None:
                        reply_item['commented_id'] = quote_comment_href.get('data-content-selector').split('#')[1]
                    else:
                        reply_item['commented_id'] = ""
                    reply_item['commented_user_names'] = quote_comment_href.get_text().replace(' said:', '')

                reply_item['topic_type'] = self.POST_TYPE_REPLY
                if thumbs_up is not None:
                    post_item['thumbs_up'] = thumbs_up
                reply_item['uuid'] = hashlib.sha1(
                    (reply_item['platform'] + '_' + reply_item['post_id']).encode('utf-8')).hexdigest()
                reply_item['user_id'] = hashlib.sha1(
                    (reply_item['platform'] + '_' + user_id).encode('utf-8')).hexdigest()

                logger.debug("leakbase forums spider, reply_item data:%s", reply_item)
                yield reply_item

        # 采集用户信息
        for user_id, user_link_url in user_dict.items():
            user_info_url = self.start_url_base + user_link_url
            yield SeleniumRequest(url=user_info_url,
                                  method='GET',
                                  callback=self.parse_user_info, errback=self.request_errback,
                                  meta={'user_id': user_id, 'user_link_url': user_info_url},
                                  dont_filter=False,
                                  wait_time=10,
                                  wait_until=EC.visibility_of_element_located((By.CLASS_NAME, 'p-body-pageContent')),
                                  screenshot=True)

    def parse_user_info(self, response):
        soup = BeautifulSoup(response.text, 'lxml')
        user_id = response.meta['user_id']
        user_link_url = response.meta['user_link_url']

        screenshot_raw = response.meta['screenshot']
        page_item = PageItem()
        self.set_item_default(page_item)
        self.set_item_original_default(page_item, response.encoding, response.url, soup, screenshot_raw)
        yield page_item

        try:
            user_item = UserItem()
            self.set_item_default(user_item)

            user_item['user_id'] = user_id
            user_item['url'] = user_link_url
            problem_message = soup.find('h1', class_='p-title-value')
            if problem_message is not None and 'problems' in problem_message.get_text():
                limit_message = soup.find('div', class_='p-body-pageContent').find('div', class_='blockMessage')
                user_item['user_description'] = limit_message.get_text()
            else:
                user_item['user_name'] = soup.find('h1', class_='memberHeader-name').find('span',
                                                                                          class_='username').get_text()
                if soup.find('div', class_='messeng-none') is not None:
                    user_description = soup.find('div', class_='messeng-none').get_text(strip=True)
                    user_item['user_description'] = user_description
                author_avatar_link = soup.find('span', class_='avatarWrapper').find('a')
                avatar_url_path = None
                if author_avatar_link is not None:
                    avatar_url_path = author_avatar_link.find('img').get('src')

                pairs_inlines = soup.find('div', class_='memberHeader-blurbContainer').find_all('dl',
                                                                                                class_='pairs pairs--inline')
                user_create_time_txt = pairs_inlines[0].find('time').get('datetime')
                reg_time = self.convert_datetime(user_create_time_txt)
                user_item['register_time'] = reg_time
                if len(pairs_inlines) > 1:
                    last_view_time_txt = pairs_inlines[1].find('time').get('datetime')
                    user_item['last_active_time'] = self.convert_datetime(last_view_time_txt)

                pairses = soup.find('div', class_='pairJustifier').find('dl', class_='pairs')
                user_item['post_counts'] = pairses.find('a').get_text(strip=True).replace(',', '')
                if avatar_url_path is not None:
                    if avatar_url_path.startswith('http'):
                        avatar_url = avatar_url_path
                    else:
                        avatar_url = self.page_url_base + avatar_url_path
                    avatar_name = avatar_url_path.split('?')[-1]
                    oss_path = MinioUtil().upload_image(avatar_url, 'dw-bucket',
                                                        self.name + '/images/' + avatar_name + '.png')
                    user_img_dict = {'name': avatar_name + '.png', 'url': avatar_url, 'oss_path': oss_path}
                    user_item['user_img'] = json.dumps(user_img_dict)
            user_item['uuid'] = hashlib.sha1(
                (user_item['platform'] + '_' + user_item['user_id']).encode('utf-8')).hexdigest()

            yield user_item
        except Exception as e:
            self.remove_fingerprint(response.url)
            logger.error("parse_user_detail error:", e)

    def set_item_default(self, item: scrapy.Item):
        item['platform'] = self.name
        item['domain'] = self.start_url_base
        item['lang'] = "en_us"
        item['net_type'] = "tor"
        item['crawl_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def set_item_original_default(self, item: scrapy.Item, encoding, url, soup, screenshot_raw):
        item['content_encode'] = encoding
        item['title'] = soup.find("head").find('title').getText(strip=True)
        content = soup.get_text()

        meta_tags = soup.find("head").find_all('meta')
        meta_dict = {}
        for meta in meta_tags:
            if meta.get('charset') is not None:
                meta_dict['charset'] = meta.get('charset')
            elif meta.get('name') or meta.get('property') or meta.get('http-equiv') is not None:
                name = meta.get('name') or meta.get('property') or meta.get('http-equiv')
                meta_content = meta.get('content')
                if name:
                    meta_dict[name] = meta_content

        json_data = json.dumps(meta_dict, indent=2)
        item['meta'] = json_data
        minio_client = MinioUtil()

        # 使用MD5算法对字节对象进行哈希
        byte_string = str(url).encode('utf-8')
        hash_object = hashlib.md5(byte_string)
        url_hash = hash_object.hexdigest()
        page_url = minio_client.upload_file_bytes(screenshot_raw, 'dw-bucket',
                                                  self.name + '/original_image/' + url_hash + '.jpg')
        txt_url = minio_client.upload_string(content, 'dw-bucket', self.name + '/text/' + url_hash + '.txt')
        item['url'] = url
        item['snapshot_name'] = url_hash + '.jpg'
        item['snapshot_oss_path'] = page_url
        item['content'] = txt_url

    def set_item_site(self, site_item: scrapy.Item, encoding, url, soup, screenshot_raw):
        site_item['content_encode'] = encoding
        site_item['title'] = soup.find("head").find('title').getText(strip=True)
        site_item['site_name'] = self.name
        site_item['domain'] = self.start_url_base
        site_item['lang'] = "en_us"
        site_item['net_type'] = "tor"

        minio_client = MinioUtil()

        # 使用MD5算法对字节对象进行哈希
        byte_string = str(url).encode('utf-8')
        hash_object = hashlib.md5(byte_string)
        url_hash = hash_object.hexdigest()
        page_url = minio_client.upload_file_bytes(screenshot_raw, 'dw-bucket',
                                                  self.name + '/site_info/' + url_hash + '.jpg')
        site_item['url'] = url
        site_item['name'] = url_hash + '.jpg'
        site_item['index_url'] = self.start_url_base
        site_item['path'] = page_url
        site_item['image_hash'] = url_hash
        site_item['last_status'] = 'online'
        site_item['is_recent_online'] = 'online'
        site_item['service_type'] = '论坛'

        statics = soup.find('div', class_='p-body-sidebar').find_all('div', class_='block')
        forum_pairses = statics[2].find_all('dl', class_='pairs')
        thread_counts = forum_pairses[0].find('dd').get_text()
        post_counts = forum_pairses[1].find('dd').get_text()
        members = forum_pairses[2].find('dd').get_text()

        link_pairses = statics[3].find_all('dl', class_='pairs')
        categories = link_pairses[0].find('dd').get_text()
        items = link_pairses[1].find('dd').get_text()
        views = link_pairses[2].find('dd').get_text()
        clicks = link_pairses[3].find('dd').get_text()
        comments = link_pairses[4].find('dd').get_text()
        ratings = link_pairses[5].find('dd').get_text()
        reviews = link_pairses[6].find('dd').get_text()

        scale = {"threads:": thread_counts, "posts:": post_counts, "members:": members, "online:": categories,
                 "items:": items, "views:": views, "clicks:": clicks, "comments:": comments, "ratings:": ratings,
                 "reviews:": reviews}
        site_item['scale'] = json.dumps(scale)
        border_list = ['Database Discussion', 'Communication', 'Questions', 'Forum news', 'Leak News',
                       'Private Combolists', 'Private Logs & Passwords', 'Private Leaks & Databases',
                       'Private Url:Log:Pass', 'Leaked Databases From Staff Team', 'Big Database Leaks',
                       'Clouds Pack', 'Database Log:Pass / Num:Pass', 'Databases Without Passwords',
                       'Mixed Database (Random)', 'Database Japan & China', 'Database Crypto & BTC',
                       'Dehashed Database', 'Hashed Database', 'Database Games', 'Valid Combos',
                       'Passwords list for HashCat', 'FTP, SSH, RDP Acces', 'Logs and Backups', 'Proxy lists',
                       'Accounts', 'Cookies', 'TXT & SQL utils', 'Trash / Dead Links and Content']
        site_item['label'] = json.dumps(border_list)

    POST_TYPE_TOPIC = "topic"
    POST_TYPE_REPLY = "comment"
    TAG_BORDER = "border_tag"
    TAG_POST = "post_tag"

    @staticmethod
    def convert_datetime(datetime_str):
        logger.debug("datetime_str: %s", datetime_str)
        # 去除末尾的 '+0000'
        input_string = datetime_str[:-5]

        # 转换为 datetime 对象
        dt = datetime.strptime(input_string, "%Y-%m-%dT%H:%M:%S")

        # 格式化为 MySQL 的 DATETIME 格式
        formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
        return formatted_date

    def remove_fingerprint(self, url):
        fingerprint_data = {
            "method": to_unicode("GET"),
            "url": canonicalize_url(url),
            "body": "",
        }
        # 移除scrapy redis指纹信息
        fingerprint_json = json.dumps(fingerprint_data, sort_keys=True)
        fingerprint_digest = hashlib.sha1(fingerprint_json.encode()).hexdigest()
        RedisTool().remove_fingerprint(self.name, fingerprint_digest)
        logger.error("remove_fingerprint: %s", fingerprint_digest)
        logger.info("remove_fingerprint, url: %s", url)

    def request_errback(self, failure):
        logger.error(repr(failure))

        if failure.check(HttpError):
            response = failure.value.response
            logger.error('HttpError on %s', response.url)
        elif failure.check(DNSLookupError):
            request = failure.request
            logger.error('DNSLookupError on %s', request.url)
        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            logger.error('TimeoutError on %s', request.url)

        request = failure.request
        self.remove_fingerprint(request.url)

    # 判断某个元素是否存在
    def is_element_exist(self, soup, element_class_name):
        try:
            if soup.find(name=None, attrs={'class': element_class_name}) is not None:
                return True
            else:
                return False
        except Exception as e:
            print("判断是否存在{element_class_name}元素失败:", e)
            return False

    # 判断是否下载类帖子
    def is_download_post(self, downloadElement):
        try:
            # 下载类帖子
            if downloadElement.find('b').get_text().contains("Download"):
                return True
            else:
                return False
        except Exception as e:
            print("判断是否下载类帖子失败:", e)
            return False

    # 回复帖子
    def reply_post(self, postElement, response_url):
        try:
            # 帖子回复请求url：response_url + add-reply
            reply_url = response_url + "add-reply"
            print("回复帖子URL:", reply_url)

            # 发起POST请求，回复内容是：ha ha ha ha，不带回调函数，请求后继续往下执行
            data = {
                "message": "ha ha ha ha"
            }
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            yield scrapy.FormRequest(url=reply_url,
                                     method='POST',
                                     formdata=data,
                                     headers=headers,
                                     #  callback=self.parse_post_detail,
                                     dont_filter=True)
        except Exception as e:
            print("回复帖子失败:", e)

    # 判断是否需要回复帖子，才能查看帖子隐藏内容
    def is_need_reply(self, postElement):
        try:
            if self.is_element_exist(postElement, 'bbCodeBlock bbCodeBlock--hide bbCodeBlock--hidden'):
                # 判断bbCodeBlock-title是否包含reply字样
                if self.is_element_exist(postElement, 'bbCodeBlock-title'):
                    # 判断bbCodeBlock-title元素是否包含"reply"
                    bbCodeBlock_title = postElement.find(name=None, attrs={'class': 'bbCodeBlock-title'}).get_text()
                    if bbCodeBlock_title.contains("reply"):
                        return True

                # 判断bbCodeBlock-content是否包含reply字样
                if self.is_element_exist(postElement, 'bbCodeBlock-content'):
                    # 判断bbCodeBlock-content元素是否包含"reply"
                    bbCodeBlock_content = postElement.find(name=None, attrs={'class': 'bbCodeBlock-content'}).get_text()
                    if bbCodeBlock_content.contains("reply"):
                        return True

                return False

        except Exception as e:
            print("判断是否需要回复帖子失败:", e)
            return False

    # 点赞
    def like_post(self, postElement):
        try:
            # 点赞
            # postElement.find_all(name=None, attrs={'class': 'reaction-sprite js-reaction'})[0].click()
            # TODO 发起请求点赞：https://leakbase.io/posts/87946/react?reaction_id=1
            print("已点赞")
            return True
        except Exception as e:
            print("点赞失败:", e)
            return False

    # 判断是否有人点赞:reactionsBar-link 元素的text中" and 266 others"的266，并返回点赞数
    def is_liked(self, postElement):
        try:
            # 判断是否有人点赞
            reactionsBar_link = postElement.find_all(name=None, attrs={'class': 'reactionsBar-link'})[0]
            if reactionsBar_link is not None:
                reactions_count = reactionsBar_link.get_text().split(" ")[-2]
                reactions_count = int(reactions_count)
                print("reactions_count:", reactions_count)
                return reactions_count
            else:
                return 0
        except Exception as e:
            print("判断是否有人点赞失败:", e)
            return 0

import hashlib
import json
from copy import deepcopy
import datetime

import scrapy
from bs4 import BeautifulSoup

from torrez.dwItems.goods_item import GoodsItem
from torrez.dwItems.page_item import PageItem
from torrez.dwItems.site_item import SiteItem
from scrapy_redis.spiders import RedisSpider
from torrez.utils.log import logger
from torrez.utils.minio_util import MinioUtil
from torrez.utils.redis import RedisTool
from torrez.utils.request import SeleniumRequest

from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.utils.python import to_unicode
from twisted.internet.error import TimeoutError, TCPTimedOutError, DNSLookupError
from w3lib.url import canonicalize_url



class ToRReZSpider(RedisSpider):
    name = 'torrez'
    redis_key = "torrez:start_urls"

    drugs_url_base = "http://mmd32xdcmzrdlpoapkpf43dxig5iufbpkkl76qnijgzadythu55fvkqd.onion/items/category/drugs-and-chemicals"
    page_url_base = "http://mmd32xdcmzrdlpoapkpf43dxig5iufbpkkl76qnijgzadythu55fvkqd.onion/items/category/drugs-and-chemicals?order=none&vendors=all&shipping_to=any&shipping_from=any&product_type=any&payments_method=any&page="
    start_url_base = "http://mmd32xdcmzrdlpoapkpf43dxig5iufbpkkl76qnijgzadythu55fvkqd.onion/home"
    domain_url = "http://mmd32xdcmzrdlpoapkpf43dxig5iufbpkkl76qnijgzadythu55fvkqd.onion"
    start_urls = [drugs_url_base]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.failed_urls = []
        redis_conn = RedisTool().redis_conn
        redis_conn.sadd(self.redis_key, *self.start_urls)

    def parse(self, response):


        yield SeleniumRequest(url=response.url,
                                  method='GET',
                                  callback=self.get_site_item,
                                  errback=self.request_errback,
                                  dont_filter=True,
                                  screenshot=True,
                                  meta={'times': 1}
                                  )

        # 使用 JSON 解析响应内容
        if response.url == self.drugs_url_base:
            soup = BeautifulSoup(response.text, 'lxml')
            page_list = soup.find_all(name=None, attrs={'class': 'page-link'})
            page_count = int(page_list[-2].text)

            for i in range(page_count, 0, -1):
                dont_filter = True if i == 1 else False
                page_url = self.page_url_base + str(i)
                yield SeleniumRequest(url=page_url,
                                      method='GET',
                                      callback=self.parse_table_data,
                                      errback=self.request_errback,
                                      dont_filter=dont_filter,
                                      screenshot=True,
                                      meta={'times': 1})

    def parse_table_data(self, response):
        page_item = PageItem()
        self.set_item_original_default(page_item, response)
        yield page_item

        soup = BeautifulSoup(response.text, 'lxml')
        # table = soup.find('tbody')
        table = soup.find_all('tbody')[1]
        rows = table.find_all('tr')

        for row in rows:
            items = row.find_all('td')

            class_name = items[0].attrs['class'][0]
            href = items[0].find('a').get('href')
            imgUrl = items[0].find('img').attrs['src']
            name = items[1].contents[1].contents[0]
            categories = items[1].find('div').find_all('a')

            category_str = ''
            for category in categories:
                category_str = category_str.replace(' ', '').replace('\n', '') + category.contents[0] + ' >> '

            if len(category_str) == 0:
                category_str = category_str[:-2]
            category_str = category_str
            shipping_span_set = items[2].find_all('span')
            shopping_from = ''
            shopping_to = ''
            for string_span in shipping_span_set:
                if 'shippingFrom' in str(string_span):
                    shopping_from = str(string_span.next).replace(' ', '').replace('\n', '')
                if 'shippingTo' in str(string_span):
                    shopping_to = str(string_span.next).replace(' ', '').replace('\n', '')

            price = items[3].find('span').text.replace(' ', '').replace('\n', '')

            vendor = items[4].find('a').text.replace(' ', '').replace('\n', '')

            spans = items[4].find_all('span')
            positive_neutral_negative_feedback = spans[0].text.replace(' ', '').replace('\n', '')
            rank = spans[1].text.replace(' ', '').replace('\n', '')

            # toRRezItem = self.saveData(class_name, name, href, imgUrl, category_str, shopping_from, shopping_to, price,
            #                            vendor,
            #                            positive_neutral_negative_feedback, rank)
            toRRezItem = GoodsItem()
            toRRezItem['crawl_category_1'] = class_name
            toRRezItem['goods_name'] = name
            toRRezItem['url'] = href
            byte_string = str(imgUrl).encode('utf-8')
            hash_object = hashlib.md5(byte_string)
            url_hash = hash_object.hexdigest()+'.jpg'
            images = {url_hash: imgUrl}
            toRRezItem['images'] = json.dumps(images)

            toRRezItem['crawl_category'] = category_str
            toRRezItem['goods_area'] = shopping_from
            toRRezItem['goods_ship_to'] = shopping_to
            toRRezItem['price'] = price
            toRRezItem['user_name'] = vendor
            # toRRezItem['PositiveNeutralNegativeFeedback'] = positive_neutral_negative_feedback
            toRRezItem['threaten_level'] = rank

            yield SeleniumRequest(url=href,
                                      method='GET',
                                      callback=self.parse_goods_detail,
                                      errback=self.request_errback,
                                      dont_filter=False,
                                      screenshot=True,
                                      meta={'toRRezItem': deepcopy(toRRezItem), 'times': 1})

    def parse_goods_detail(self, response):
        page_item = PageItem()
        self.set_item_original_default(page_item, response)
        yield page_item

        toRRezItem = response.meta['toRRezItem']

        self.set_item_default(toRRezItem)

        byte_string = str(response.url).encode('utf-8')
        hash_object = hashlib.md5(byte_string)
        url_hash = hash_object.hexdigest()
        toRRezItem['goods_id'] = url_hash
        toRRezItem["uuid"] = hashlib.sha1((toRRezItem['platform'] + '_' + toRRezItem['goods_id']).encode('utf-8')).hexdigest()
        soup = BeautifulSoup(response.text, 'lxml')
        body = soup.find('body')
        table = body.find_all('div')[0].find('main').find_all("div", {"class": {"clo-sm-9", "mb-3"}})[0]

        name = table.find_all("div", {"class": {"titleHeader"}})[0].find('h3').getText(strip=True)
        description = table.find_all("div", {"class": {"tab-pane"}})[0].getText(strip=True)
        secondurl = table.find_all("li", {"class": {"nav-item"}})[1].find('a').attrs['href']
        # subName = table.find_all("div", {"class": {"col", "singleItemDetails"}})[0].find('h6').text
        trs = table.find_all("div", {"class": {"col", "singleItemDetails"}})[0].find('table').find_all('tr')
        # toRRezItem = ToRRezItem()
        for tr in trs:
            trName = tr.find_all('th')[0].getText(strip=True)
            if trName == 'Sold by':
                toRRezItem['user_name'] = tr.find_all('td')[0].find('a').getText(strip=True)
                toRRezItem['url_and_address'] = tr.find_all('td')[0].find('a').get('href')

            if trName == 'Items Available':
                sku_quantify = tr.find_all('td')[0].getText(strip=True)
                if 'Unlimited' in sku_quantify:
                    sku_quantify = -1
                toRRezItem['sku_quantify'] = int(sku_quantify)

            if trName == 'Item views':
                toRRezItem['goods_browse_count'] = tr.find_all('th')[1].getText(strip=True)

            if trName == 'Product Type':
                toRRezItem['crawl_category'] = tr.find_all('td')[0].getText(strip=True)

        toRRezItem['goods_name'] = name
        toRRezItem['goods_info'] = description

        meta = {'times': 1, 'toRRezItem': deepcopy(toRRezItem)}
        yield SeleniumRequest(url=secondurl,
                              method='GET',
                              callback=self.parse_goods_feedback_info,
                              errback=self.request_errback,
                              dont_filter=True,
                              screenshot=True,
                              meta=meta)
        # pass

    def parse_goods_feedback_info(self, response):
        toRRezItem = response.meta['toRRezItem']
        # todo 放开账号限制后再爬取相关用户信息
        soup = BeautifulSoup(response.text, 'html.parser')
        body = soup.find('body')
        table = body.find_all('div')[0].find('main').find_all("div", {"class": {"clo-sm-9", "mb-3"}})[0]

        description = table.find_all("div", {"class": {"tab-pane"}})[0].getText(strip=True)
        feedbackCount = 0
        buys = ''
        commentlist = []
        if "This particular item has no feedback yet" not in description:
            rows = table.find_all("div", {"class": {"tab-pane"}})[0].find_all("div", {"class": {"singleReview"}})
            for row in rows:
                name = row.find('strong').getText(strip=True)
                manner = row.find_all('small')[0].getText(strip=True)
                consumption = row.find_all('small')[1].getText(strip=True)
                comment = row.find('p').getText(strip=True)
                commentDic = {}
                commentDic['name'] = name
                commentDic['manner'] = manner
                commentDic['consumption'] = consumption
                commentDic['comment'] = comment
                commentlist.append(commentDic)
                feedbackCount = feedbackCount + 1
                buys = buys + name + ','

            description = commentlist
        else:
            description = ''

        toRRezItem['goods_feedback_count'] = feedbackCount
        toRRezItem['goods_buyer'] = buys
        toRRezItem['comment_content'] = str(description)
        yield toRRezItem

    def parse_goods_refunds_policy_info(self, response, toRRezItem):
        soup = BeautifulSoup(response.text, 'html.parser')
        body = soup.find('body')
        table = body.find_all('div')[0].find('main').find_all("div", {"class": {"clo-sm-9", "mb-3"}})[0]
        description = table.find_all("div", {"class": {"tab-pane"}})[0].getText(strip=True)
        toRRezItem['RefundsPolicy'] = description
        logger.debug("parse_goods_refunds_policy_info over data for %s", toRRezItem)
        return toRRezItem

    def get_site_item(self, response):
        screenshot_raw = response.meta['screenshot']
        soup = BeautifulSoup(response.text, 'html.parser')

        site_item = SiteItem()
        site_item['platform'] = self.name
        site_item['domain'] = self.domain_url
        site_item['lang'] = "en_us"
        site_item['net_type'] = "tor"
        minio_client = MinioUtil()

        # 使用MD5算法对字节对象进行哈希
        byte_string = str(response.url).encode('utf-8')
        hash_object = hashlib.md5(byte_string)
        url_hash = hash_object.hexdigest()
        page_url = minio_client.upload_file_bytes(screenshot_raw, 'dw-bucket',
                                                  self.name + '/original_image/' + url_hash + '.jpg')

        site_item['site_name'] = self.name
        site_item['title'] = soup.find("head").find('title').getText(strip=True)
        site_item['name'] = url_hash + '.jpg'
        site_item['index_url'] = self.start_url_base
        site_item['path'] = page_url
        site_item['image_hash'] = url_hash
        site_item['last_status'] = 'online'
        site_item['is_recent_online'] = 'online'

        lis = soup.find("div", {"class": {"categories"}}).find("ul", {"class": {"sidebar"}}).contents

        goods_nums = 0
        goods_levels = []
        for li in lis:
            if li == '\n':
                continue
            else:
                section = li.find("a")
                goods_nums = goods_nums + int(section.find("span").getText(strip=True).replace("(", "").replace(")", ""))
                goods_levels.append(str(section.getText(strip=True)))

        site_item['goods_count'] = goods_nums
        site_item['goods_label'] = str(goods_levels)

        yield site_item

    def set_item_original_default(self, item: scrapy.Item, response):
        screenshot_raw = response.meta['screenshot']
        item['content_encode'] = response.encoding
        soup = BeautifulSoup(response.text, 'lxml')
        item['title'] = soup.find("head").find('title').getText(strip=True)
        content = soup.get_text()
        meta_tags = soup.find("head").find_all('meta')
        meta_dict = {}
        for meta in meta_tags:
            name = meta.get('name') or meta.get('property') or meta.get('http-equiv')
            content = meta.get('content')
            if name:
                meta_dict[name] = content

        item['meta'] =json.dumps(meta_dict, indent=2)

        minio_client = MinioUtil()

        byte_string = str(response.url).encode('utf-8')
        hash_object = hashlib.md5(byte_string)
        url_hash = hash_object.hexdigest()
        page_url = minio_client.upload_file_bytes(screenshot_raw, 'dw-bucket',
                                                  self.name + '/original_image/' + url_hash + '.jpg')
        txt_url = minio_client.upload_string(content, 'dw-bucket', self.name + '/text/' + url_hash + '.txt')
        item['url'] = response.url
        item['snapshot_name'] = url_hash + '.jpg'
        item['snapshot_oss_path'] = page_url
        item['snapshot_hash'] = url_hash
        item['content'] = txt_url

        self.set_item_default(item)

    def set_item_default(self, item: scrapy.Item):
        item['platform'] = self.name
        item['domain'] = self.start_url_base
        item['lang'] = "en_us"
        item['net_type'] = "tor"
        item['crawl_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def remove_fingerprint(self, url):
        fingerprint_data = {
            "method": to_unicode("GET"),
            "url": canonicalize_url(url),
            "body": "",
        }
        fingerprint_json = json.dumps(fingerprint_data, sort_keys=True)
        fingerprint_digest = hashlib.sha1(fingerprint_json.encode()).hexdigest()
        RedisTool().remove_fingerprint(self.name, fingerprint_digest)
        logger.info("remove_fingerprint: %s", fingerprint_digest)
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


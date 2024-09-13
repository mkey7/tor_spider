# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import pymysql
from pymysql.converters import escape_string
from twisted.enterprise import adbapi

from torrez.dwItems.goods_item import GoodsItem
from torrez.dwItems.page_item import PageItem
from torrez.dwItems.site_item import SiteItem
from torrez.settings import MYSQL_HOST, MYSQL_DB_NAME, MYSQL_USER, MYSQL_PORT, MYSQL_PASSWD, \
    MYSQL_CHARSET
from torrez.utils.log import logger


class ToRRezPipeline:
    def __init__(self, dbpool):
        self.dbpool = dbpool
        self.ITME_TYPE_MAP = {
            ('torrez', GoodsItem): self.do_insert_forums_goods,
            ('torrez', PageItem): self.do_insert_forums_original_page,
            ('torrez', SiteItem): self.do_insert_site_info
        }

        self.POST_FIELDS = [
            "uuid", "post_id", "platform", "domain", "topic_type", "user_id", "user_name", "url", "title", "content",
            "label", "images", "images_obs", "attachments", "attachments_obs", "commented_count", "clicks_times",
            "thumbs_up", "thumbs_down", "publish_time", "update_time", "crawl_tags", "comment_id", "topic_id",
            "commented_id", "commented_user_id", "commented_user_names", "emails", "bitcoin_addresses", "eth_addresses",
            "url_and_address", "extract_entity", "threaten_level", "lang", "net_type", "crawl_time"
        ]
        self.POST_UPDATE_FIELDS = [
            "commented_count", "clicks_times", "thumbs_up", "thumbs_down", "publish_time", "update_time", "crawl_time"
        ]

        self.USER_FIELDS = [
            "uuid", "user_id", "platform", "domain", "user_name", "user_nickname", "user_description", "url",
            "identity_tags", "register_time", "last_active_time", "goods_orders", "level", "member_degree", "ratings",
            "user_img", "topic_nums", "post_counts", "area", "user_verification", "user_order_count",
            "user_viewed_count", "user_feedback_count", "user_followed_count", "user_related_url_and_address",
            "user_related_images", "user_related_files", "user_recent_day", "user_related_crawl_tags", "emails",
            "bitcoin_addresses", "eth_addresses", "user_hazard_level", "lang", "net_type", "crawl_time"
        ]
        self.USER_UPDATE_FIELDS = [
            "last_active_time", "level", "member_degree", "ratings", "user_img", "topic_nums", "post_counts",
            "user_order_count", "user_viewed_count", "user_feedback_count", "user_followed_count", "crawl_time"]

        self.GOODS_FIELDS = [
            "uuid", "goods_id", "platform", "domain", "goods_name", "goods_info", "images", "images_obs", "attachments",
            "bitcoin_addresses", "contacts", "crawl_category", "crawl_category_1", "goods_area", "goods_browse_count",
            "goods_buyer", "goods_feedback_count", "comment_user_id", "comment_id", "comment_time", "comment_content",
            "goods_ship_to", "goods_tag", "goods_update_time", "price", "publish_time", "sku_quantify", "sold_count",
            "url", "user_id", "user_name", "url_and_address", "keywords_by_nlp", "threaten_level", "lang", "net_type",
            "crawl_time", "created_at"
        ]

        self.GOODS_UPDATE_FIELDS = [
            "goods_browse_count", "goods_buyer", "goods_feedback_count", "comment_user_id", "comment_id",
            "comment_time", "comment_content", "goods_update_time", "price", "publish_time", "sku_quantify",
            "sold_count", "crawl_time"
        ]

        self.SITE_FIELDS = [
            "site_name", "domain", "index_url", "title", "description", "snapshot", "name", "path", "image_hash",
            "last_status", "first_publish_time", "last_publish_time", "service_type", "is_recent_online",
            "scale", "active_level", "label", "goods_label", "goods_count", "pay_methods", "goods_user_count",
            "site_hazard", "lang", "net_type", "user_info"
        ]

        self.SITE_UPDATE_FIELDS = [
            "name", "path", "image_hash", "last_status", "last_publish_time", "is_recent_online", "scale",
            "goods_count", "goods_user_count"
        ]

        self.ORIGINAL_PAGE_FIELDS = [
            "platform", "domain", "url", "content_encode", "meta", "page_source", "title", "snapshot_name",
            "snapshot_oss_path", "snapshot_hash", "label", "publish_time", "images", "subject", "content",
            "warn_topics", "url_and_address", "extract_entity", "threaten_level", "lang", "net_type", "crawl_time"
        ]

        self.ORIGINAL_PAGE_UPDATE_FIELDS = [
            "snapshot_name", "snapshot_oss_path", "snapshot_hash", "publish_time", "content", "crawl_time"
        ]

    @classmethod
    def from_settings(cls, settings):
        db_params = {
            'host': MYSQL_HOST,
            'port': MYSQL_PORT,
            'db': MYSQL_DB_NAME,
            'user': MYSQL_USER,
            'passwd': MYSQL_PASSWD,
            'charset': MYSQL_CHARSET,
            'cursorclass': pymysql.cursors.DictCursor,
            'use_unicode': True,
            'cp_reconnect': True
        }
        dbpool = adbapi.ConnectionPool("pymysql", **db_params)
        return cls(dbpool)

    def process_item(self, item, spider):
        # 检查是否有对应的处理函数
        insert_function = self.ITME_TYPE_MAP.get((spider.name, type(item)))
        if insert_function is None:
            # 如果没有对应的处理函数，记录日志并返回
            logger.warning(f"Unhandled item type: {type(item)}, spider: {spider.name}")
            return

        # 运行插入操作并处理错误
        try:
            query = insert_function(item)
            query.addErrback(self.handle_error, item, spider)
        except Exception as e:
            logger.error(f"Error processing item from {spider.name}: {item}, {e}")

        return item

    # def close_spider(self, spider):
    #     self.dbpool.close()

    def execute_insert(self, table, data, update_fields):
        placeholders = ', '.join(['%s'] * len(data))
        columns = ', '.join(data.keys())
        sql = ""
        if len(update_fields) == 0:
            sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            logger.debug("sql: %s", sql)  # 谨慎记录SQL，避免敏感信息泄露
        else:
            update_clauses = ', '.join([f"{field} = VALUES({field})" for field in update_fields])
            sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update_clauses}"
            logger.debug("DUPLICATE KEY UPDATE SQL: %s", sql)  # 谨慎记录SQL，避免敏感信息泄露

        # 使用runInteraction执行插入操作
        def _execute(cursor):
            try:
                cursor.execute(sql, tuple(data.values()))
            except pymysql.Error as e:
                logger.error(f"Error {e.args[0]}: {e.args[1]}")
                # cursor.rollback()
                raise

        return self.dbpool.runInteraction(_execute)

    def do_insert_forums_post(self, item):
        data = self.build_insert_data(item, self.POST_FIELDS)
        update_data = self.build_update_fields(item, self.POST_UPDATE_FIELDS)
        return self.execute_insert("post", data, update_data)

    def do_insert_forums_user(self, item):
        data = self.build_insert_data(item, self.USER_FIELDS)
        update_data = self.build_update_fields(item, self.USER_UPDATE_FIELDS)
        return self.execute_insert("user", data, update_data)

    def do_insert_forums_goods(self, item):
        data = self.build_insert_data(item, self.GOODS_FIELDS)
        update_data = self.build_update_fields(item, self.GOODS_UPDATE_FIELDS)
        return self.execute_insert("goods", data, update_data)

    def do_insert_forums_original_page(self, item):
        data = self.build_insert_data(item, self.ORIGINAL_PAGE_FIELDS)
        update_data = self.build_update_fields(item, self.ORIGINAL_PAGE_UPDATE_FIELDS)
        return self.execute_insert("original_page", data, update_data)

    def do_insert_site_info(self, item):
        data = self.build_insert_data(item, self.SITE_FIELDS)
        update_data = self.build_update_fields(item, self.SITE_UPDATE_FIELDS)
        return self.execute_insert("site", data, update_data)

    @staticmethod
    def build_insert_data(item, fields):
        esc_array = ['title', 'content', 'goods_name', 'goods_info']
        return {field: (escape_string(item[field]) if field in esc_array else item[field])
                for field in fields if field in item}

    @staticmethod
    def build_update_fields(item, fields):
        return [field for field in fields if field in item]

    @staticmethod
    def handle_error(failure, item, spider):
        logger.error(f"Error processing item from {spider.name}: {item}")
        logger.error(failure.getTraceback())

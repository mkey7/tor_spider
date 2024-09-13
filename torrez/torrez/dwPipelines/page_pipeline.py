# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import pymysql
from pymysql.converters import escape_string
from twisted.enterprise import adbapi


from torrez.settings import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_DB_NAME, MYSQL_PASSWD, MYSQL_CHARSET
from torrez.utils.log import logger


# useful for handling different item types with a single interface

class PagePipeline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool
        self.ORIGINAL_PAGE_FIELDS = [
            "platform", "domain", "url", "content_encode", "meta", "page_source", "title", "snapshot_name",
            "snapshot_oss_path", "snapshot_hash", "label", "publish_time", "subject", "content",
            "warn_topics", "url_and_address", "extract_entity", "threaten_level", "lang", "net_type", "crawl_time"
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
        # 运行插入操作并处理错误
        try:
            query = self.do_insert_forums_original_page(item)
            query.addErrback(self.handle_error, item, spider)
        except Exception as e:
            logger.error(f"Error processing item from {spider.name}: {item}, {e}")

        return item

    def execute_insert(self, table, data):
        placeholders = ', '.join(['%s'] * len(data))
        columns = ', '.join(data.keys())
        sql = f"INSERT IGNORE INTO {table} ({columns}) VALUES ({placeholders})"
        logger.debug("sql: %s", sql)  # 谨慎记录SQL，避免敏感信息泄露

        # 使用runInteraction执行插入操作
        def _execute(cursor):
            try:
                cursor.execute(sql, tuple(data.values()))
            except pymysql.Error as e:
                logger.error(f"Error {e.args[0]}: {e.args[1]}")
                # cursor.rollback()
                raise

        return self.dbpool.runInteraction(_execute)


    def do_insert_forums_original_page(self, item):
        data = self.build_insert_data(item, self.ORIGINAL_PAGE_FIELDS)
        return self.execute_insert("original_page", data)

    @staticmethod
    def build_insert_data(item, fields):
        esc_array = ['title', 'content', 'goods_name', 'goods_info']
        return {field: (escape_string(item[field]) if field in esc_array else item[field])
                for field in fields if field in item}

    @staticmethod
    def handle_error(failure, item, spider):
        logger.error(f"Error processing item from {spider.name}: {item}")
        logger.error(failure.getTraceback())

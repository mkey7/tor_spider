import pymysql
from dbutils.pooled_db import PooledDB

from leakbase.settings import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_DB_NAME, MYSQL_PASSWD, MYSQL_CHARSET


class DBManager:
    _connection_pool = None

    def __new__(cls, *args, **kwargs):
        if not cls._connection_pool:
            print('new _connection_pool')
            cls._connection_pool = PooledDB(creator=pymysql, mincached=1, maxcached=20, host=MYSQL_HOST,
                                            port=MYSQL_PORT, user=MYSQL_USER, passwd=MYSQL_PASSWD, db=MYSQL_DB_NAME,
                                            charset=MYSQL_CHARSET)
        return super(DBManager, cls).__new__(cls)

    def __init__(self):
        self.dbpool = DBManager._connection_pool
        self.cursor = self.dbpool.connection().cursor()

    def get_incremental(self, spider_name, plate_name):
        sql = """SELECT * FROM dw_spider.incremental WHERE spider_name = '{}' AND plate_name = '{}'""".format(
            spider_name, plate_name)
        count = self.cursor.execute(sql)
        result = self.cursor.fetchone() if count > 0 else None
        if result is not None and result[4] is not None and result[5] is not None:
            return result[4], result[5]
        else:
            return 0, 20

    def ins_up_incremental(self, spider_name, plate_name, page_count, crawled_count):
        # 使用参数化查询
        sql = """INSERT INTO incremental (spider_name, plate_name, page_count, page_crawled_count) VALUES (%s, %s, %s, %s) 
                 ON DUPLICATE KEY UPDATE page_count = %s, page_crawled_count = %s"""
        row_count = self.cursor.execute(sql, (
            spider_name, plate_name, page_count, crawled_count, page_count, crawled_count))
        self.cursor.connection.commit()
        return row_count


if __name__ == '__main__':
    db = DBManager()
    #
    # db.ins_up_incremental('onniforums', 'home', 1000, 1)
    # crawled_page_count, limit = db.get_incremental_data('onniforums', 'home')
    # print(crawled_page_count)
    # print(limit)

    page_count = 4
    page_crawled_count = 0
    limit = 4
    start = page_count - page_crawled_count if (page_count - page_crawled_count) > 0 else 1
    print('start page count:', start)
    end = start - limit if (start - limit) > 0 else 0
    print('end page count:', end)
    for page in range(start, end, -1):
        print(page)
        print('page_crawled_count:', page_count - page + 1)

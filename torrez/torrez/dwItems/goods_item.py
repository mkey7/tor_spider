import scrapy


class GoodsItem(scrapy.Item):
    uuid = scrapy.Field()
    goods_id = scrapy.Field()
    platform = scrapy.Field()
    domain = scrapy.Field()
    goods_name = scrapy.Field()
    goods_info = scrapy.Field()
    images = scrapy.Field()
    images_obs = scrapy.Field()
    attachments = scrapy.Field()
    bitcoin_addresses = scrapy.Field()
    contacts = scrapy.Field()
    crawl_category = scrapy.Field()
    crawl_category_1 = scrapy.Field()
    goods_area = scrapy.Field()
    goods_browse_count = scrapy.Field()
    goods_buyer = scrapy.Field()
    goods_feedback_count = scrapy.Field()
    comment_user_id = scrapy.Field()
    comment_id = scrapy.Field()
    comment_time = scrapy.Field()
    comment_content = scrapy.Field()
    goods_ship_to = scrapy.Field()
    goods_tag = scrapy.Field()
    goods_update_time = scrapy.Field()
    price = scrapy.Field()
    publish_time = scrapy.Field()
    sku_quantify = scrapy.Field()
    sold_count = scrapy.Field()
    url = scrapy.Field()
    user_id = scrapy.Field()
    user_name = scrapy.Field()
    url_and_address = scrapy.Field()
    keywords_by_nlp = scrapy.Field()
    threaten_level = scrapy.Field()
    lang = scrapy.Field()
    net_type = scrapy.Field()
    crawl_time = scrapy.Field()
    created_at = scrapy.Field()

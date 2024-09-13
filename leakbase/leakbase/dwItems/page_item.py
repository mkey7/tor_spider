import scrapy


class PageItem(scrapy.Item):
    domain = scrapy.Field()
    platform = scrapy.Field()
    url = scrapy.Field()
    content_encode = scrapy.Field()
    meta = scrapy.Field()
    page_source = scrapy.Field()
    title = scrapy.Field()
    snapshot_name = scrapy.Field()
    snapshot_oss_path = scrapy.Field()
    snapshot_hash = scrapy.Field()
    label = scrapy.Field()
    publish_time = scrapy.Field()
    images = scrapy.Field()
    subject = scrapy.Field()
    content = scrapy.Field()
    warn_topics = scrapy.Field()
    url_and_address = scrapy.Field()
    extract_entity = scrapy.Field()
    lang = scrapy.Field()
    net_type = scrapy.Field()
    crawl_time = scrapy.Field()
    images_obs = scrapy.Field()
    field_name = scrapy.Field()



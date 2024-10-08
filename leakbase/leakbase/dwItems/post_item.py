import scrapy


class PostItem(scrapy.Item):
    uuid = scrapy.Field()
    post_id = scrapy.Field()
    platform = scrapy.Field()
    domain = scrapy.Field()
    topic_type = scrapy.Field()
    user_id = scrapy.Field()
    user_name = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    label = scrapy.Field()
    images = scrapy.Field()
    images_obs = scrapy.Field()
    attachments = scrapy.Field()
    attachments_obs = scrapy.Field()
    commented_count = scrapy.Field()
    clicks_times = scrapy.Field()
    thumbs_up = scrapy.Field()
    thumbs_down = scrapy.Field()
    publish_time = scrapy.Field()
    update_time = scrapy.Field()
    crawl_tags = scrapy.Field()
    comment_id = scrapy.Field()
    topic_id = scrapy.Field()
    commented_id = scrapy.Field()
    commented_user_id = scrapy.Field()
    commented_user_names = scrapy.Field()
    emails = scrapy.Field()
    bitcoin_addresses = scrapy.Field()
    eth_addresses = scrapy.Field()
    url_and_address = scrapy.Field()
    extract_entity = scrapy.Field()
    threaten_level = scrapy.Field()
    lang = scrapy.Field()
    net_type = scrapy.Field()
    crawl_time = scrapy.Field()

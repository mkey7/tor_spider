import hashlib
import json
import logging

import scrapy
from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline
from scrapy.utils.python import to_bytes

from leakbase.utils.minio_util import MinioUtil
from leakbase.utils.redis_util import RedisTool

logger = logging.getLogger(__name__)


class DwImagesPipeline(ImagesPipeline):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redis_tool = RedisTool()

    def get_media_requests(self, item, info):
        if item is None or 'images' not in item:
            logger.debug("get_media_requests item is None or 'images' is None")
            return item

        logger.debug("get_media_requests images: %s", item["images"])

        images_dict = json.loads(item["images"])
        for image_name, url in images_dict.items():
            if not self.redis_tool.bf_img_exists(self.spiderinfo.spider.name, url, image_name):
                yield scrapy.Request(url)

    def item_completed(self, results, item, info):
        image_url_paths = {}
        if results is None or len(results) == 0:
            if item is None or 'images' not in item:
                return item
            else:  # 图片下载失败补救措施
                images_dict = json.loads(item["images"])
                for image_name, url in images_dict.items():
                    oss_path = MinioUtil().upload_image(url, 'dw-bucket',
                                                        self.spiderinfo.spider.name + '/images/' + image_name + '.png')
                    image_url_paths[url] = oss_path
        else:
            logger.debug("item_completed, results : %s", results)
            image_url_paths = {x["url"]: x["path"] for ok, x in results if ok}

        logger.debug("images obs: %s", image_url_paths)
        if not image_url_paths:
            return item

        adapter = ItemAdapter(item)
        adapter["images_obs"] = json.dumps(image_url_paths)

        images_dict = json.loads(item['images'])
        for url_out, path in image_url_paths.items():
            for image_name, url_in in images_dict.items():
                if url_out == url_in:
                    self.redis_tool.bf_img_add(self.spiderinfo.spider.name, url_in, image_name)
        return item

    def file_path(self, request, response=None, info=None, *, item=None):
        spider_name = self.spiderinfo.spider.name
        images_dict = json.loads(item['images'])
        for image_name, url in images_dict.items():
            if url == request.url:
                return f"{spider_name}/images/{image_name}"

        image_guid = hashlib.sha1(to_bytes(request.url)).hexdigest()
        return f"{spider_name}/{image_guid}.jpg"

    def image_downloaded(self, response, request, info, *, item=None):
        checksum = None
        try:
            checksum = super().image_downloaded(response, request, info, item=item)
        except Exception as e:
            logger.warning("image_downloaded exception occured！")
            logger.warning(e)
        return checksum

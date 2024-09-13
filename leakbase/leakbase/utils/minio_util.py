import logging
from io import BytesIO

import requests
import urllib3
from minio import Minio

from leakbase.settings import AWS_ENDPOINT_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION_NAME, \
    AWS_VERIFY

# 禁用InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)


class MinioUtil:
    _minio_client = None

    def __new__(cls, *args, **kwargs):
        if not cls._minio_client:
            print('new _minio_client')
            cls._minio_client = Minio(AWS_ENDPOINT_URL.replace('http://', ''),
                                      access_key=AWS_ACCESS_KEY_ID,
                                      secret_key=AWS_SECRET_ACCESS_KEY,
                                      secure=AWS_VERIFY)
        return super(MinioUtil, cls).__new__(cls)

    def __init__(self):
        self.client = MinioUtil._minio_client
        self.endpoint = AWS_REGION_NAME

    def upload_image(self, image_url, bucket_name, object_name=None):
        try:
            # 下载图片
            with requests.get(image_url, stream=True, verify=AWS_VERIFY) as response:
                response.raise_for_status()  # 确保请求成功
                content_length = int(response.headers["Content-Length"])
                image_data = response.raw

                # 如果没有提供对象名称，则使用URL中的文件名
                if object_name is None:
                    object_name = image_url.split('/')[-1]

                # 检查存储桶是否存在
                if not self.client.bucket_exists(bucket_name):
                    self.client.make_bucket(bucket_name)

                # 上传图片
                self.client.put_object(bucket_name, object_name, image_data, content_length)
                logger.debug('图片 %s 已上传到OSS的存储桶 %s 中。', object_name, bucket_name)

                # 构建图片在MinIO中的URL
                image_minio_url = f'{bucket_name}/{object_name}'
                return image_minio_url
        except requests.exceptions.RequestException as e:
            print(f'下载图片时出错: {e}')
            return None
        except Exception as e:
            print(f'上传图片到MinIO时出错: {e}')
            return None

    def upload_file_bytes(self, file_bytes, bucket_name, object_name):
        try:
            # 如果没有提供对象name
            if object_name is None:
                return None

            # 检查存储桶是否存在
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)

            # 上传文件
            file_io = BytesIO(file_bytes)
            self.client.put_object(bucket_name, object_name, file_io, len(file_bytes))
            logger.debug('文件 %s 已上传到OSS的存储桶 %s 中。', object_name, bucket_name)

            # 构建图片在MinIO中的URL
            image_oss_url = f'{bucket_name}/{object_name}'
            return image_oss_url
        except Exception as e:
            print(f'上传文件到OSS时出错: {e}')
            return None

    def upload_string(self, string, bucket_name, object_name):
        return self.upload_file_bytes(bytes(string, 'utf-8'), bucket_name, object_name)


# 使用示例
if __name__ == "__main__":
    minio_client = MinioUtil()
    image_url = 'https://www.baidu.com/img/PCtm_d9c8750bed0b3c7d089fa7d55720d6cf.png'
    bucket_name = 'dw-bucket'
    minio_url = minio_client.upload_image(image_url, bucket_name)
    if minio_url:
        print(f'图片在MinIO中的URL: {minio_url}')

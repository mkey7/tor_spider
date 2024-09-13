import hashlib
from io import BytesIO

import requests
import urllib3
from minio import Minio

from torrez.settings import AWS_ENDPOINT_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, MINIO_ENDPOINT, MINIO_SECURE

# 禁用InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class MinioUtil:
    _minio_client = None

    def __new__(cls, *args, **kwargs):
        if not cls._minio_client:
            print('new _minio_client')
            cls._minio_client = Minio(endpoint=MINIO_ENDPOINT, access_key=AWS_ACCESS_KEY_ID,
                                      secret_key=AWS_SECRET_ACCESS_KEY,
                                      secure=MINIO_SECURE)
        return super(MinioUtil, cls).__new__(cls)

    def __init__(self):
        self.client = MinioUtil._minio_client
        self.endpoint = AWS_ENDPOINT_URL

    def upload_image(self, image_url, bucket_name, object_name=None):
        try:
            # 下载图片
            response = requests.get(image_url, stream=True)
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
            print(f'图片 {object_name} 已上传到MinIO的存储桶 {bucket_name} 中。')

            # 构建图片在MinIO中的URL
            image_minio_url = f'{bucket_name}/{object_name}'
            return image_minio_url
        except Exception as e:
            print(f'上传图片到MinIO时出错: {e}')
            return None
        except requests.exceptions.RequestException as e:
            print(f'下载图片时出错: {e}')
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
            print(f'文件 {object_name} 已上传到OSS的存储桶 {bucket_name} 中。')

            # 构建图片在MinIO中的URL
            image_oss_url = f'{bucket_name}/{object_name}'
            return image_oss_url
        except Exception as e:
            print(f'上传文件到OSS时出错: {e}')
            return None

    def upload_string(self, string, bucket_name, object_name):
        return self.upload_file_bytes(bytes(string, 'utf-8'), bucket_name, object_name)


    def get_hash_by_string(self,string):
        # 将字符串转换为字节对象
        byte_string = string.encode('utf-8')

        # 使用MD5算法对字节对象进行哈希
        hash_object = hashlib.md5(byte_string)
        return hash_object.hexdigest()
# 使用示例
if __name__ == "__main__":
    minio_client = MinioUtil()
    image_url = 'https://www.baidu.com/img/PCtm_d9c8750bed0b3c7d089fa7d55720d6cf.png'
    bucket_name = 'dw-bucket'
    minio_url = minio_client.upload_image(image_url, bucket_name)
    if minio_url:
        print(f'图片在MinIO中的URL: {minio_url}')

    # minio_client = MinioUtil()
    # image_raw = 'test'
    # bucket_name = 'dw-bucket'
    # minio_url = minio_client.upload_file_bytes(bytes(image_raw, 'utf-8'), bucket_name, 'test/test.txt')
    # if minio_url:
    #     print(f'图片在MinIO中的URL: {minio_url}')

    # minio_client = MinioUtil()
    # out = minio_client.get_hash_by_string('test')
    # print(f'图片在MinIO中的URL: {out}')

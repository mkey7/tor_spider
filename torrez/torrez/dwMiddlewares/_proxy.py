from torrez.settings import *


class ProxyMiddleware:
    def __init__(self, settings):
        self.proxy = settings.get('Proxy')

    @classmethod
    def from_crawler(cls, crawler):
        # todo add proxies pools
        # return cls(ip=crawler.settings.get('PROXIES'))
        return cls(crawler.settings)

    def process_request(self, request, spider):
        # ip = random.choice(self.ip)
        # request.meta['proxy'] = ip
        request.meta['proxy'] = Proxy
        # request.meta['proxies'] = tor_proxy_config

import scrapy


class SeleniumRequest(scrapy.Request):

    def __init__(self, *args, wait_time=None, wait_until=None, screenshot=True, script=None, **kwargs):
        self.wait_time = wait_time
        self.wait_until = wait_until
        self.screenshot = screenshot
        self.script = script

        super().__init__(*args, **kwargs)

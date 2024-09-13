# tor网站爬虫项目

## 可通过dockerfile部署
```
docker build -t spider .
docker run -it --name spider1 -v /path/to/project:/home/tor_spider spider
```

## 改进
- 弃用**privoxy**
- 使用**webdriver_manager**管理chromedriver

## 需配置

> leakbase 和 torrez 的setting 都需要修改
> 
> 现在中间件的地址已经配置为我们自己的服务器的配置

- proxy变量：tor服务IP:port
- 数据库中间件服务的相关配置

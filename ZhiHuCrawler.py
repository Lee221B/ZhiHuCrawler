''' 编码格式 = "utf-8",
    Python版本: python3.6.1
    需要第三方库:
        BeautifulSoup,
        requests,
        selenium,
        以及用C++封装好SWIG生成的BloomFilter模块
    作者：
        Lee221B
    最近更新时间：
        2017.12.29
    实现功能：
        爬取知乎话题下的图片，
        图片上限10000张，
        实现了对用户头像、广告图的过滤，
        自动在各话题之间跳转，
        跳转方式取决于知乎本身'''

import time
import re
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import random
import os
import BloomFilter as bf


class ZhiHuCrawler:
    ''' 构造函数中记录爬虫启动至今所下载的图片数量numOfImg及访问url数量umOfURL ，
        爬虫启动的startURL,
        以及将爬虫伪造为浏览器以瞒过反爬虫机制的headers及agent信息，
        为防止爬虫爬取过度频繁导致IP被封，准备了listOfProxies以储存代理https信息,
        listOfProxies中https可能失效，需要手动更新。
        为防止爬虫被捕获在环路中以及下载重复图片，
        调用了BloomFilter以存储已经访问的网页以及图片，
        默认最大爬取深度为30'''
    def __init__(self, url):
        self.numOfImg = 0
        self.numOfURL = 0
        self.startURL = url
        self.agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) ' \
                     'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'
        self.headers = {
            "user-agent": self.agent
        }
        self.listOfProxies = [{"https": "https://113.65.8.221:9999"},
                              {"https": "https://14.153.55.34:3128"},
                              {"https": "https://61.155.164.106:3128"},
                              {"https": "https://112.114.98.247:8118"},
                              {"https": "https://220.168.236.104:8888"},
                              {"https": "https://180.120.214.86:8118"},
                              {"https": "https://113.218.216.226:8888"},
                              {"https": "https://117.121.100.9:3128"},
                              {"https": "https://202.98.197.243:3128"},
                              {"https": "https://61.155.164.106:3128"},
                              {"https": "https://222.64.185.154:9000"},
                              {"https": "https://101.81.106.155:9797"},
                              {"https": "https://183.151.145.78:8118"},
                              {"https": "https://180.76.134.106:3128"},
                              {"https": "https://219.138.58.246:3128"}] #ok
        self.numOfProxies = len(self.listOfProxies)
        self.proxies = self.listOfProxies[0]
        self.filter = bf.BloomFilter()
        self.imageFilter = bf.BloomFilter()
        self.depth = 30

    ''' 当自带的http失效时，爬虫将从已有的代理IP中随机选取https进行爬取'''
    def getProxies(self):
        index = random.randint(0, self.numOfProxies - 1)
        print("采用第 %d 个代理HTTP" % (index + 1))
        self.proxies = self.listOfProxies[index]

    ''' 当所有访问https下载网页html的方法都失败时(由于反爬虫机制或者IP失效)时,
        使用selenium调用Chrome或Safari浏览器来爬取网页html,
        因为此种方法可以爬取动态网页所有内容，
        函数名为 dynamicDownloadPage'''
    def dynamicDownloadPage(self, URL, url):
        try:
            driver = webdriver.Chrome()
        except:
            driver = webdriver.Safari()
        driver.get(URL)
        cookie = driver.get_cookies()
        driver.get(url)
        #self.execute_times(20, driver)
        #print("Here")
        html = driver.page_source
        return html

    ''' 若一定需要爬取动态网页深层的html信息，
        在dynamicDownloadPage中调用execute_times函数，
        以模拟鼠标向下拖拽至底部times次以获取深层html信息'''
    def execute_times(self, times, driver):
        for i in range(times + 1):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)

    ''' 下载url网页的html内容，
        参数URL为访问url的上个网页，
        用以填写 headers 以通过反爬虫机制检查'''
    def downloadPage(self, URL, url):
        ''' 将 URL 填入 headers 中 referer 中，
            referer 为访问的来源网页(也就是你从哪个网页跳转过来),
            知乎会检查 referer 以判断是否为爬虫'''
        self.headers['referer'] = URL
        accessFail = True

        ''' 尝试用真实https访问网页，
            若异常或访问失败，
            调用函数 usingHTTP 以代理https访问网页'''
        try:
            print("正在访问 %s" % url)
            response = requests.get(url, headers=self.headers, timeout=20)
            print("服务器响应码为: %d" % response.status_code, end='\t')
            if response.status_code == 200:
                print("HTTP连接成功")
                accessFail = False
                html = response.text
            else:
                print("本机HTTP被标记为爬虫或由于其他原因，访问失败")
                accessFail = True
        except:
            html = self.usingHTTP(URL, url)

        if accessFail == True:
            html = self.usingHTTP(URL, url)
        return html

    ''' 遍历listOfProxies中https信息以访问网页，
        若全部失效则采用函数dynamicDownloadPage'''
    def usingHTTP(self, URL, url):
        proxiesSuccess = False
        while not proxiesSuccess:
            print('正在访问 %s 代理HTTP: ' % url, self.proxies['https'])
            try:
                response = requests.get(url, headers=self.headers, proxies=self.proxies, timeout=20)
                print("服务器响应码为: %d" % response.status_code, end='\t')
                if response.status_code == 200:
                    proxiesSuccess = True
                    print("HTTP连接成功")
                    html = response.text
                else:
                    print("HTTP被标记为爬虫或由于其他原因，访问失败")
                    self.listOfProxies.remove(self.proxies)
                    self.numOfProxies -= 1
                    if self.numOfProxies == 0:
                        print("所有HTTP连接失败", end='\t')
                        print("将启用selenium")
                        html = self.dynamicDownloadPage(URL, url)
            except:
                proxiesSuccess = False
                print("HTTP连接失败")
                self.listOfProxies.remove(self.proxies)
                self.numOfProxies -= 1
                if self.numOfProxies == 0:
                    print("所有HTTP连接失败", end='\t')
                    print("将启用selenium")
                    html = self.dynamicDownloadPage(URL, url)
            if not proxiesSuccess and self.numOfProxies != 0:
                self.getProxies()

        return html

    ''' 解析html文件中图片(jpg, png格式)，
        并下载保存于子目录picture中'''
    def downloadImage(self, url, html):
        soup = BeautifulSoup(html, "lxml")

        ''' 知乎上所有图片都存储在figure标签下'''
        figures = soup.find_all("figure")
        urls = []
        for figure in figures:
            ''' 尝试用多种方法获取图片url'''
            try:
                item = figure.img["data-original"]
            except:
                try:
                    item = figure.img['data-actualsrc']
                except:
                    try:
                        item = figure.img['src']
                    except:
                        '''若均失败则用正则表达式匹配图片url，正确性存疑'''
                        regx1 = "https://[0-9a-zA-Z/_\.-]+\.jpg"
                        pattern = re.compile(regx1, re.S)
                        items = re.findall(pattern, figure.noscript.text)

            ''' 对该网页中图片url进行小规模去重'''
            if item not in urls:
                urls.append(item)

        for imageURL in urls:
            ''' 检验图片url是否已经下载过'''
            if self.imageFilter.alreadyInHash(imageURL):
                print("Picture from %s having been downloaded" % imageURL)
                pass
            elif imageURL[-3:] == 'gif':
                pass
            else:
                ''' 将已下载图片url存入hash中'''
                self.imageFilter.addToHash(imageURL)
                print("Downloading image from %s" % imageURL)
                self.headers['referer'] = url
                image = requests.get(imageURL, headers=self.headers)

                ''' 判断是否为jpeg格式，特殊处理'''
                if imageURL[-4] == '.':
                    fileName = ("%s." + imageURL[-3:]) % (self.numOfImg + 1)
                else:
                    fileName = ("%s." + imageURL[-4:]) % (self.numOfImg + 1)
                if not os.path.exists('picture'):
                    os.mkdir('picture')
                with open(os.getcwd() + '/picture/' + fileName, "wb") as fp:
                    fp.write(image.content)
                    fp.close()
                    self.numOfImg += 1
                    if self.numOfImg == 10000:
                        print("Dowloading completed")
                        return
                    print("Having downloaded %d images" % self.numOfImg)
        return

    ''' 解析html文件中所有链接以跳转'''
    def getURL(self, html):
        urls = []
        soup = BeautifulSoup(html, "lxml")
        ''' 解析html文件中所有url，以跳转到其他网页'''
        metas = soup.find_all(href=re.compile('[0-9a-zA-Z\.\-_]{1,}'))
        for meta in metas:
            try:
                url2Aceess = meta['content']
            except:
                '''若解析得到url只有后半部分，手动添加https'''
                if 'https' not in meta['href']:
                    url2Aceess = "https://www.zhihu.com" + meta['href']
                else:
                    url2Aceess = meta['href']

            ''' 针对爬取知乎制定了一系列url的过滤规则，
                如不可跳转到知乎外，不可跳转到用户界面等等，
                可自行修改'''
            if 'zhihu' not in url2Aceess:
                pass
            if 'topic' not in url2Aceess and 'question' not in url2Aceess and 'answer' not in url2Aceess:
                pass
            elif 'https' not in url2Aceess and 'http' in url2Aceess:
                pass
            elif 'people' in url2Aceess or 'static' in url2Aceess:
                pass
            elif 'javascript' in url2Aceess or 'licence' in url2Aceess:
                pass
            elif 'notification' in url2Aceess or 'contact' in url2Aceess:
                pass
            elif 'app' in url2Aceess or 'careers' in url2Aceess:
                pass
            elif 'jubao' in url2Aceess or 'terms' in url2Aceess:
                pass
            elif 'zhimg' in url2Aceess or 'comet' in url2Aceess:
                pass
            elif 'upload' in url2Aceess or 'unanswered' in url2Aceess:
                pass
            elif 'signin' in url2Aceess or 'signup' in url2Aceess:
                pass
            elif 'link' in url2Aceess or 'target' in url2Aceess:
                pass
            elif url2Aceess in urls:
                pass
            elif self.urlAlreadyAcessed(url2Aceess) == False:
                ''' 通过hash判断解析得到url是否访问过'''
                urls.append(url2Aceess)

        return urls

    def urlAlreadyAcessed(self, url):
        return self.filter.alreadyInHash(url)

    def crawlImages(self, URL, url, depth):
        if depth == 0:
            return
        else:
            html = self.downloadPage(URL, url)
            self.numOfURL += 1
            print("Having accessed %d urls" % self.numOfURL)
            self.downloadImage(url, html)

            '''下载完url中图片后将其加入hash中以表示访问过'''
            self.filter.addToHash(url)
            urlTemp = self.getURL(html)

            ''' 进行处理，优先访问话题下问题的url，
                而不是一直在话题之间跳转'''
            urls = []
            for url2Access in urlTemp:
                if 'question' in url2Access:
                    urlTemp.remove(url2Access)
                    urls.append(url2Access)
            for url2Access in urlTemp:
                urls.append(url2Access)

            for url2Access in urls:
                self.crawlImages(URL=url, url=url2Access, depth=(depth - 1))
                if self.numOfImg == 10000:
                    return



spider = ZhiHuCrawler('https://www.zhihu.com/topic/19551388')
spider.crawlImages("https://www.zhihu.com", spider.startURL, spider.depth)
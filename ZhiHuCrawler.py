# encode = "utf-8"

import time
import re
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import random
import os
import BloomFilter as bf


class ZhiHuCrawler:
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

    def getProxies(self):
        index = random.randint(0, self.numOfProxies - 1)
        print("采用第 %d 个代理HTTP" % (index + 1))
        self.proxies = self.listOfProxies[index]

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

    def execute_times(self, times, driver):
        for i in range(times + 1):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)

    def downloadPage(self, URL, url):
        self.headers['referer'] = URL
        accessFail = True
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

    def downloadImage(self, url, html):
        #html = self.dynamicDownloadPage(URL, url)
        soup = BeautifulSoup(html, "lxml")
        figures = soup.find_all("figure")
        urls = []
        for figure in figures:
            try:
                item = figure.img["data-original"]
            except:
                try:
                    item = figure.img['data-actualsrc']
                except:
                    try:
                        item = figure.img['src']
                    except:
                        regx1 = "https://[0-9a-zA-Z/_\.-]+\.jpg"
                        pattern = re.compile(regx1, re.S)
                        items = re.findall(pattern, figure.noscript.text)

            if item not in urls:
                urls.append(item)

        for imageURL in urls:
            if self.imageFilter.alreadyInHash(imageURL):
                print("Picture from %s having been downloaded" % imageURL)
                pass
            elif imageURL[-3:] == 'gif':
                pass
            else:
                self.imageFilter.addToHash(imageURL)
                print("Downloading image from %s" % imageURL)
                self.headers['referer'] = url
                image = requests.get(imageURL, headers=self.headers)
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

    def getURL(self, html):
        #html = self.dynamicDownloadPage(URL, url)
        urls = []
        soup = BeautifulSoup(html, "lxml")
        metas = soup.find_all(href=re.compile('[0-9a-zA-Z\.\-_]{1,}'))
        for meta in metas:
            try:
                url2Aceess = meta['content']
            except:
                if 'http' not in meta['href']:
                    url2Aceess = "https://www.zhihu.com" + meta['href']
                else:
                    url2Aceess = meta['href']
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
            self.filter.addToHash(url)
            urlTemp = self.getURL(html)
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
#spider.downloadImage("https://www.zhihu.com", spider.startURL)
'''html = spider.downloadPage('https://www.zhihu.com', spider.startURL)
soup = BeautifulSoup(html, "lxml")
#print(soup.prettify())
metas = soup.find_all(href=re.compile('[0-9a-zA-Z_\-\./]{1,}'))
for meta in metas:
    print(meta)
urls = spider.getURL(html)
for url in urls:
    print(url)'''
#spider.downloadImage("https://www.zhihu.com", spider.startURL)
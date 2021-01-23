# -*- coding:utf-8 -*-

"""
TODO：可以尝试实现其他网站的访问。
"""

import time
import requests
from bs4 import BeautifulSoup
import base64
import os
import json
import sys
from tkinter import messagebox, Tk


def write_cache(filename, cache={}, mode='w'):
    """
    将metainfo写入cache文件

    :param filename: str cache文件名
    :param cache: dict 一个metainfo字典
    :param mode: str 模式，默认覆写模式
    :return: 无
    """
    with open(filename, mode) as f:
        f.write(json.dumps(cache))


def read_cache(filename):
    """
    读取cache文件。

    :param filename: str cache文件名
    :return: dict
    """

    cache = {}
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            raw = f.read()
        if raw:
            cache = json.loads(raw)
    else:
        with open(filename, mode='w', encoding='utf-8') as f:
            f.write(json.dumps(cache))
    return cache

def get_inventory(label):
    """
    获取指定label文件夹下所有文件的文件名

    :param label: str 标签，即文件夹名
    :return: list 文件名列表
    """
    path = './' + label
    if not os.path.isdir(path):
        return []
    for dir_path, subpaths, files in os.walk(path):
        return files


def get_jandan(target_page):
    """
    从jandan.net的某图版获取某页所有图片链接

    :param target_page: 页面链接地址
    :return: list 其中链接为list，当前页数为int
    """

    headers = {'User-Agent': get_local_fake_useragent()}
    r = requests.get(target_page, headers=headers)
    r_bs = BeautifulSoup(r.text, features='lxml')
    pic_items = r_bs.select('div > div > div.text > p > a')
    pic_links = ['http:' + x['href'] for x in pic_items]

    try:
        current_page = r_bs.find('span', class_='current-comment-page').string
        current_page = int(current_page[1:-1])
    except Exception:
        current_page = 0
    return [pic_links, current_page]


def get_jandan_next_page(current_page):
    """
    从当前页码int推出下一页（其实是上一页）的地址
    eg  http://jandan.net/zoo/MjAyMTAxMTgtMTE=#comments
        a = MjAyMTAxMTgtMTE=#comments

    :param current_page: int
    :return: str
    """
    #
    # 如果没有下一页，返回''
    if current_page > 1:
        current_page -= 1
    else:
        raise Exception('No more pages today.')
    a = time.strftime('%Y%m%d')
    a = a + '-' + str(current_page)
    a = base64.b64encode(a.encode('utf8')).decode() + '#comments'
    return a


def check(links, inventory):
    """
    检查给定的文件链接列表是否已经存在于inventory列表中，并返回不存在其中的links

    :param links: 链接列表
    :param inventory: 文件名列表
    :return: new_links
    """
    names = [x.split('/')[-1] for x in links]
    new_links = []
    for i in range(len(names)):
        if names[i] not in inventory:
            new_links.append(links[i])
    return new_links


# 下载:给定链接和文件名
def download(url, direc='.', filename=None, headers=None):
    """
    从url下载文件到direc，可以指定文件名为filename，可以指定下载时使用的http头
    """
    from os import makedirs, getcwd, path
    direc = path.join(getcwd(), direc.strip('"'))
    if not path.exists(direc):
        makedirs(direc)

    if not filename:
        filename = url.split('/')[-1]
    else:
        ext = url.split('.')[-1]
        if filename.split('.')[-1] != ext:
            filename += '.' + ext

    if not headers:
        # ua = UserAgent()
        # headers = {'User-Agent': ua.random}
        headers = {'User-Agent': get_local_fake_useragent()}

    filename = path.join(direc, filename)
    with requests.get(url=url, headers=headers) as r:
        with open(filename, 'wb+') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    f.flush()
    return filename


def get_local_fake_useragent():
    """
    避免使用fake_useragent可能引起的网络连接延迟问题（？）
    :return:
    """
    a = ['Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2224.3 Safari/537.36',
         'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/534.55.3 (KHTML, like Gecko) Version/5.1.3 Safari/534.53.10',
         'Mozilla/5.0 (Windows NT 6.4; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2225.0 Safari/537.36',
         'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; Media Center PC 6.0; InfoPath.3; MS-RTC LM 8; Zune 4.7',
         'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.137 Safari/4E423F',
         'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1623.0 Safari/537.36',
         'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1866.237 Safari/537.36',
         'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.2 Safari/537.36',
         'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36',
         'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1468.0 Safari/537.36',
         'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1664.3 Safari/537.36',
         'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.14 (KHTML, like Gecko) Chrome/24.0.1292.0 Safari/537.14',
         'Mozilla/5.0 (Windows NT 5.1; rv:21.0) Gecko/20130401 Firefox/21.0',
         'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36',
         'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36',
         'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36',
         'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.2117.157 Safari/537.36',
         'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2226.0 Safari/537.36',
         'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0)  Gecko/20100101 Firefox/18.0',
         'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1468.0 Safari/537.36',
         'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
         'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36',
         'Mozilla/5.0 (Windows NT 6.4; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2225.0 Safari/537.36',
         'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2224.3 Safari/537.36',
         'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.60 Safari/537.17',
         'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36',
         'Opera/9.80 (X11; Linux i686; U; it) Presto/2.7.62 Version/11.00',
         'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/21.0.1',
         'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36',
         'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36',
         'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2226.0 Safari/537.36',
         'Mozilla/5.0 (Windows; U; Windows NT 5.1; ru-RU) AppleWebKit/533.19.4 (KHTML, like Gecko) Version/5.0.3 Safari/533.19.4',
         'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1944.0 Safari/537.36',
         'Mozilla/5.0 (X11; CrOS i686 4319.74.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.57 Safari/537.36',
         'Mozilla/5.0 (X11; OpenBSD amd64; rv:28.0) Gecko/20100101 Firefox/28.0',
         'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36',
         'Mozilla/5.0 (Windows NT 6.4; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2225.0 Safari/537.36',
         'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2225.0 Safari/537.36',
         'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1309.0 Safari/537.17',
         'Mozilla/5.0 (X11; OpenBSD i386) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36',
         'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1464.0 Safari/537.36',
         'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
         'Mozilla/5.0 (Windows NT 6.4; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2225.0 Safari/537.36',
         'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36',
         'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1944.0 Safari/537.36',
         'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1664.3 Safari/537.36',
         'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36',
         'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2225.0 Safari/537.36',
         'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36',
         'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36']
    i = int(time.time() * 1000) % len(a)
    return a[i]


def main(args=None):
    """
    运行一次

    :param args: 可控参数，待定义
    :return:
    """

    label = 'zoo'
    if args:
        label = args

    cache_file = 'randpic.json'

    # 先用缓存链接
    cache = read_cache(cache_file)
    if cache and (label in cache.keys()) and cache[label] != []:
        target = cache[label].pop()
        write_cache(cache_file, cache)
        file = download(target, direc=label)
        return file

    # 如果cache里没有可用的链接，就get一批
    home = 'http://jandan.net/' + label
    [pic_links, current_page] = get_jandan(home)

    # 检查重复
    inventory = get_inventory(label)
    pic_links = check(pic_links, inventory)

    # 如果这批都已下载了
    while not pic_links:
        try:
            next_page = get_jandan_next_page(current_page)
        except Exception:
            # 页面都抓完了就会返回None
            return None
        [pic_links, current_page] = get_jandan(home + '/' + next_page)
        pic_links = check(pic_links, inventory)

    # 终于找到了至少一个新链接
    target = pic_links.pop()
    file = download(target, direc=label)
    if label not in cache.keys():
        cache[label] = pic_links
    else:
        cache[label].extend(pic_links)
    write_cache(cache_file, cache)

    return file


if __name__ == '__main__':
    arg = None
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        vaild_label = ['zoo', 'ooxx', 'pic', 'top']
        if arg not in vaild_label:
            arg = None
    file = main(arg)
    if file:
        os.startfile(file)
    else:
        root = Tk()
        root.withdraw()
        messagebox.showinfo('randpic', '已经...没有更多了\n明天再来看吧')

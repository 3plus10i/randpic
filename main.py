# -*- coding:utf-8 -*-

"""
TODO：可以尝试实现其他网站的访问。
"""

import time
import requests
from bs4 import BeautifulSoup
# from fake_useragent import UserAgent
import base64
import os
import json
import sys


def metainfo_dict(url='', label='', downloaded=False, page_num=None):
    """
    将元信息组装成dict

    :param url: str 链接
    :param label: str 文件所属的类别标签
    :param downloaded: bool 是否已下载
    :param page_num: int 下载时所在的页数
    :return: dict metainfo字典
    """
    """
    example_data = {
        'time_stamp': 1611071754,
        'date': '20210118',
        'filename': r'007uWeI8ly1gms62b4278j30u00u0abu.jpg',
        'url': r'http://wx3.sinaimg.cn/large/007uWeI8ly1gms62b4278j30u00u0abu.jpg',
        'label': 'zoo'
        'downloaded': True,
        'page_num': 13,
        'page_base64': 'MjAyMTAxMTgtMTE='
    }
    """
    data = {
        'time_stamp': int(time.time() * 10000000),
        'data': time.strftime('%Y%m%d'),
        'filename': url.split('/')[-1],
        'url': url,
        'label': label,
        'downloaded': downloaded,
        'page_num': page_num
    }
    if page_num:
        a = time.strftime('%Y%m%d')
        a = a + '-' + str(page_num)
        a = base64.b64encode(a.encode('utf8')).decode()
        data['page_base64'] = a
    else:
        data['page_base64'] = None
    return data


def write_log(filename, data, mode='w'):
    """
    将metainfo写入log文件

    :param filename: str log文件名
    :param data: list|dict 一个metainfo字典或多个metainfo字典组成的列表
    :param mode: str 模式，默认覆写模式
    :return: 无
    """
    with open(filename, mode) as f:
        if isinstance(data, list):
            for x in data:
                f.write(json.dumps(x) + '\n')
        else:
            f.write(json.dumps(data) + '\n')


def append_log(filename, data):
    """
    追加若干metainfo到log文件

    :param filename: str log文件名
    :param data: list|dict 一个metainfo字典或多个metainfo字典组成的列表
    :return: 无
    """
    write_log(filename, data, mode='a+')


def read_log(filename):
    """
    读取log文件。在log过大时还会执行删除操作

    :param filename: str log文件名
    :return: 由metainfo字典组成的list
    """
    data = []
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            raw = f.readlines()
            if raw:
                data = [json.loads(x) for x in raw]
        new_data = flush_log(data)  # 检查log文件的大小，如果记录过多则删除若干最陈旧的记录
        if new_data:
            write_log(filename, new_data)
            data = new_data
    return data


def flush_log(data, max_num=200):
    """
    检查log记录，如果条数过多则删除若干最陈旧的数据
    最陈旧的数据浮于上方
    这里如果考虑不同label的影响就太复杂了。没必要。直接删除前n-N条。

    :return:无
    """
    new_data = []
    if len(data) > max_num:
        new_data = data[len(data) - max_num:]
    return new_data


def get_jandan(target_page):
    """
    从jandan.net的某图版获取某页所有图片链接

    :param target_page: 页面链接地址
    :return: list 其中链接为list，当前页数为int
    """
    # http://jandan.net/zoo

    # ua = UserAgent()
    # headers = {'User-Agent': ua.random}
    headers = {'User-Agent': get_local_fake_useragent()}
    r = requests.get(target_page, headers=headers)
    r_bs = BeautifulSoup(r.text, features='lxml')
    pic_items = r_bs.select('div > div > div.text > p > a')
    pic_links = ['http:' + x['href'] for x in pic_items]

    current_page = r_bs.find('span', class_='current-comment-page').string
    current_page = str(current_page)
    current_page = current_page.replace('[', '')
    current_page = current_page.replace(']', '')
    current_page = int(current_page)

    return [pic_links, current_page]


def get_jandan_next_page(current_page):
    # 从当前页码int推出下一页（其实是上一页）的地址
    # eg  http://jandan.net/zoo/MjAyMTAxMTgtMTE=#comments
    #     a = MjAyMTAxMTgtMTE=#comments
    # 如果没有下一页，返回‘’
    if current_page > 1:
        current_page -= 1
    else:
        raise Exception('No more pages today.')
        # return ''
    a = time.strftime('%Y%m%d')
    a = a + '-' + str(current_page)
    a = base64.b64encode(a.encode('utf8')).decode() + '#comments'
    return a


def check(links, data):
    """
    检查给定的链接列表是否已经存在于metainfo中，并返回不存在其中的links

    :param links: 链接列表
    :param data: metainfo元信息列表
    :return: new_links
    """
    data_urls = [x['url'] for x in data]
    new_links = []
    for x in links:
        if x not in data_urls:
            new_links.append(x)
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
    return os.path.join(direc, filename)


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
    i = int(time.time()*1000) % len(a)
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

    log = 'randpic.json'
    # 先从记录里找可用的链接
    data = read_log(log)
    if data:
        for i in range(len(data)):
            x = data[i]
            if x['label'] == label:
                if not x['downloaded']:
                    data[i]['downloaded'] = True
                    write_log(log, data)
                    target = x['url']
                    file = download(target, direc='./' + label)
                    return file

    # 如果data里没有可用的链接
    home = 'http://jandan.net/' + label
    [pic_links, current_page] = get_jandan(home)
    pic_links = check(pic_links, data)
    while not pic_links:
        try:
            next_ = get_jandan_next_page(current_page)
        except Exception:
            print('No more today')
            time.sleep(2)
            return None
        [pic_links, current_page] = get_jandan(home + '/' + next_)
        pic_links = check(pic_links, data)
    # 终于找到了至少一个新链接
    target = pic_links[0]
    file = download(target, direc='./' + label)
    new_data = metainfo_dict(pic_links[0], label=label, downloaded=True, page_num=current_page)
    data.append(new_data)
    if len(pic_links) > 1:
        for x in pic_links[1:]:
            new_data = metainfo_dict(x, label=label, downloaded=False, page_num=current_page)
            data.append(new_data)
    write_log(log, data)
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

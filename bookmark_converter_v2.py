import argparse
import logging
import os
import re
import sys
import signal
import string
import time

from io import BytesIO
from urllib.parse import urlparse

import base64
import chardet
import concurrent.futures
import requests

from bs4 import BeautifulSoup
from PIL import Image
from pyfiglet import Figlet

# 程序配置
OUTPUT_DIR = "output/images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 系统默认转义字符集
escape_chars = re.escape(string.punctuation)

# 配置日志记录
logging.basicConfig(level=logging.INFO, filename='output/error.txt', filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 数据处理相关常量
ITEM_PATTERN = '<A.*?<\/A>'
URL_PATTERN = r'<A\s+HREF="(.*?)"'
ICON_PATTERN = r'ICON="data:image\/png;base64,([^"]+)"'
TITLE_PATTERN = r'<A[^>]+>([^<]+)</A>'
DEFAULT_ICON_FILE = 'assets/globe.png'

# 用户配置
MAX_WORKERS = 8  # 设置最大线程数

# 网站图标尺寸设置
IMAGE_WIDTH = 32
IMAGE_HEIGHT = 32

# 并发处理的终止标志符
running = True


def on_signal(signum, frame):
    global running
    running = False


def get_default_icon():
    with open(DEFAULT_ICON_FILE, 'rb') as file:
        icon_data = file.read()
    icon = base64.b64encode(icon_data).decode('utf-8').replace('\n', '')
    return icon


def is_valid_protocol(item):
    url = ''.join(re.findall(URL_PATTERN, item))
    parsed_url = urlparse(url)
    protocol = parsed_url.scheme
    return protocol in ['http', 'https']


def extract_data(text):
    item_text = re.findall(ITEM_PATTERN, text)

    result = {
        i: {
            'url': ''.join(re.findall(URL_PATTERN, item)),
            'icon': ''.join(re.findall(ICON_PATTERN, item)) or get_default_icon(),
            # 'title': ''.join(re.findall(TITLE_PATTERN, item))

            # 添加字符转义
            'title': re.sub(f"[{escape_chars}]", lambda x: "\\" + x.group(0), ''.join(re.findall(TITLE_PATTERN, item)))
        }
        for i, item in enumerate(item_text)
        if is_valid_protocol(item)
    }

    return result


def process_url(url, icon, title, output_dir, silent_mode, proxy, username=None, password=None):
    try:
        # 根据标题生成文件名
        parsed_url = urlparse(url)
        file_name = parsed_url.netloc
        file_name = file_name.replace(".", "_")  # 替换点为下划线
        file_name = re.sub(r'^_+', '', file_name)  # 去除开头的下划线
        file_name = re.sub(r'\W+', '', file_name)  # 去除特殊符号

        # 统一输出路径的斜杠，支持不同系统下的不同路径格式
        output_dir = output_dir.replace("\\", "/")

        # 将base64编码解码为字节数据
        image_data = base64.b64decode(icon)

        # 打开图像
        image = Image.open(BytesIO(image_data))

        # 调整图像尺寸
        resized_image = image.resize(
            (IMAGE_WIDTH, IMAGE_HEIGHT), resample=Image.LANCZOS)

        # 保存图像到指定路径
        save_path = os.path.join(output_dir, f"{file_name}.png")
        resized_image.save(save_path)

        # 发送 GET 请求获取页面内容
        proxies = {
            'http': proxy,
            'https': proxy
        }

        if proxy.startswith('socks'):
            proxies['http'] = 'socks5h://' + proxy[len('socks5://'):]
            proxies['https'] = 'socks5h://' + proxy[len('socks5://'):]

        response = requests.get(url, proxies=proxies,
                                timeout=10, auth=(username, password))
        encoding = chardet.detect(response.content)['encoding']

        if encoding is None:
            encoding = 'utf-8'  # 使用默认编码作为备选方案

        response.encoding = encoding
        soup = BeautifulSoup(response.text, 'html.parser')

        # 提取 <head> 中的 <meta> 标签
        meta_tags = soup.find_all('meta')

        # 提取描述（description）
        description = ''
        newline = os.linesep
        for tag in meta_tags:
            if 'name' in tag.attrs and tag.attrs['name'].lower() == 'description':
                description = tag.attrs['content']
                if len(description) > 30:
                    description = description[:30] + "..."
                description = description.replace("\r\n", newline).replace(
                    "\n", newline).replace("\r", newline)
                description = re.sub(
                    f"[{escape_chars}]", lambda x: "\\" + x.group(0), description)
                break

        # 输出到终端
        if not silent_mode:
            print(f"  name: \"{title}\"")
            print(f"  url: {url}")
            print(f"  img: /images/logos/{file_name}.png")
            print(f"  description: \"{description}\"\n")

        # 写入结果到文件
        time.sleep(0.1)
        with open('output/result.txt', 'a', encoding='utf-8', buffering=1024) as output_file:
            output_file.write(f"- name: \"{title}\"\n")
            output_file.write(f"  url: {url}\n")
            output_file.write(f"  img: /images/logos/{file_name}.png\n")
            output_file.write(f"  description: \"{description}\"\n")

    except Exception as e:
        # 如果发生异常，将异常信息写入日志
        logging.error(str(e))


def main(file_name, silent_mode, proxy, username=None, password=None):
    with open(file_name, "r", encoding="utf-8") as file:
        content = file.read()

    data = extract_data(content)

    # 注册中止信号处理程序
    signal.signal(signal.SIGINT, on_signal)

    # 并发处理所有URL
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 将每个URL提交给线程池处理
        futures = [
            executor.submit(process_url, data[i]['url'], data[i]['icon'], data[i]
                            ['title'], OUTPUT_DIR, silent_mode, proxy, username, password)
            for i in data.keys()
        ]

        # 迭代访问已完成的任务，同时检查中止标志
        # 设置超时时间为600秒
        for future in concurrent.futures.as_completed(futures, timeout=600):
            if not running:
                executor.shutdown(wait=False)  # 终止线程池中正在运行的任务
                sys.exit()
            try:
                future.result()  # 获取任务的结果，检查是否有异常
            except Exception as e:
                logging.error(f"Error occurred: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="处理书签文件", add_help=False)
    parser.add_argument("file_name", type=str, nargs="?",
                        default="", help="要处理的书签文件名")
    parser.add_argument("-h", "--help", action="store_true", help="显示帮助文档")
    parser.add_argument(
        "-s", "--silent", action="store_true", help="静默模式，不将信息输出到终端")
    parser.add_argument("-p", "--proxy", type=str, default="",
                        help="指定代理服务器，格式：[SCHEME://]PROXY:PORT [USERNAME] [PASSWORD]（不填写协议则默认为socks5）")
    args = parser.parse_args()

    if args.file_name == "":
        # 输出ASCII艺术标题
        f = Figlet(font='slant')
        print(f.renderText('Bookmark Converter'))
        parser.print_help()
        sys.exit()

    if not os.path.isfile(args.file_name):
        print("文件不存在！")
        sys.exit(1)

    if args.proxy and "://" not in args.proxy:
        # 如果代理服务器协议为空，并且没有指定协议，则默认使用 SOCKS 协议
        args.proxy = f"socks5://{args.proxy}"

    proxy = args.proxy.split(" ")
    proxy_address = proxy[0]
    username = None
    password = None

    if len(proxy) >= 3:
        username = proxy[1]
        password = proxy[2]

    main(args.file_name, args.silent, proxy_address, username, password)

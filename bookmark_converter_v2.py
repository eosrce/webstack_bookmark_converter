import argparse
import logging
import os
import re
import csv
import sys
import signal
import shutil
import concurrent.futures
import requests
import base64
import chardet
import tempfile

from io import BytesIO
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from PIL import Image
from pyfiglet import Figlet
from enum import Enum

# 输出目录配置
OUTPUT_DIR = "output"
IMAGES_DIR = "/images/logos"

# 数据处理相关常量
ITEM_PATTERN = '<A.*?<\/A>'
URL_PATTERN = r'<A\s+HREF="(.*?)"'
ICON_PATTERN = r'ICON="data:image\/png;base64,([^"]+)"'
TITLE_PATTERN = r'<A[^>]+>([^<]+)</A>'
DEFAULT_ICON_FILE = 'assets/globe.png'

# 导出文件设置
CSV_HEADER = ['name', 'url', 'img', 'description']
GLOBAL_ENCODING = 'utf-8'

# 用户配置
MAX_WORKERS = 8  # 设置最大线程数

# 网站图标尺寸设置
IMAGE_WIDTH = 32
IMAGE_HEIGHT = 32

# 临时文件输出
global_temp_file = None

# 导出模式
# 0 txt
# 1 csv
export_mode = 0

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
            'title': ''.join(re.findall(TITLE_PATTERN, item))
        }
        for i, item in enumerate(item_text)
        if is_valid_protocol(item)
    }

    return result


def export_to_output(data):
    export_functions = {
        0: (export_to_text, "txt"),
        1: (export_to_csv, "csv"),
        2: (export_to_yaml, "yaml"),
        3: (export_to_template, "yaml")
    }

    if export_mode in export_functions:
        export_function, file_extension = export_functions[export_mode]

        if export_mode == 3:
            template_name = "assets/_config.example.yml"
            file_name = f"{OUTPUT_DIR}/webstack.{file_extension}"
            export_function(data, file_name, template_name)
        else:
            file_name = f"{OUTPUT_DIR}/result.{file_extension}"
            export_function(data, file_name)
    else:
        print("导出错误。")
        sys.exit(1)


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

        # 创建临时文件
        create_temp_file()
        if global_temp_file:
            # 保存网页内容到临时文件
            global_temp_file.write(response.text)
            global_temp_file.seek(0)

            # 打开临时文件，并将文件句柄传递给BeautifulSoup
            with open(global_temp_file.name, 'r') as file:
                soup = read_temp_file(file.name)

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
                break

        data = {
            'name': title,
            'url': url,
            'img': f"{IMAGES_DIR}/{file_name}.png",
            'description': description
        }

        export_to_output(data)

        # 输出到终端
        if not silent_mode:
            print(f"  name: \"{data['name']}\"")
            print(f"  url: {data['url']}")
            print(f"  img: {data['img']}")
            print(f"  description: \"{data['description']}\"\n")

    except Exception as e:
        # 如果发生异常，将异常信息写入文件
        with open(f"{OUTPUT_DIR}/error.txt", 'a', encoding='utf-8') as error_file:
            error_file.write(f"- name: \"{title}\"\n")
            error_file.write(f"  url: {url}\n")
            error_file.write(f"  img: {IMAGES_DIR}/{file_name}.png\n")
            error_file.write(f"  error: \"{str(e)}\"\n")


def process_data(file_name, silent_mode, proxy, username=None, password=None):
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
                            ['title'], OUTPUT_DIR + IMAGES_DIR, silent_mode, proxy, username, password)
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

    logging.info(f"任务完成。")


def export_to_csv(data, file_name, custom_header=CSV_HEADER):
    # 检查文件是否为空
    is_file_empty = not os.path.exists(
        file_name) or os.path.getsize(file_name) == 0

    # 转换数据类型为列表
    data = [data]

    # 写入数据
    with open(file_name, 'a', newline="", buffering=1024) as csvfile:
        # 创建写入器对象
        writer = csv.writer(csvfile)

        # 写入表头
        if is_file_empty:
            writer.writerow(custom_header)

        # 写入数据
        for item in data:
            row = [item.get(key, '') for key in custom_header]
            writer.writerow(row)


def export_to_text(data, file_name):
    with open(file_name, 'a', encoding='utf-8', buffering=1024) as textfile:
        # textfile.write(f"- name: \"{data['name']}\"\n")
        # textfile.write(f"  description: \"{data['description']}\"\n")

        # 输出时转义双引号
        textfile.write(
            "-  name: \"{}\"\n".format(data['name'].replace('"', '\\"')))
        textfile.write(f"  url: {data['url']}\n")
        textfile.write(f"  img: {data['img']}\n")
        textfile.write("  description: \"{}\"\n".format(
            data['description'].replace('"', '\\"')))


def export_to_yaml(data, file_name):
    with open(file_name, 'a', encoding='utf-8', buffering=1024) as textfile:
        # textfile.write(f"- name: \"{data['name']}\"\n")
        # textfile.write(f"  description: \"{data['description']}\"\n")

        # 输出时转义双引号
        textfile.write(
            "  -  name: \"{}\"\n".format(data['name'].replace('"', '\\"')))
        textfile.write(f"    url: {data['url']}\n")
        textfile.write(f"    img: {data['img']}\n")
        textfile.write("    description: \"{}\"\n".format(
            data['description'].replace('"', '\\"')))


def generate_templates(template_name):
    with open(template_name, 'r', encoding='utf-8') as template:
        ''


def export_to_template(data, file_name):
    with open(file_name, 'a', encoding='utf-8', buffering=1024) as textfile:
        if "bookmark_converter:":
            # 输出时转义双引号
            textfile.write(
                "  -  name: \"{}\"\n".format(data['name'].replace('"', '\\"')))
            textfile.write(f"    url: {data['url']}\n")
            textfile.write(f"    img: {data['img']}\n")
            textfile.write("    description: \"{}\"\n".format(
                data['description'].replace('"', '\\"')))


def remove_existing_files():
    # 检查并删除images/logos文件夹
    if os.path.exists("output"):
        shutil.rmtree("output")


def create_temp_file():
    global global_temp_file
    global_temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8')


def close_temp_file():
    global global_temp_file
    if global_temp_file:
        global_temp_file.close()
        global_temp_file = None


def read_temp_file(temp_file_path):
    try:
        with open(temp_file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
            return soup
    except IOError as e:
        print(f"Error while reading the file: {e}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="处理书签文件", add_help=False)
    parser.add_argument("file_name", type=str, nargs="?",
                        default="", help="要处理的书签文件名")
    parser.add_argument("-o", "--output", type=str, default='txt',
                        help="输出的文件格式，目前支持 txt，csv，yml")
    parser.add_argument("-h", "--help", action="store_true", help="显示帮助文档")
    parser.add_argument(
        "-s", "--silent", action="store_true", help="静默模式，不将信息输出到终端")
    parser.add_argument("-p", "--proxy", type=str, default="",
                        help="指定代理服务器，格式：[SCHEME://]PROXY:PORT [USERNAME] [PASSWORD]（不填写协议则默认为socks5）")
    parser.add_argument("-k", "--keep", action="store_true",
                        help="保留上一次的结果")
    parser.add_argument("-t", "--template", action="store_true",
                        help="输出 Webstack Hexo 版本配置文件，模板文件为assets/_config.example.yml")
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

    if args.output == 'txt':
        export_mode = 0
    elif args.output == 'csv':
        export_mode = 1
    elif args.output == 'yaml':
        export_mode = 2
    else:
        print("不支持的文件类型。")
        sys.exit(1)

    if args.output and args.template:
        print("请勿同时指定 -o 和 -t 参数")
        sys.exit(1)

    elif not args.output and args.template:
        # 生成模板文件到 output 文件夹下
        export_mode = 3
        generate_templates()

    if args.proxy and "://" not in args.proxy:
        # 如果代理服务器协议为空，并且没有指定协议，则默认使用 SOCKS 协议
        args.proxy = f"socks5://{args.proxy}"

    if args.help:
        parser.print_help()
        sys.exit(0)

    if not args.keep:
        remove_existing_files()

    proxy = args.proxy.split(" ")
    proxy_address = proxy[0]
    username = None
    password = None

    if len(proxy) >= 3:
        username = proxy[1]
        password = proxy[2]

    # 创建输出目录
    os.makedirs(OUTPUT_DIR + IMAGES_DIR, exist_ok=True)

    # 配置日志记录
    logging.basicConfig(level=logging.INFO, filename=f"{OUTPUT_DIR}/log.txt",
                        filemode='a', format='%(asctime)s - %(levelname)s - %(message)s')

    # 数据处理部分
    process_data(args.file_name, args.silent,
                 proxy_address, username, password)

    print("程序运行结束。")

    # 解析完成后删除临时文件
    close_temp_file()

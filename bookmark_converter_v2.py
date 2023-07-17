import re
import os
import base64
import requests
from PIL import Image
from io import BytesIO
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import sys
import concurrent.futures
import chardet
import keyboard
import argparse
import logging
from pyfiglet import Figlet

# 创建保存图像的文件夹
OUTPUT_DIR = "output/images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 配置日志记录
logging.basicConfig(level=logging.INFO, filename='output/log.txt', filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 定义一个全局标志变量，用于控制并发处理的终止
running = True


def on_hotkey(event):
    global running
    logging.info('中止并发处理和脚本')
    running = False


def extract_data(text):
    # 提取base64编码和A链接的标题
    base64_pattern = r'ICON="data:image\/png;base64,([^"]+)"'
    base64_matches = re.findall(base64_pattern, text)
    base64_codes = [match for match in base64_matches]

    title_pattern = r'<DT><A[^>]+>([^<]+)</A>'
    title_matches = re.findall(title_pattern, text)
    titles = [match for match in title_matches]

    return base64_codes, titles


def process_url(url, title, base64_code, output_dir, output_to_terminal, socks5_proxy):
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
        image_data = base64.b64decode(base64_code)

        # 打开图像
        image = Image.open(BytesIO(image_data))
        # 保存图像到指定路径
        save_path = os.path.join(output_dir, f"{file_name}.png")
        image.save(save_path)

        # 发送 GET 请求获取页面内容
        proxies = {
            'http': 'socks5://' + socks5_proxy,
            'https': 'socks5://' + socks5_proxy
        }

        response = requests.get(url, proxies=proxies, timeout=10)
        encoding = chardet.detect(response.content)['encoding']

        if encoding is None:
            encoding = 'utf-8'  # 使用默认编码作为备选方案

        response.encoding = encoding
        soup = BeautifulSoup(response.text, 'html.parser')

        # 提取 <head> 中的 <meta> 标签
        meta_tags = soup.find_all('meta')

        # 提取描述（description）
        description = ''
        for tag in meta_tags:
            if 'name' in tag.attrs and tag.attrs['name'].lower() == 'description':
                description = tag.attrs['content'].encode('utf-8')  # 先将字节对象解码为字符串对象
                description = description.decode('utf-8').replace("\n", "")  # 解码后按照字符串处理
                if len(description) > 30:
                    description = description[:30] + "..."
                break

        # # 将描述信息编码为utf-8并解码为字符串
        description = description.encode('utf-8', errors='ignore').decode('utf-8')

        # 输出到终端和日志
        if output_to_terminal:
            print(f"- name: '{title}'")
            print(f"  url: {url}")
            print(f"  img: /images/logos/{file_name}.png")
            print(f"  description: '{description}'")

        logging.info(f"- name: '{title}'")
        logging.info(f"  url: {url}")
        logging.info(f"  img: /images/logos/{file_name}.png")
        logging.info(f"  description: '{description}'")

        # 写入结果到文件
        with open('output/result.txt', 'a', encoding='utf-8') as output_file:
            output_file.write(f"- name: '{title}'\n")
            output_file.write(f"  url: {url}\n")
            output_file.write(f"  img: /images/logos/{file_name}.png\n")
            output_file.write(f"  description: '{description}'\n")

    except Exception as e:
        # 如果发生异常，将异常信息写入文件和日志
        logging.error(f"- name: '{title}'")
        logging.error(f"  url: {url}")
        logging.error(f"  img: /images/logos/{file_name}.png")
        logging.error(f"  error: '{str(e)}'")

        with open('output/error.txt', 'a', encoding='utf-8') as error_file:
            error_file.write(f"- name: '{title}'\n")
            error_file.write(f"  url: {url}\n")
            error_file.write(f"  img: /images/logos/{file_name}.png\n")
            error_file.write(f"  error: '{str(e)}'\n")


def main(file_name, output_to_terminal, socks5_proxy):
    with open(file_name, "r", encoding="utf-8") as file:
        content = file.read()

    # 使用正则表达式提取以'<A HREF="'开头的行
    bookmark_lines = re.findall(r'<A HREF="(.*?)"', content)

    # 过滤不符合条件的URL
    filtered_urls = [url for url in bookmark_lines if url.startswith(("http://", "https://"))]

    # 提取base64编码和A链接的标题
    base64_codes, titles = extract_data(content)

    # 并发处理所有URL
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # 将每个URL提交给线程池处理
        futures = [
            executor.submit(process_url, url, title, base64_code, OUTPUT_DIR, output_to_terminal, socks5_proxy)
            for url, title, base64_code in zip(filtered_urls, titles, base64_codes)
        ]

        # 注册中止热键事件
        keyboard.add_hotkey('ctrl+c', on_hotkey, args=('event',))  # 添加args参数来传递事件对象

        # 迭代访问已完成的任务，同时检查中止标志
        for future in concurrent.futures.as_completed(futures, timeout=600):  # 设置超时时间为600秒
            if not running:
                executor.shutdown(wait=False)  # 终止线程池中正在运行的任务
                break
            try:
                future.result()  # 获取任务的结果，检查是否有异常
            except Exception as e:
                logging.error(f"Error occurred: {str(e)}")

        # 停止监听键盘事件
        keyboard.unhook_all()

    logging.info("处理完成！")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="处理书签文件")
    parser.add_argument("file_name", type=str, nargs="?", default="", help="要处理的书签文件名")
    parser.add_argument("-o", "--output", action="store_true", help="输出到终端")
    parser.add_argument("-p", "--proxy", type=str, default="", help="指定代理服务器")
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

    main(args.file_name, args.output, args.proxy)
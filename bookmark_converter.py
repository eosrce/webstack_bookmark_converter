#!/usr/bin/python
import re
import os
import base64
import requests
from PIL import Image
from io import BytesIO
from pypinyin import lazy_pinyin
from unidecode import unidecode
from bs4 import BeautifulSoup
import sys
import concurrent.futures

# 可配置的socks5服务器代理
SOCKS5_PROXY = ''

def extract_data(text):
    # 提取base64编码
    base64_pattern = r'ICON="data:image\/png;base64,([^"]+)"'
    base64_matches = re.findall(base64_pattern, text)
    base64_codes = [match for match in base64_matches]

    # 提取A链接的标题
    title_pattern = r'<DT><A[^>]+>([^<]+)</A>'
    title_matches = re.findall(title_pattern, text)
    titles = [match for match in title_matches]
    
    return base64_codes, titles

# 获取命令行参数中的文件名
file_name = sys.argv[1] if len(sys.argv) > 1 else "input/example.txt"

with open(file_name, "r", encoding="utf-8") as file:
    content = file.read()

# 使用正则表达式提取以'<A HREF="'开头的行
bookmark_lines = re.findall(r'<A HREF="(.*?)"', content)

# 过滤不符合条件的URL
filtered_urls = [url for url in bookmark_lines if url.startswith(("http://", "https://"))]

# 提取base64编码和A链接的标题
base64_codes, titles = extract_data(content)

# 创建保存图像的文件夹
output_dir = "output/images"
os.makedirs(output_dir, exist_ok=True)


# 定义处理单个URL的函数
def process_url(url, title, base64_code, output_dir):
    try:
        # 根据标题生成文件名
        file_name = unidecode(title)  # 将中文转换为拼音
        file_name = file_name.replace(" ", "_")  # 替换空格为下划线
        file_name = re.sub(r'\W+', '', file_name)  # 去除特殊符号

        # 统一输出路径的斜杠，支持不同系统下的不同路径格式
        output_dir = output_dir.replace("\\", "/")

        # 控制下划线数量，确保文件名开头不是下划线开头
        num_underscores = min(2, len(file_name))  # 控制下划线最多出现2次
        file_name = re.sub(r'^_+', '', file_name)  # 去除开头的下划线
        file_name = re.sub(r'_+', '_'.ljust(num_underscores, '_'), file_name)  # 控制下划线数量

        # 将base64编码解码为字节数据
        image_data = base64.b64decode(base64_code)

        # 打开图像
        image = Image.open(BytesIO(image_data))
        # 保存图像到指定路径
        save_path = os.path.join(output_dir, f"{file_name}.png")
        image.save(save_path)

        # 发送 GET 请求获取页面内容
        proxies = {
            'http': SOCKS5_PROXY,
            'https': SOCKS5_PROXY
        }
        response = requests.get(url, proxies=proxies)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取 <head> 中的 <meta> 标签
        meta_tags = soup.find_all('meta')

        # 提取描述（description）
        description = ''
        for tag in meta_tags:
            if 'name' in tag.attrs and tag.attrs['name'].lower() == 'description':
                description = tag.attrs['content']
                break

        # 将描述信息编码为utf-8并解码为字符串
        description = description.encode('utf-8', errors='ignore').decode('utf-8')

        # 写入结果到文件
        with open('output/result.txt', 'a', encoding='utf-8') as output_file:
            output_file.write("- name: " + title + "\n")
            output_file.write("  url: " + url + "\n")
            output_file.write("  img: " + "/images/logos/" + file_name + ".png" + "\n")
            output_file.write("  description: " + description + "\n")

    except Exception as e:
        # 如果发生异常，将异常信息写入文件
        with open('output/error.txt', 'a', encoding='utf-8') as error_file:
            error_file.write("- name: " + title + "\n")
            error_file.write("  url: " + url + "\n")
            error_file.write("  img: " + "/images/logos/" + file_name + ".png" + "\n")
            error_file.write("  error: " + str(e) + "\n")

# 并发处理所有URL
with concurrent.futures.ThreadPoolExecutor() as executor:
    # 将每个URL提交给线程池处理
    futures = [executor.submit(process_url, url, title, base64_code, output_dir) for url, title, base64_code in zip(filtered_urls, titles, base64_codes)]

    # 迭代访问已完成的任务
    for future in concurrent.futures.as_completed(futures):
        try:
            future.result()  # 获取任务的结果，检查是否有异常
        except Exception as e:
            print(f"Error occurred: {str(e)}")

print("处理完成！")

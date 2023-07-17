# Webstack Bookmark Converter

## 介绍

这是一个完全使用 GPT 编写的 Python 脚本，用于将 Edge 浏览器导出的书签数据（HTML 格式）转换为 Webstack Hexo 版本可以直接使用的格式（YAML）。脚本具有以下功能：

1. 从给定的HTML文件中提取以`<A HREF="`开头的行，这些行包含书签URL。
2. 过滤不符合条件的URL，只保留以`http://`或`https://`开头的URL。
3. 提取HTML文件中的base64编码和A链接的标题。
4. 创建一个保存图像的输出文件夹。
5. 将提取的数据打印到一个结果文件中，并保存图片到指定路径。
6. 使用提取的URL发送GET请求，获取页面内容。
7. 使用BeautifulSoup库提取`<head>`中的`<meta>`标签。
8. 将提取的标题、URL、图像路径和描述写入结果文件。
9. 使用了并发。

请确保已安装所需的依赖项。运行命令如下：

```python
pip install -r requirements.txt
python .\bookmark_converter_v2.py
    ____              __                        __
   / __ )____  ____  / /______ ___  ____ ______/ /__
  / __  / __ \/ __ \/ //_/ __ `__ \/ __ `/ ___/ //_/
 / /_/ / /_/ / /_/ / ,< / / / / / / /_/ / /  / ,<
/_____/\____/\____/_/|_/_/ /_/ /_/\__,_/_/  /_/|_|

   ______                           __
  / ____/___  ____ _   _____  _____/ /____  _____
 / /   / __ \/ __ \ | / / _ \/ ___/ __/ _ \/ ___/
/ /___/ /_/ / / / / |/ /  __/ /  / /_/  __/ /
\____/\____/_/ /_/|___/\___/_/   \__/\___/_/


usage: bookmark_converter_v2.py [-h] [-o] [-p PROXY] [file_name]

处理书签文件

positional arguments:
  file_name             要处理的书签文件名

options:
  -h, --help            show this help message and exit
  -o, --output          输出到终端
  -p PROXY, --proxy PROXY
                        指定代理服务器
```

## 已知问题

- [x] 由于 YAML 格式的局限性，以及采集站点 description 会遇到各式各样的文本，需要再次处理；
  - [x] description 中的特殊符号需要转义，如`[`, `]`, `|`, `:`；
  - [x] description 中的内容需要删除多余换行，确保整段内容只占一行；
  - [x] description 中的内容应设定字数上限；
  - [] description 中的内容可能存在编码问题，仍需完善。
- [x] 网站图标根据站点标题进行拼音转写（中文情况下），将空格转换为下划线，最终会导致文件名过长，应该为使用域名作为名称。
- [ ] 从原始文件获取的数据时应使用字典存储，对数据源进行校验；
  - [ ] 图像获取机制存在 bug，如果站点没有图标则会导致顺序错乱；

## 来源项目

[HCLonely/hexo-theme-webstack: A hexo theme based on webstack. | 一个基于webstack的hexo主题。](https://github.com/HCLonely/hexo-theme-webstack/)

# Webstack Bookmark Converter

## 介绍

这是一个完全使用 GPT 编写的 Python 脚本，用于将 Edge 浏览器导出的书签数据（HTML 格式）转换为 Webstack Hexo 版本可以直接使用的格式（YAML）。脚本具有以下功能：

1. 从给定的 HTML 文件中提取以`<A HREF="`开头的行，这些行包含书签 URL。
2. 过滤不符合条件的 URL，只保留以`http://`或`https://`开头的 URL。
3. 提取 HTML 文件中的 base64 编码和 A 链接的标题。
4. 创建一个保存图像的输出文件夹。
5. 将提取的数据打印到一个结果文件中，并保存图片到指定路径。
6. 使用提取的 URL 发送 GET 请求，获取页面内容。
7. 使用 BeautifulSoup 库提取`<head>`中的`<meta>`标签。
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


usage: bookmark_converter_v2.py [-h] [-s] [-p PROXY] [file_name]

处理书签文件

positional arguments:
  file_name             要处理的书签文件名

options:
  -h, --help            显示帮助文档
  -s, --silent          静默模式，不将信息输出到终端
  -p PROXY, --proxy PROXY
                        指定代理服务器，格式：[SCHEME://]PROXY:PORT [USERNAME] [PASSWORD]（不填写协 议则默认为socks5）
```

## 已知问题

> 在下一次的提交后清除之前已经解决的

- [x] description 中的内容可能存在编码问题，仍需完善；
- [x] 从原始文件获取的数据时应使用字典存储，对数据源进行校验；
  - [x] 图像获取机制存在 bug，如果站点没有图标则会导致顺序错乱；
- [ ] 添加一个仅输出网站图标的选项，用于重设图标大小或图标获取失败时的重新尝试；
- [ ] 添加输出 csv 格式支持，计划初步支持导入数据分析软件进行可视化分析；
- [ ] 未在 Linux 环境下进行测试；
- [ ] 可能因速率过快或无严格校验，提取 description 时可能会错误提取额外一部分，造出最终结果出现偏差；

## 来源项目

[HCLonely/hexo-theme-webstack: A hexo theme based on webstack. | 一个基于 webstack 的 hexo 主题。](https://github.com/HCLonely/hexo-theme-webstack/)

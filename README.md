# Webstack Bookmark Converter

## 目录 Table to Contents

- [Webstack Bookmark Converter](#webstack-bookmark-converter)
  - [目录 Table to Contents](#目录-table-to-contents)
  - [介绍 Summary](#介绍-summary)
  - [功能 Features](#功能-features)
  - [使用方式 How to use](#使用方式-how-to-use)
  - [已知问题 Known issues](#已知问题-known-issues)
  - [开发计划 Development project](#开发计划-development-project)
  - [相关项目 Related Projects](#相关项目-related-projects)

## 介绍 Summary

这是一个完全使用 GPT 编写的 Python 脚本，用于将浏览器导出的书签数据（HTML 格式）转换为 Webstack Hexo 版本可以直接使用的格式（YAML）。脚本具有以下功能：

1. 从给源文件中提取以包含书签数据的条目。
2. 过滤不符合条件的 URL，只保留以`http://`或`https://`开头的书签。
3. 像网站发出 GET 请求，获取站点简介。
4. 使用 BeautifulSoup 库提取`<head>`中的`<meta>`标签。
5. 将提取的数据写入结果文件，可以直接复制到`webstack.yml`中使用。
6. 使用并发提高程序运行效率。

适合批量导入书签数据到 Webstack 的用户使用。

## 功能 Features

- 书签（收藏夹）数据导入到 Webstack。
- 支持 Webstack Hexo版本。
- 支持导出 csv 格式。
- 获取书签中站点的介绍文本（建议配合代理使用）。
- 根据书签中保存的站点图标的 Base64 数据还原成图标文件（但分辨率较低）。

## 使用方式 How to use

请确保已安装所需的依赖项。运行命令如下：

```python
# 安装依赖
cmd > pip install -r requirements.txt
cmd > python .\bookmark_converter_v2.py
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


usage: bookmark_converter_v2.py [-o OUTPUT] [-h] [-s] [-p PROXY] [-k] [-t] [file_name]

处理书签文件

positional arguments:
  file_name             要处理的书签文件名

options:
  -o OUTPUT, --output OUTPUT
                        输出的文件格式，目前支持 txt，csv，yml
  -h, --help            显示帮助文档
  -s, --silent          静默模式，不将信息输出到终端
  -p PROXY, --proxy PROXY
                        指定代理服务器，格式：[SCHEME://]PROXY:PORT [USERNAME] [PASSWORD]（不填写协议则默认为socks5）
  -k, --keep            保留上一次的结果
  -t, --template        输出 Webstack Hexo 版本配置文件，模板文件为assets/_config.example.yml
```

## 已知问题 Known issues

- [ ] 添加控制是否输出网站图标的功能。
- [ ] 提取`description`时可能存在问题。
- [ ] 数据的输出顺序存在 bug。
- [ ] 输出 CSV 格式有待优化。

## 开发计划 Development project

- [ ] 适配 Linux 系统环境。
- [ ] 通过第三方 API 获取站点图标。
- [ ] 添加参数选项，选择是否需要联网获取站点介绍。
- [ ] 生成 Webstack Hexo 版本能够直接使用的`webstack.yml`配置文件。

## 相关项目 Related Projects

[HCLonely/hexo-theme-webstack: A hexo theme based on webstack. | 一个基于 webstack 的 hexo 主题。](https://github.com/HCLonely/hexo-theme-webstack/)

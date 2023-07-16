# Webstack Bookmark Converter

## 介绍

> 一个使用 ChatGPT 3.5 编写的 Python 脚本，用于 Edge 导出书签到 hexo 版本的 Webstack 导航站中。包括这份 README 也是 GPT 自己生成的（耸肩）。
>
> 用法参照下方，不指定文件名时默认为 input/example.txt 的演示数据，也可以直接将 Edge 导出的内容复制粘贴进去。

这是一个Python脚本，用于从HTML文件中提取书签数据，并下载其中的图像。脚本具有以下功能：

1. 从给定的HTML文件中提取以`<A HREF="`开头的行，这些行包含书签URL。
2. 过滤不符合条件的URL，只保留以`http://`或`https://`开头的URL。
3. 提取HTML文件中的base64编码和A链接的标题。
4. 创建一个保存图像的输出文件夹。
5. 将提取的数据打印到一个结果文件中，并保存图片到指定路径。
6. 使用提取的URL发送GET请求，获取页面内容。
7. 使用BeautifulSoup库提取`<head>`中的`<meta>`标签。
8. 将提取的标题、URL、图像路径和描述写入结果文件。
9. 使用了并发。

你可以将此脚本保存为Python文件（例如`bookmark_extractor.py`），并运行它来提取书签数据和下载图像。确保已安装所需的依赖项（如`requests`、`PIL`、`pypinyin`、`unidecode`、`bs4`等）。运行命令如下：

```python
pip install -r requirements.txt
python bookmark_extractor.py input/example.html
```

## 已知问题

- 图像获取机制存在 bug，可能会导致获取到的不是与站点相对应的图标；
- 由于 YAML 格式的局限性，以及采集站点 description 会遇到各式各样的文本，需要再次处理；
  - description 中的特殊符号需要转义，如`[`, `]`, `|`, `:`；
  - description 中的内容需要删除多余换行，确保整段内容只占一行；
  - description 中的内容应设定字数上限；
  - description 中的内容可能存在编码问题，例如日文、阿拉伯文、韩文，需要完善一下在输出时的编码设定。
- 网站图标根据站点标题进行拼音转写（中文情况下），将空格转换为下划线，最终会导致文件名过长，应该为使用域名作为名称。

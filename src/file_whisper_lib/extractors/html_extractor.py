"""
HTML处理模块
"""
import re
import base64
from typing import List
from loguru import logger
from bs4 import BeautifulSoup

from ..dt import Node, File, Data
from .utils import encode_binary, decode_binary


class HTMLExtractor:
    
    @staticmethod
    def extract_text_from_html(html: str) -> str:
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text(separator=' ', strip=True)
    
    @staticmethod
    def extract_urls_from_html(html: str) -> list:
        """
        提取 HTML 中的所有 URL，覆盖常见标签、元数据、预加载、表单、懒加载、SVG 以及内联 CSS 中的 URL。
        """
        soup = BeautifulSoup(html, 'html.parser')
        urls = set()

        # 1. 基础标签属性
        # 各标签对应的 URL 属性（部分标签有多个 URL 来源）
        tag_attr_map = {
            'a': ['href'],
            'img': ['src', 'srcset'],
            'script': ['src', 'data-main'],
            'link': ['href'],
            'iframe': ['src'],
            'video': ['src', 'poster'],
            'audio': ['src'],
            'track': ['src'],
            'form': ['action'],
            'input': ['src'],  # 针对 type="image" 的情况
            'object': ['data'],
            'embed': ['src']
        }

        for tag, attrs in tag_attr_map.items():
            for element in soup.find_all(tag):
                for attr in attrs:
                    value = element.get(attr)
                    if value:
                        if attr == 'srcset':
                            # srcset 可能形如 "img1.jpg 1x, img2.jpg 2x" 分割后提取 URL
                            for part in value.split(','):
                                candidate = part.strip().split(' ')[0].strip()
                                if candidate:
                                    urls.add(candidate)
                        else:
                            urls.add(value.strip())

        # 2. 元数据与 SEO
        for meta in soup.find_all('meta'):
            # 开放图谱 <meta property="og:image" content="url">
            if meta.get('property', '').strip().lower() == 'og:image':
                content = meta.get('content')
                if content:
                    urls.add(content.strip())
            # 页面刷新 <meta http-equiv="refresh" content="5;url=redirect_url">
            if meta.get('http-equiv', '').lower() == 'refresh':
                content = meta.get('content', '')
                # 匹配形如 "5;url=redirect_url" 的格式
                m = re.search(r'url=([^;]+)', content, flags=re.IGNORECASE)
                if m:
                    urls.add(m.group(1).strip())

        # 网站图标、DNS预解析、预加载等依靠 <link> 标签，上面已经在 tag_attr_map 中处理

        # 3. 动态内容与懒加载
        # 任意含有 data-src 属性
        for element in soup.find_all(attrs={"data-src": True}):
            data_src = element.get("data-src")
            if data_src:
                urls.add(data_src.strip())

        # 4. SVG 和特殊标签
        # <image> 标签可能使用 xlink:href 或 href 属性
        for image in soup.find_all('image'):
            xlink = image.get('xlink:href')
            if xlink:
                urls.add(xlink.strip())
            alternative = image.get('href')
            if alternative:
                urls.add(alternative.strip())

        # 5. CSS 中的 URL（内联样式以及 <style> 标签内）
        # 正则匹配 url(...) 形式, 可处理单引号、双引号或不带引号的情况
        style_pattern = re.compile(r'url\((?:\'|"|)([^\'")]+)(?:\'|"|)\)')

        # 检查所有存在 style 属性的元素
        for element in soup.find_all(style=True):
            style_text = element.get('style', '')
            matches = style_pattern.findall(style_text)
            for m in matches:
                if m:
                    urls.add(m.strip())

        # 检查 <style> 标签内部的 CSS 内容
        for style_tag in soup.find_all('style'):
            css_content = style_tag.string
            if css_content:
                matches = style_pattern.findall(css_content)
                for m in matches:
                    if m:
                        urls.add(m.strip())

        return list(urls)
    
    @staticmethod
    def extract_img_from_html(html: str) -> list:
        img_bytes_list = []
        soup_t = BeautifulSoup(html, 'html.parser')
        # 查找所有的 img 标签
        images = soup_t.find_all('img')
        
        # 遍历 img 标签，打印图片 src 属性
        for image in images:
            if not image.has_attr('src'):
                continue
            img_src = image['src']
            # 这个判据不知道是否正确，最起码没有base64编码的就有问题了
            if (img_src.find("base64") == -1):
                continue 
            img_arrays1 = img_src.split(';')
            
            # img_arrays1[1]中的数据是：base64,iVBORw0KGgoAAAANSUhEUgAAAZAAAAGQCAIAAA……
            img_arrays2 = img_arrays1[1].split(',')
            if len(img_arrays2) < 1:
                continue
            if img_arrays2[0] != 'base64':
                continue
            
            # 这里 img_str 中是 base64 编码的：iVBORw0KGgoAAAANSUhEUgAAAZAAAAGQCAIAAA……
            img_str = img_arrays2[1]
            
            # 这里的 img_bytes 就是图片的二进制数组，base64 解码后的
            img_bytes = base64.b64decode(img_str)

            img_bytes_list.append(img_bytes)

        return img_bytes_list

    @staticmethod
    def extract_html(node: Node) -> List[Node]:
        nodes = []
        text = ""
        
        try:
            if isinstance(node.content, File):
                logger.debug(f"Node[{node.id}] file {node.content.mime_type}")
                text = decode_binary(node.content.content)
            elif isinstance(node.content, Data):
                logger.debug(f"Node[{node.id}] data {node.content.type}")
                text = decode_binary(node.content.content)
            
            html_text = HTMLExtractor.extract_text_from_html(text)
            
            t_node = Node()
            t_node.id = 0
            t_node.content = Data(type="TEXT", content=encode_binary(html_text))
            t_node.prev = node
            # 继承父节点的页数限制
            t_node.pdf_max_pages = node.pdf_max_pages
            t_node.word_max_pages = node.word_max_pages
            nodes.append(t_node)

            html_urls = HTMLExtractor.extract_urls_from_html(text)
            for url in html_urls:
                    t_node = Node()
                    t_node.id = 0
                    t_node.content = Data(type="URL", content=encode_binary(url))
                    t_node.prev = node
                    # 继承父节点的页数限制
                    t_node.pdf_max_pages = node.pdf_max_pages
                    t_node.word_max_pages = node.word_max_pages
                    nodes.append(t_node)

            img_bytes_list = HTMLExtractor.extract_img_from_html(text)
            for img_bytes in img_bytes_list:
                t_node = Node()
                t_node.content = File(
                    path="",
                    name="",
                    content=img_bytes
                )
                t_node.prev = node
                # 继承父节点的页数限制
                t_node.pdf_max_pages = node.pdf_max_pages
                t_node.word_max_pages = node.word_max_pages
                nodes.append(t_node)
            
        except Exception as e:
            logger.error(f"Error extracting HTML: {str(e)}")
            
        return nodes
import re
import unittest
from bs4 import BeautifulSoup

class Extractor:
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


class TestExtractUrlsFromHtml(unittest.TestCase):
    def test_empty_html(self):
        """测试空的 HTML 字符串"""
        html = ""
        self.assertEqual(Extractor.extract_urls_from_html(html), [])

    def test_basic_tags(self):
        """测试基础标签中 URL 的提取"""
        html = """
        <html>
            <body>
                <a href="https://example.com">Example</a>
                <img src="image.jpg" alt="An image">
                <script src="script.js"></script>
                <link rel="stylesheet" href="style.css">
                <iframe src="frame.html"></iframe>
                <video src="video.mp4" poster="poster.jpg"></video>
                <audio src="audio.mp3"></audio>
                <track src="subtitle.vtt">
                <form action="submit.php"></form>
                <input type="image" src="button.png">
                <object data="object.swf"></object>
                <embed src="plugin.swf">
            </body>
        </html>
        """
        expected_urls = {
            "https://example.com", "image.jpg", "script.js", "style.css",
            "frame.html", "video.mp4", "poster.jpg", "audio.mp3", "subtitle.vtt",
            "submit.php", "button.png", "object.swf", "plugin.swf"
        }
        result = set(Extractor.extract_urls_from_html(html))
        self.assertEqual(result, expected_urls)

    def test_srcset(self):
        """测试 <img> 标签中的 srcset 属性"""
        html = '<img srcset="small.jpg 320w, medium.jpg 640w, large.jpg 1024w" alt="Responsive image">'
        expected_urls = {"small.jpg", "medium.jpg", "large.jpg"}
        result = set(Extractor.extract_urls_from_html(html))
        self.assertTrue(expected_urls.issubset(result))

    def test_meta_refresh(self):
        """测试 meta 标签中刷新 URL 的提取"""
        html = '<meta http-equiv="refresh" content="5;url=https://redirect.com">'
        expected_urls = {"https://redirect.com"}
        result = set(Extractor.extract_urls_from_html(html))
        self.assertEqual(result, expected_urls)

    def test_meta_og_image(self):
        """测试 meta 开放图谱中 URL 的提取"""
        html = '<meta property="og:image" content="https://example.com/og-image.jpg">'
        expected_urls = {"https://example.com/og-image.jpg"}
        result = set(Extractor.extract_urls_from_html(html))
        self.assertEqual(result, expected_urls)

    def test_inline_style(self):
        """测试内联 style 属性中的 CSS URL 提取"""
        html = '<div style="background: url(\'bg1.jpg\'); border-image: url(bg2.png) 30 round;"></div>'
        expected_urls = {"bg1.jpg", "bg2.png"}
        result = set(Extractor.extract_urls_from_html(html))
        self.assertEqual(result, expected_urls)

    def test_style_tag(self):
        """测试 <style> 标签内 CSS 中 URL 的提取"""
        html = """
        <style>
            .logo { background-image: url("logo.png"); }
            .banner { background: url('banner.jpg') no-repeat; }
        </style>
        """
        expected_urls = {"logo.png", "banner.jpg"}
        result = set(Extractor.extract_urls_from_html(html))
        self.assertEqual(result, expected_urls)

    def test_data_src(self):
        """测试自定义 data-src 属性的提取"""
        html = '<div data-src="lazyload.jpg"></div>'
        expected_urls = {"lazyload.jpg"}
        result = set(Extractor.extract_urls_from_html(html))
        self.assertEqual(result, expected_urls)

    def test_svg_image(self):
        """测试 SVG 中 <image> 标签的 xlink:href 和 href 属性的提取"""
        html = """
        <svg>
            <image xlink:href="vector1.svg"></image>
            <image href="vector2.svg"></image>
        </svg>
        """
        expected_urls = {"vector1.svg", "vector2.svg"}
        result = set(Extractor.extract_urls_from_html(html))
        self.assertEqual(result, expected_urls)

    def test_complex_mixed_html(self):
        """测试包含多种标签和嵌入 CSS、JS 中 URL 的复杂 HTML"""
        html = """
        <html>
            <head>
                <title>Test</title>
                <meta property="og:image" content="og.jpg">
                <meta http-equiv="refresh" content="0;url=redirect.html">
                <link rel="icon" href="favicon.ico">
                <style>
                    .bg { background-image: url(bg-style.png); }
                </style>
            </head>
            <body>
                <h1>Header</h1>
                <a href="page.html">Go to page</a>
                <img src="image.jpg" srcset="small.jpg 1x, large.jpg 2x">
                <div style="background: url('div-bg.jpg')">
                    Content
                </div>
                <div data-src="lazy.png"></div>
                <svg>
                    <image xlink:href="vector.svg"></image>
                </svg>
            </body>
        </html>
        """
        expected_urls = {
            "og.jpg", "redirect.html", "favicon.ico", "bg-style.png",
            "page.html", "image.jpg", "small.jpg", "large.jpg",
            "div-bg.jpg", "lazy.png", "vector.svg"
        }
        result = set(Extractor.extract_urls_from_html(html))
        self.assertEqual(result, expected_urls)


if __name__ == "__main__":
    unittest.main()
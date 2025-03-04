import unittest
import base64
from bs4 import BeautifulSoup

class Extractor:
    @staticmethod
    def extract_img_from_html(html: str) -> str:
                soup_t = BeautifulSoup(html, 'html.parser')
                # 查找所有的 img 标签
                images = soup_t.find_all('img')
                
                # 遍历 img 标签，打印图片 src 属性
                for image in images:
                    # print(f"\n3.image --> {image}\n")
                    # 这里的img_src是：data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAZAAAAGQCAIAAA……
                    # print(f"\n3.image --> {type(image)} -- \n")
                    if not image.has_attr('src'):
                        continue
                    img_src = image['src']
                    # print(f"\n4.img_src --> {img_src}\n")
                    #self._logger().debug(f"find image resource - {img_src}")
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



class TestExtractTextFromHtml(unittest.TestCase):
    def test_empty_html(self):
        """测试空的 HTML 字符串"""
        html = ""
        self.assertEqual(Extractor.extract_text_from_html(html), "")

    def test_simple_html(self):
        """测试简单的 HTML 标签"""
        html = "<p>Hello <strong>World</strong></p>"
        self.assertEqual(Extractor.extract_text_from_html(html), "Hello World")

    def test_complex_html(self):
        """测试包含多种 HTML 标签和层级的复杂 HTML"""
        html = """
        <html>
            <head><title>Test</title></head>
            <body>
                <h1>Header</h1>
                <p>Paragraph with <a href="#">link</a> inside.</p>
                <div>
                    <p>Another paragraph.</p>
                </div>
            </body>
        </html>
        """
        expected_text = "Test Header Paragraph with link inside. Another paragraph."
        self.assertEqual(Extractor.extract_text_from_html(html), expected_text)

    def test_html_with_whitespace(self):
        """测试 HTML 中存在多余空格/换行的情况"""
        html = """
            <div>
                Line1
                <span>Line2</span>
            </div>
        """
        expected_text = "Line1 Line2"
        self.assertEqual(Extractor.extract_text_from_html(html), expected_text)

if __name__ == "__main__":
    unittest.main()
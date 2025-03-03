import unittest
from bs4 import BeautifulSoup

class Extractor:
    @staticmethod
    def extract_text_from_html(html: str) -> str:
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text(separator=' ', strip=True)

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
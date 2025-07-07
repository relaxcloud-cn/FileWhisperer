# Initialize PaddleOCR instance
from paddleocr import PaddleOCR
ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False)

# Run OCR inference on a sample image 
result = ocr.predict(
    input="/home/cyan/filewhisperer/image_1.png")

# Extract OCR text from results
for res in result:
    # Extract the text content - OCRResult behaves like a dict
    if 'rec_texts' in res:
        ocr_texts = res['rec_texts']
        print("\n提取的OCR文本:")
        for i, text in enumerate(ocr_texts, 1):
            print(f"{i}: {text}")
        
        # Join all texts into a single string
        full_text = '\n'.join(ocr_texts)
        print(f"\n完整文本:\n{full_text}")
    else:
        print("未找到rec_texts字段")

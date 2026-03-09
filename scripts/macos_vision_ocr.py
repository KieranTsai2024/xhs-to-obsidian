#!/usr/bin/env python3
"""
macOS Vision Framework OCR
使用 Apple Vision Framework 进行图片文字识别（支持中文）

依赖：pip install pyobjc-framework-Vision pyobjc-framework-Quartz
"""

import sys
from pathlib import Path

def ocr_with_vision(image_path: str) -> str:
    """使用 macOS Vision Framework 进行 OCR"""
    try:
        import Vision
        import Quartz
        from Foundation import NSURL
        
        # 加载图片
        image_url = NSURL.fileURLWithPath_(image_path)
        image = Quartz.CIImage.imageWithContentsOfURL_(image_url)
        
        if image is None:
            return ""
        
        # 创建 OCR 请求
        request = Vision.VNRecognizeTextRequest.alloc().init()
        
        # 配置 OCR 选项
        request.setUsesLanguageCorrection_(True)
        
        # 设置识别语言（中文 + 英文）
        # Vision Framework 使用 BCP-47 语言代码
        languages = ["zh-Hans", "en"]
        request.setRecognitionLanguages_(languages)
        
        # 设置识别级别（准确优先）
        # 使用字符串常量，避免版本兼容问题
        request.setRecognitionLevel_(0)  # 0 = accurate, 1 = fast
        
        # 执行请求
        handler = Vision.VNImageRequestHandler.alloc().initWithCIImage_options_(image, None)
        success = handler.performRequests_error_([request], None)
        
        if not success:
            return ""
        
        # 提取识别结果
        results = []
        for observation in request.results():
            text = observation.topCandidates_(1)
            if text and len(text) > 0:
                recognized_text = text[0].string()
                confidence = text[0].confidence()
                if confidence > 0.5:  # 只保留置信度>50% 的结果
                    results.append(recognized_text)
        
        return "\n".join(results)
        
    except ImportError as e:
        print(f"Vision Framework 不可用：{e}", file=sys.stderr)
        print("请安装：pip install pyobjc-framework-Vision pyobjc-framework-Quartz", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"OCR 错误：{e}", file=sys.stderr)
        return ""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python macos_vision_ocr.py <图片路径>", file=sys.stderr)
        sys.exit(1)
    
    image_path = sys.argv[1]
    if not Path(image_path).exists():
        print(f"文件不存在：{image_path}", file=sys.stderr)
        sys.exit(1)
    
    result = ocr_with_vision(image_path)
    print(result)

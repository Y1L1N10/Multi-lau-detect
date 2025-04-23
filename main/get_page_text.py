from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
from googletrans import Translator
import os
import re
import random
from langdetect import detect
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

def get_page_text(url):
    driver = webdriver.Chrome()
    driver.maximize_window()
    try:
        # 检查当前URL，防止重定向
        if url == 'https://mapify.so':
            driver.get(url)
            current_url = driver.current_url
            if current_url != url:
                driver.get(url)
                time.sleep(1)
                current_url = driver.current_url
                if current_url != url:
                    raise Exception(f'页面重定向到{current_url}，无法保持原始URL')
        else:
            driver.get(url)
        # 获取整个页面的文本内容
        body = driver.find_element(By.TAG_NAME, 'body')
        # 排除class为relative overflow-x-hidden text-[#000]的元素
        excluded_elements = driver.find_elements(By.CSS_SELECTOR, '.relative.overflow-x-hidden.text-\[\#000\]')
        for element in excluded_elements:
            driver.execute_script("arguments[0].style.display = 'none';", element)
        
        # 初始化滚动位置和结果集
        last_height = driver.execute_script("return document.body.scrollHeight")
        elements_with_text = []
        
        while True:
            # 获取当前可见区域的文本内容
            body = driver.find_element(By.TAG_NAME, 'body')
            elements = body.find_elements(By.XPATH, ".//*[text()]")
            for element in elements:
                try:
                    text = element.text
                    if text and text.strip():
                        elements_with_text.append({
                            "tag": element.tag_name,
                            "text": text,
                            "html": element.get_attribute('outerHTML')
                        })
                except:
                    continue
            
            # 向下滚动1000px
            driver.execute_script("window.scrollBy(0, 1000);")
            
            # 等待页面加载
            time.sleep(1)
            
            # 计算新的滚动高度并检查是否到达页面底部
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # 获取html标签的lang属性
        html_tag = driver.find_element(By.TAG_NAME, 'html')
        html_lang = html_tag.get_attribute('lang')
        print(f"HTML lang attribute: {html_lang}")

        # 将结果写入文件
        result = []
        for item in elements_with_text:
            result.append(f"{item['html']}\n{item['text']}")
            
        text_file_path = f"../page_text/page_text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        os.makedirs(os.path.dirname(text_file_path), exist_ok=True)
        with open(text_file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(result))

        # 增强版文本预处理，提高语言检测准确性
        def clean_text(text):
            # 移除HTML标签
            text = re.sub(r'<[^>]+>', '', text)
            # 移除特殊字符和多余空格
            text = re.sub(r'[\t\n\r\f\v]+', ' ', text)
            # 保留更多语言字符
            text = re.sub(r'[^\w\s\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7a3\u0400-\u04ff\u0e00-\u0e7f\u1ea0-\u1ef9]', ' ', text)
            # 移除连续重复字符
            text = re.sub(r'(.)\1{3,}', r'\1', text)
            return ' '.join(text.strip().split())

        # 简单语言检测（基于字符特征）
        def simple_language_detection(text):
            # 检测中文
            if any('\u4e00' <= c <= '\u9fff' for c in text):
                return 'zh-CN'
            # 检测日语假名
            if any('\u3040' <= c <= '\u309f' for c in text) or any('\u30a0' <= c <= '\u30ff' for c in text):
                return 'ja'
            # 检测韩文
            if any('\uac00' <= c <= '\ud7a3' for c in text):
                return 'ko'
            # 检测俄语
            if any('\u0400' <= c <= '\u04ff' for c in text):
                return 'ru'
            return None

        # 记录不匹配的文本
        mismatched_texts = []
        detected_languages = []

        # 按段落合并文本以提高检测准确性
        current_paragraph = []
        paragraphs = []

        for item in elements_with_text:
            text = clean_text(item['text'])
            if not text:
                continue

            current_paragraph.append({
                'text': text,
                'item': item
            })

            # 当段落累积一定长度或遇到特定标签时进行处理
            if len(''.join(p['text'] for p in current_paragraph)) > 100 or item['tag'] in ['h1', 'h2', 'h3', 'p']:
                paragraphs.append(current_paragraph)
                current_paragraph = []

        if current_paragraph:
            paragraphs.append(current_paragraph)

        for paragraph in paragraphs:
            # 合并段落中的文本
            combined_text = ' '.join(p['text'] for p in paragraph)
            detected_lang = None

            # 方法1: 首先使用简单语言检测
            try:
                detected_lang = simple_language_detection(combined_text)
                if detected_lang:
                    # 计算置信度
                    if detected_lang.startswith('zh'):
                        chars = len([c for c in combined_text if '\u4e00' <= c <= '\u9fff'])
                        confidence = chars / len(combined_text) if len(combined_text) > 0 else 0
                        if confidence > 0.2:  # 如果中文字符比例超过20%，认为检测结果可靠
                            detected_languages.append(detected_lang)
                            continue
                    elif detected_lang == 'ja':
                        chars = len([c for c in combined_text if ('\u3040' <= c <= '\u309f') or ('\u30a0' <= c <= '\u30ff')])
                        confidence = chars / len(combined_text) if len(combined_text) > 0 else 0
                        if confidence > 0.2:
                            detected_languages.append(detected_lang)
                            continue
                    elif detected_lang == 'ko':
                        chars = len([c for c in combined_text if '\uac00' <= c <= '\ud7a3'])
                        confidence = chars / len(combined_text) if len(combined_text) > 0 else 0
                        if confidence > 0.2:
                            detected_languages.append(detected_lang)
                            continue
                    else:
                        detected_languages.append(detected_lang)
            except Exception as e:
                print(f"简单语言检测失败: {str(e)}")

            # 方法2: 使用langdetect库
            if not detected_lang or detected_lang == 'en':
                try:
                    simple_text = combined_text[:150].strip()
                    if len(simple_text) > 15:
                        detected_lang = detect(simple_text)
                        detected_languages.append(detected_lang)
                        continue
                except Exception:
                    pass

            # 方法3: 使用googletrans，带指数退避重试
            max_retries = 3
            backoff_time = 0.5

            for retry in range(max_retries):
                try:
                    translator = Translator(service_urls=[
                        'translate.google.com',
                        'translate.google.co.kr',
                        'translate.google.co.jp',
                        'translate.google.de',
                        'translate.google.fr'
                    ])
                    text_to_detect = combined_text[:200].strip()
                    detection = translator.detect(text_to_detect)
                    detected_lang = detection.lang
                    detected_lang = detected_lang.lower().replace('-', '_')
                    detected_languages.append(detected_lang)
                    break
                except Exception as e:
                    if retry == max_retries - 1:
                        if not detected_lang:
                            try:
                                detected_lang = simple_language_detection(combined_text)
                                detected_languages.append(detected_lang)
                            except Exception:
                                detected_lang = 'en'
                                detected_languages.append(detected_lang)
                    else:
                        wait_time = backoff_time * (2 ** retry) + random.uniform(0, 0.5)
                        time.sleep(wait_time)

            if not detected_lang:
                print(f"无法检测文本语言: {combined_text[:50]}...")
                continue

            # 标准化语言代码进行比较
            lang_mapping = {
                'cn': 'zh-CN', 'tc': 'zh-TW', 'en': 'en', 'ja': 'ja',
                'ko': 'ko', 'ru': 'ru', 'fr': 'fr', 'de': 'de', 'es': 'es'
            }
            normalized_html_lang = lang_mapping.get(html_lang.lower(), html_lang)
            normalized_detected_lang = lang_mapping.get(detected_lang.lower(), detected_lang)

            # 计算置信度
            text_length = len(combined_text)
            confidence_threshold = 0.7

            if normalized_detected_lang.startswith('zh-CN'):
                lang_chars = len([c for c in combined_text if '\u4e00' <= c <= '\u9fff'])
            elif normalized_detected_lang == 'ja':
                lang_chars = len([c for c in combined_text if ('\u3040' <= c <= '\u309f') or ('\u30a0' <= c <= '\u30ff')])
            elif normalized_detected_lang == 'ko':
                lang_chars = len([c for c in combined_text if '\uac00' <= c <= '\ud7a3'])
            else:
                lang_chars = text_length

            confidence = lang_chars / text_length if text_length > 0 else 0

            if normalized_detected_lang != normalized_html_lang and confidence > confidence_threshold:
                for p in paragraph:
                    mismatched_texts.append({
                        "text": p['text'],
                        "tag": p['item']['tag'],
                        "html": p['item']['html'],
                        "detected_lang": detected_lang
                    })

        # 打印不匹配的文本
        if mismatched_texts:
            print("\n发现语言不匹配的文本:")
            for item in mismatched_texts:
                print(f"标签: <{item['tag']}>")
                print(f"检测语言: {item['detected_lang']}")
                print(f"文本内容: {item['text']}")
                print(f"HTML: {item['html'][:100]}...")
                print("-" * 50)
            
            # 将不匹配的文本写入单独的文件
            mismatch_file_path = f"../page_text/mismatched_text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(mismatch_file_path, 'w', encoding='utf-8') as f:
                for item in mismatched_texts:
                    f.write(f"Tag: <{item['tag']}>\n")
                    f.write(f"Detected language: {item['detected_lang']}\n")
                    f.write(f"Text: {item['text']}\n")
                    f.write(f"HTML: {item['html']}\n")
                    f.write("-" * 50 + "\n")
            print(f"不匹配文本已保存至: {mismatch_file_path}")
        else:
            from collections import Counter
            most_common_lang = Counter(detected_languages).most_common(1)[0][0] if detected_languages else html_lang
            print(f"\n未发现语言不匹配的文本。")
            print(f"网页声明的语言: {html_lang}")
            print(f"检测到的主要语言: {most_common_lang}")
            print(f"语言检测结果{'正确' if html_lang == most_common_lang else '不正确'}")
        
        # 返回出现次数最多的语言类型
        from collections import Counter
        if detected_languages:
            return Counter(detected_languages).most_common(1)[0][0]
        return html_lang
    finally:
        driver.quit()

if __name__ == "__main__":
    #text = get_page_text("https://mapify.so/ja")
    #text = get_page_text("https://mapify.so/cn")
    #text = get_page_text("https://mapify.so/tc")
    text = get_page_text("https://mapify.so")
    print(f"最终检测到的语言: {text}")
    
    # 将返回的语言代码写入文件
    with open(f"../page_text/detected_lang_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", "w", encoding="utf-8") as f:
        f.write(text)
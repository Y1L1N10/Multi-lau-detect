from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
from langdetect import detect, DetectorFactory
from collections import Counter
import os
import re
import random
import requests
from googletrans import Translator, LANGUAGES

# 设置langdetect的种子，确保结果一致性
DetectorFactory.seed = 0

# 简单的备用语言检测函数，基于文本特征
def simple_language_detection(text):
    # 增强版语言检测逻辑，提高中文识别准确率
    # 中文检测
    chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
    if chinese_chars > len(text) * 0.05:  # 降低中文检测阈值
        # 简体/繁体中文判断 (增强版)
        traditional_chars = len([c for c in text if c in '繁體國說壹經來這個當時後會發現實現問題點樣學習經驗'])
        simplified_chars = len([c for c in text if c in '简体中文说一经过来这个当时后发现实现问题点样学习经验'])
        
        # 根据简繁字符比例判断
        if traditional_chars > 0 and traditional_chars > simplified_chars * 1.5:
            return 'zh-TW'
        return 'zh-CN'
    
    # 日语检测 (假名字符)
    japanese_chars = len([c for c in text if ('\u3040' <= c <= '\u309f') or ('\u30a0' <= c <= '\u30ff')])
    if japanese_chars > len(text) * 0.05:
        return 'ja'
    
    # 韩语检测 (韩文字符)
    korean_chars = len([c for c in text if '\uac00' <= c <= '\ud7a3'])
    if korean_chars > len(text) * 0.15:  # 提高韩语检测阈值
        return 'ko'
    
    # 俄语检测 (西里尔字符)
    russian_chars = len([c for c in text if '\u0400' <= c <= '\u04ff'])
    if russian_chars > len(text) * 0.15:  # 提高俄语检测阈值
        return 'ru'
    
    # 泰语检测
    thai_chars = len([c for c in text if '\u0e00' <= c <= '\u0e7f'])
    if thai_chars > len(text) * 0.15:  # 提高泰语检测阈值
        return 'th'
    
    # 越南语检测
    vietnamese_chars = len([c for c in text if '\u1ea0' <= c <= '\u1ef9'])
    if vietnamese_chars > len(text) * 0.15:  # 添加越南语检测
        return 'vi'
    
    # 阿拉伯语检测
    arabic_chars = len([c for c in text if '؀' <= c <= 'ۿ' or 'ݐ' <= c <= 'ݿ' or 'ࢠ' <= c <= 'ࣿ'])
    if arabic_chars > len(text) * 0.15:
        return 'ar'
        
    # 希伯来语检测
    hebrew_chars = len([c for c in text if '֐' <= c <= '׿'])
    if hebrew_chars > len(text) * 0.15:
        return 'he'
        
    # 波兰语检测 (基于特殊字符)
    polish_chars = len([c for c in text if c in 'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ'])
    if polish_chars > len(text) * 0.05:
        return 'pl'
        
    # 土耳其语检测 (基于特殊字符)
    turkish_chars = len([c for c in text if c in 'çğıöşüÇĞİÖŞÜ'])
    if turkish_chars > len(text) * 0.05:
        return 'tr'
        
    # 荷兰语检测 (基于特殊字符)
    dutch_chars = len([c for c in text if c in 'áéíóúýÁÉÍÓÚÝ'])
    if dutch_chars > len(text) * 0.05:
        return 'nl'
        
    # 意大利语检测 (基于特殊字符)
    italian_chars = len([c for c in text if c in 'àèéìíîòóùúÀÈÉÌÍÒÓÙÚ'])
    if italian_chars > len(text) * 0.05:
        return 'it'
        
    # 默认返回英语
    return 'en'

def get_page_text(driver, url):
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
            # 等待页面加载完成
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            
            # 获取当前可见区域的文本内容
            body = driver.find_element(By.TAG_NAME, 'body')
            elements = body.find_elements(By.XPATH, ".//*[not(self::script) and not(self::style) and string-length(normalize-space(text())) > 0]")
            
            for element in elements:
                try:
                    # 确保元素在视图中
                    driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(0.1)  # 短暂等待确保元素完全可见
                    
                    # 获取元素文本和属性
                    text = element.text
                    aria_label = element.get_attribute('aria-label') or ''
                    title = element.get_attribute('title') or ''
                    alt = element.get_attribute('alt') or ''
                    placeholder = element.get_attribute('placeholder') or ''
                    
                    # 合并所有文本内容
                    combined_text = ' '.join(filter(None, [text, aria_label, title, alt, placeholder]))
                    
                    if combined_text.strip():
                        elements_with_text.append({
                            "tag": element.tag_name,
                            "text": combined_text,
                            "html": element.get_attribute('outerHTML')
                        })
                except Exception as e:
                    print(f"提取元素文本时出错: {str(e)}")
                    continue
            
            # 使用更平滑的滚动
            last_height = driver.execute_script("return window.pageYOffset;")
            driver.execute_script("window.scrollTo(0, window.pageYOffset + window.innerHeight);")
            
            # 等待动态内容加载
            time.sleep(1.5)
            
            # 检查是否到达页面底部
            new_height = driver.execute_script("return window.pageYOffset;")
            if new_height == last_height:
                # 尝试再次滚动以确保真的到达底部
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                final_height = driver.execute_script("return window.pageYOffset;")
                if final_height == new_height:
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

        # 直接分析文本内容，使用langdetect替代googletrans
        
        # 记录不匹配的文本
        mismatched_texts = []
        detected_languages = []
        
        # 增强版文本预处理，提高语言检测准确性
        def clean_text(text):
            # 移除HTML标签
            import re
            text = re.sub(r'<[^>]+>', '', text)
            # 移除特殊字符和多余空格
            text = re.sub(r'[\t\n\r\f\v]+', ' ', text)
            # 保留更多语言字符
            text = re.sub(r'[^\w\s\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7a3\u0400-\u04ff\u0e00-\u0e7f\u1ea0-\u1ef9]', ' ', text)
            # 移除连续重复字符
            text = re.sub(r'(.)\1{3,}', r'\1', text)
            return ' '.join(text.strip().split())
        
        # 合并相邻的文本以提高检测准确性
        merged_texts = []
        current_text = ""
        
        for item in elements_with_text:
            if len(current_text) < 100:  # 设置合适的文本长度阈值
                current_text += " " + item['text'].strip()
            else:
                merged_texts.append({
                    "text": current_text,
                    "items": [item]
                })
                current_text = item['text'].strip()
        
        if current_text:  # 添加最后一段文本
            merged_texts.append({
                "text": current_text,
                "items": [elements_with_text[-1]]
            })
        
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
            
            # 完全重构的语言检测逻辑，使用多种方法并增强错误处理
            detected_lang = None
            
            # 方法1: 首先使用简单语言检测（基于字符特征，不依赖网络）
            try:
                detected_lang = simple_language_detection(combined_text)
                if detected_lang:
                    # 计算置信度
                    if detected_lang.startswith('zh'):
                        chars = len([c for c in combined_text if '\u4e00' <= c <= '\u9fff'])
                        confidence = chars / len(combined_text) if len(combined_text) > 0 else 0
                        if confidence > 0.2:  # 如果中文字符比例超过20%，认为检测结果可靠
                            detected_languages.append(detected_lang)
                            continue  # 跳过其他检测方法
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
                        # 对于其他语言，先添加到结果，但继续尝试其他方法
                        detected_languages.append(detected_lang)
            except Exception as e:
                print(f"简单语言检测失败: {str(e)}")
            
            # 方法2: 使用langdetect库
            if not detected_lang or detected_lang == 'en':  # 如果没有检测到或检测为英语，尝试使用langdetect
                try:
                    # 提取更短的文本片段进行检测
                    simple_text = combined_text[:150].strip()  # 增加文本长度以提高准确性
                    if len(simple_text) > 15:  # 确保文本长度足够
                        detected_lang = detect(simple_text)
                        detected_languages.append(detected_lang)
                        continue  # 检测成功，跳过googletrans
                except Exception as e:
                    # 不打印错误，继续尝试下一种方法
                    pass
            
            # 方法3: 使用googletrans，带指数退避重试
            max_retries = 3
            backoff_time = 0.5  # 初始退避时间
            
            for retry in range(max_retries):
                try:
                    # 创建新的Translator实例，避免复用可能导致的连接问题
                    translator = Translator(service_urls=[
                        'translate.google.com',
                        'translate.google.co.kr',
                    ])
                    # 限制文本长度，减少请求负担
                    text_to_detect = combined_text[:200].strip()
                    detection = translator.detect(text_to_detect)
                    detected_lang = detection.lang
                    # 转换语言代码格式（例如zh-CN -> zh_cn）
                    detected_lang = detected_lang.lower().replace('-', '_')
                    detected_languages.append(detected_lang)
                    break
                except Exception as e:
                    # 如果最后一次重试也失败
                    if retry == max_retries - 1:
                        # 如果之前的方法都没有成功，再次使用简单语言检测
                        if not detected_lang:
                            try:
                                detected_lang = simple_language_detection(combined_text)
                                detected_languages.append(detected_lang)
                            except Exception:
                                # 如果所有方法都失败，设置一个默认值
                                detected_lang = 'en'  # 默认为英语
                                detected_languages.append(detected_lang)
                    else:
                        # 指数退避策略，每次失败后等待时间增加
                        wait_time = backoff_time * (2 ** retry) + random.uniform(0, 0.5)
                        time.sleep(wait_time)
            
            if not detected_lang:
                print(f"无法检测文本语言: {combined_text[:50]}...")
                continue
            
            # 如果检测到的语言与html标签的lang不同，记录该文本
            # 定义语言代码映射关系
            lang_mapping = {
                'cn': 'zh-CN',
                'tc': 'zh-TW',
                'en': 'en',
                'ja': 'ja',
                'id': 'id',
                'de': 'de',
                'es': 'es',
                'fr': 'fr',
                'pt': 'pt',
                'ko': 'ko',
                'hi': 'hi',
                'ru': 'ru',
                'th': 'th',
                'vi': 'vi',
                'ar': 'ar',
                'he': 'he',
                'pl': 'pl',
                'tr': 'tr',
                'nl': 'nl',
                'it': 'it',
             
            }
            
            # 标准化语言代码进行比较
            normalized_html_lang = lang_mapping.get(html_lang.lower(), html_lang)
            normalized_detected_lang = lang_mapping.get(detected_lang.lower(), detected_lang)
            
            # 如果检测到的语言与html标签的lang不同，且置信度足够高才记录
            text_length = len(combined_text)
            confidence_threshold = 0.7  # 设置置信度阈值
            
            # 计算文本中目标语言字符的比例
            if normalized_detected_lang.startswith('zh'):
                lang_chars = len([c for c in combined_text if '\u4e00' <= c <= '\u9fff'])
            elif normalized_detected_lang == 'ja':
                lang_chars = len([c for c in combined_text if ('\u3040' <= c <= '\u309f') or ('\u30a0' <= c <= '\u30ff')])
            elif normalized_detected_lang == 'ko':
                lang_chars = len([c for c in combined_text if '\uac00' <= c <= '\ud7a3'])
            else:
                lang_chars = text_length  # 对于其他语言，假设置信度足够
            
            confidence = lang_chars / text_length if text_length > 0 else 0
            
            # 只有当置信度超过阈值且语言不匹配时才记录
            if normalized_detected_lang != normalized_html_lang and confidence > confidence_threshold:
                # 记录段落中的所有相关文本
                try:
                    for p in paragraph:
                        mismatched_texts.append({
                            "text": p['text'],
                            "tag": p['item']['tag'],
                            "html": p['item']['html'],
                            "detected_lang": detected_lang
                        })
                except Exception as e:
                    print(f"Language detection error for text '{text[:30]}...': {e}")

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
        
        # 检查是否有乱码
        has_garbled = False
        for item in elements_with_text:
            try:
                item['text'].encode('utf-8').decode('utf-8')
            except UnicodeDecodeError:
                has_garbled = True
                break
        
        # 返回语言类型和乱码检测结果
        if detected_languages:
            main_lang = Counter(detected_languages).most_common(1)[0][0]
            print(f'检测到的语言: {main_lang}，{"有乱码" if has_garbled else "无乱码"}')            
            return main_lang
        print(f'检测到的语言: {html_lang}，{"有乱码" if has_garbled else "无乱码"}')            
        return html_lang
    except Exception as e:
        print(f"检测过程中出现错误: {str(e)}")
        return None
        driver.quit()


def switch_language(driver, language):
    # 点击语言切换按钮
    locale_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='homepage-locale-btn']"))
    )
    driver.execute_script("arguments[0].click();", locale_btn)

    # 选择目标语言
    language_link = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, f"a[href='/{language}']"))
    )
    language_link.click()


def main():
    # 初始化WebDriver
    driver = webdriver.Chrome()
    # 网页全屏
    driver.maximize_window()
    try:
        # 访问目标网站
        driver.get("https://mapify.so/cn")

        # 遍历并切换所有支持的语言
        languages = ['en', 'ja', 'tc', 'cn', 'id', 'de', 'es', 'fr', 'pt', 'ko', 'hi', 'ru', 'th', 'vi']  # 所有支持的语言代码
        for lang in languages:
            try:
                print(f"\n正在检测 {lang} 语言版本...")
                # 切换语言
                switch_language(driver, lang)
                # 等待页面加载完成
                time.sleep(2)
                # 检测当前页面语言
                detected_lang = get_page_text(driver, driver.current_url)
                if detected_lang:
                    print(f"当前语言: {lang}, 检测到的语言: {detected_lang}")
                else:
                    print(f"语言检测失败: {lang}")
            except Exception as e:
                print(f"处理 {lang} 语言版本时出错: {str(e)}")
                continue

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
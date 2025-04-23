from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
from googletrans import Translator
import os
import sys
from collections import Counter

class IntegratedDetector:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        sys.stdout.reconfigure(encoding='utf-8')

    def check_text_overflow(self):
        text_elements = self.driver.find_elements(By.XPATH, '//*[text()]')
        overflow_elements = []

        for element in text_elements:
            try:
                WebDriverWait(self.driver, 0.1).until(
                    EC.presence_of_element_located((By.XPATH, f"//*[text()='{element.text}']")))
                
                overflow_x = element.value_of_css_property('overflow-x')
                overflow_y = element.value_of_css_property('overflow-y')
                scroll_width = int(element.get_attribute('scrollWidth') or 0)
                client_width = int(element.get_attribute('clientWidth') or 0)
                scroll_height = int(element.get_attribute('scrollHeight') or 0)
                client_height = int(element.get_attribute('clientHeight') or 0)

                if (overflow_x == 'hidden' or overflow_y == 'hidden') and \
                   (scroll_width > client_width or scroll_height > client_height):
                    overflow_elements.append({
                        'tag': element.tag_name,
                        'text': element.text,
                        'html': element.get_attribute("outerHTML"),
                        'dimensions': {
                            'scroll_width': scroll_width,
                            'client_width': client_width,
                            'scroll_height': scroll_height,
                            'client_height': client_height
                        }
                    })
            except Exception:
                continue

        if overflow_elements:
            overflow_file = f"../page_text/overflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(overflow_file, 'w', encoding='utf-8') as f:
                for item in overflow_elements:
                    f.write(f"标签: <{item['tag']}>\n")
                    f.write(f"文本: {item['text']}\n")
                    f.write(f"HTML: {item['html']}\n")
                    f.write(f"尺寸: {item['dimensions']}\n")
                    f.write("-" * 50 + "\n")
            print(f"文字溢出检测结果已保存至: {overflow_file}")
        return overflow_elements

    def get_page_text(self, url):
        try:
            if url == 'https://mapify.so':
                self.driver.get(url)
                if self.driver.current_url != url:
                    self.driver.get(url)
                    time.sleep(1)
                    if self.driver.current_url != url:
                        raise Exception(f'页面重定向到{self.driver.current_url}，无法保持原始URL')
            else:
                self.driver.get(url)

            # 获取页面文本和语言检测
            html_lang = self.driver.find_element(By.TAG_NAME, 'html').get_attribute('lang')
            print(f"HTML lang属性: {html_lang}")

            # 检查文字溢出
            overflow_results = self.check_text_overflow()
            
            # 返回主要语言
            return html_lang
        except Exception as e:
            print(f"检测过程中出错: {e}")
            return None

    def switch_language(self, language):
        try:
            locale_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='homepage-locale-btn']")))
            self.driver.execute_script("arguments[0].click();", locale_btn)

            language_link = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"a[href='/{language}']")))
            language_link.click()
            return True
        except Exception:
            return False

    def run_full_detection(self, base_url='https://mapify.so/cn'):
        try:
            self.driver.get(base_url)
            languages = ['en', 'ja', 'tc', 'cn']
            
            for lang in languages:
                if self.switch_language(lang):
                    detected_lang = self.get_page_text(self.driver.current_url)
                    print(f"检测到的语言: {detected_lang}")
            return True
        except Exception as e:
            print(f"完整检测过程中出错: {e}")
            return False
        finally:
            self.driver.quit()

if __name__ == "__main__":
    detector = IntegratedDetector()
    detector.run_full_detection()
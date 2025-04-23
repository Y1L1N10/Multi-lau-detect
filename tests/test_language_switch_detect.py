import pytest
import pytest_asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
@pytest.mark.asyncio
async def test_language_switch():
    driver = webdriver.Chrome()
    driver.maximize_window()
    try:
        driver.get("https://mapify.so/cn")
        languages = ['en', 'ja', 'tc', 'cn']
        for lang in languages:
            # 点击语言切换按钮
            locale_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='homepage-locale-btn']"))
            )
            driver.execute_script("arguments[0].click();", locale_btn)

            # 选择目标语言
            language_link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"a[href='/{lang}']"))
            )
            language_link.click()

            # 验证URL是否正确
            expected_url = f"https://mapify.so/{lang}" if lang != 'en' else "https://mapify.so/"
            assert driver.current_url == expected_url

            # 验证html标签的lang属性
            html_tag = driver.find_element(By.TAG_NAME, 'html')
            lang_attribute = html_tag.get_attribute('lang')
            if lang == 'en':
                assert lang_attribute == 'en-US'
            elif lang == 'ja':
                assert lang_attribute == 'ja'
            elif lang == 'tc':
                assert lang_attribute == 'zh-TW'
            elif lang == 'cn':
                assert lang_attribute == 'zh-CN'

            #fun3：页面语言类型判断
            # 获取网页关键文本内容
            key_text = driver.find_element(By.CSS_SELECTOR, 'h1').text
            
            # 使用googletrans判断语言类型，增加异常处理
            from googletrans import Translator
            translator = Translator()
            try:
                detected_lang = await translator.detect(key_text)
                assert detected_lang.lang == lang_attribute
            except Exception as e:
                print(f"Language detection failed: {e}")
                assert False, "Language detection failed"
    finally:
        driver.quit()


if __name__ == "__main__":
    pytest.main()
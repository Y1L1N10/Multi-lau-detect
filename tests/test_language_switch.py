import pytest
import allure
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@allure.feature("语言切换测试")
def test_language_switch():
    driver = webdriver.Chrome()
    driver.maximize_window()
    
    with allure.step("初始化浏览器并访问页面"):
        driver.get("https://mapify.so/cn")
    
    try:
        languages = ['en', 'ja', 'tc', 'cn', 'id', 'de', 'es', 'fr', 'pt', 'ko', 'hi', 'ru', 'th', 'vi']  # 所有支持的语言代码
        
        for lang in languages:
            with allure.step(f"切换至{lang}语言"):
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

            with allure.step("验证URL和语言属性"):
                expected_url = f"https://mapify.so/{lang}" if lang != 'en' else "https://mapify.so/"
                try:
                    assert driver.current_url == expected_url
                except AssertionError:
                    driver.save_screenshot(f"failure_{lang}.png")
                    allure.attach.file(f"failure_{lang}.png", name=f"URL验证失败_{lang}", attachment_type=allure.attachment_type.PNG)
                    raise

                html_tag = driver.find_element(By.TAG_NAME, 'html')
                lang_attribute = html_tag.get_attribute('lang')
                expected_lang = {
                    'en': 'en-US',
                    'ja': 'ja',
                    'tc': 'zh-TW',
                    'cn': 'zh-CN',
                    'id': 'id',
                    'de': 'de',
                    'es': 'es',
                    'fr': 'fr',
                    'pt': 'pt',
                    'ko': 'ko',
                    'hi': 'hi',
                    'ru': 'ru',
                    'th': 'th',
                    'vi': 'vi'
                }
                try:
                    assert lang_attribute == expected_lang[lang]
                except AssertionError:
                    driver.save_screenshot(f"failure_{lang}_attribute.png")
                    allure.attach.file(f"failure_{lang}_attribute.png", name=f"语言属性失败_{lang}", attachment_type=allure.attachment_type.PNG)
                    raise
    finally:
        driver.quit()


if __name__ == "__main__":
    pytest.main()
    #自动在控制台输入：allure serve allure-results
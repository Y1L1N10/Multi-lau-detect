import pytest
import allure
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from web_lau_detect.main.language_switch_get_page_detect import get_page_text, switch_language, main

@pytest.fixture(scope='function')
def driver():
    # 初始化WebDriver
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()

@allure.feature('语言检测功能')
class TestLanguageDetection:
    
    @allure.story('测试get_page_text函数')
    @pytest.mark.parametrize('url,expected_lang', [
        ('https://mapify.so/cn', 'zh-CN'),
        ('https://mapify.so', 'en'),
        ('https://mapify.so/ja', 'ja'),
        ('https://mapify.so/tc', 'zh-TW')
    ])
    def test_get_page_text(self, url, expected_lang):
        with allure.step(f'访问URL: {url}'):
            detected_lang = get_page_text(url)
            assert detected_lang == expected_lang, f'期望语言为{expected_lang}，实际检测到的语言为{detected_lang}'

    @allure.story('测试switch_language函数')
    @pytest.mark.parametrize('target_lang', ['', 'ja', 'tc', 'cn'])
    def test_switch_language(self, driver, target_lang):
        with allure.step(f'切换语言到: {target_lang}'):
            # 访问初始页面
            driver.get('https://mapify.so/cn')
            
            # 切换语言
            switch_language(driver, target_lang)
            
            # 验证URL已更改
            expected_url = f'https://mapify.so/{target_lang}'
            assert driver.current_url == expected_url, f'URL应为{expected_url}，实际为{driver.current_url}'
            
            # 验证html lang属性已更改
            html_tag = driver.find_element(By.TAG_NAME, 'html')
            lang_mapping = {
                'cn': 'zh-CN',
                'tc': 'zh-TW',
                'en': 'en',
                'ja': 'ja'
            }
            expected_lang = lang_mapping[target_lang]
            actual_lang = html_tag.get_attribute('lang')
            assert actual_lang == expected_lang, f'HTML lang属性应为{expected_lang}，实际为{actual_lang}'

    @allure.story('测试main函数完整流程')
    def test_main_flow(self):
        with allure.step('执行main函数'):
            main()
            # 由于main函数内部已经包含了完整的测试流程，这里主要验证其是否能正常执行完成
            # 如果执行过程中没有抛出异常，则认为测试通过
            assert True

if __name__ == '__main__':
    pytest.main(['-v', '--alluredir=../allure-results'])
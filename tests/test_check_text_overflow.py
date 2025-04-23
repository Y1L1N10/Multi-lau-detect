import pytest
import allure
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from web_lau_detect.main.check_text_overflow import check_text_overflow
import os

@pytest.fixture(scope='module')
def driver():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()

@pytest.fixture(autouse=True)
def cleanup():
    # 清理之前的测试文件
    if os.path.exists('overflow_results.txt'):
        os.remove('overflow_results.txt')
    yield
    # 测试后清理
    if os.path.exists('overflow_results.txt'):
        os.remove('overflow_results.txt')

@allure.feature('文字溢出检测')
class TestCheckTextOverflow:
    
    @allure.story('正常情况测试')
    @allure.title('测试文字溢出检测功能 - 正常页面')
    def test_check_text_overflow_normal(self, driver):
        with allure.step('访问测试页面'):
            driver.get('https://mapify.so/cn')
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[text()]'))
            )
        
        with allure.step('执行文字溢出检测'):
            check_text_overflow(driver)
            
        with allure.step('验证结果文件生成'):
            assert os.path.exists('overflow_results.txt'), '结果文件未生成'
            
        with allure.step('验证结果文件内容格式'):
            with open('overflow_results.txt', 'r', encoding='utf-8') as f:
                content = f.read()
                # 验证文件格式
                assert '标签:' in content, '结果文件缺少标签信息'
                assert '文本:' in content, '结果文件缺少文本信息'
                assert 'HTML:' in content, '结果文件缺少HTML信息'
                assert '属性:' in content, '结果文件缺少属性信息'
                assert 'CSS属性:' in content, '结果文件缺少CSS属性信息'
                assert '尺寸:' in content, '结果文件缺少尺寸信息'
                
                # 验证内容完整性
                assert '<' in content and '>' in content, '结果文件缺少有效的HTML标签'
                assert '{' in content and '}' in content, '结果文件缺少有效的属性数据'
    
    @allure.story('边界情况测试')
    @allure.title('测试文字溢出检测功能 - 空白页面')
    def test_check_text_overflow_empty_page(self, driver):
        with allure.step('访问空白页面'):
            driver.get('about:blank')
        
        with allure.step('执行文字溢出检测'):
            check_text_overflow(driver)
            
        with allure.step('验证无溢出结果'):
            assert not os.path.exists('overflow_results.txt'), '空白页面不应生成结果文件'
    
    @allure.story('异常情况测试')
    @allure.title('测试文字溢出检测功能 - 动态加载内容')
    def test_check_text_overflow_dynamic_content(self, driver):
        with allure.step('访问测试页面'):
            driver.get('https://mapify.so/cn')
            
        with allure.step('等待动态内容加载'):
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[text()]'))
            )
            
        with allure.step('执行文字溢出检测'):
            check_text_overflow(driver)
            
        with allure.step('验证结果'):
            if os.path.exists('overflow_results.txt'):
                with open('overflow_results.txt', 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 验证文件内容格式
                    assert isinstance(content, str), '结果文件内容格式错误'
                    assert len(content.strip()) > 0, '结果文件不应为空'
                    # 验证包含必要的信息
                    assert any(['overflow' in line.lower() for line in content.split('\n')]), '结果文件缺少溢出信息'
    
    @allure.story('异常处理测试')
    @allure.title('测试文字溢出检测功能 - DOM元素变化')
    def test_check_text_overflow_dom_changes(self, driver):
        with allure.step('访问测试页面并修改DOM'):
            driver.get('https://mapify.so/cn')
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[text()]'))
            )
            # 动态修改DOM
            driver.execute_script("""
                // 添加一个溢出的元素
                const div = document.createElement('div');
                div.style.width = '100px';
                div.style.height = '20px';
                div.style.overflow = 'hidden';
                div.style.whiteSpace = 'nowrap';
                div.textContent = 'This is a very long text that should overflow';
                document.body.appendChild(div);
                
                // 移除一些现有元素
                const elements = document.querySelectorAll('p, span');
                elements.forEach(el => el.remove());
            """)
            
        with allure.step('执行文字溢出检测'):
            check_text_overflow(driver)
            
        with allure.step('验证检测结果'):
            assert os.path.exists('overflow_results.txt'), '应检测到人工创建的溢出元素'
            with open('overflow_results.txt', 'r', encoding='utf-8') as f:
                content = f.read()
                assert 'This is a very long text' in content, '未检测到预期的溢出文本'
                assert '100px' in content, '未记录元素尺寸信息'

if __name__ == '__main__':
    pytest.main(['-v', '--alluredir=../allure-results'])
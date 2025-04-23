from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys

# 设置控制台输出编码
sys.stdout.reconfigure(encoding='utf-8')

def check_text_overflow(driver):
    # 等待页面加载完成
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[text()]')))
    
    # 获取所有包含文字的网页元素
    text_elements = driver.find_elements(By.XPATH, '//*[text()]')
    
    overflow_elements = []
    max_retries = 3

    for element in text_elements:
        for retry in range(max_retries):
            try:
                # 使用JavaScript检查元素是否仍在DOM中
                if not driver.execute_script("return arguments[0].isConnected", element):
                    print(f"元素已从DOM中移除，跳过处理")
                    break
                
                # 等待元素变为可交互状态
                WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.XPATH, f".//*[contains(text(), '{element.text[:50]}')]")))
                
                # 使用JavaScript滚动到元素位置
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
            
                # 使用JavaScript获取样式和尺寸信息
                style = driver.execute_script("""
                    const style = window.getComputedStyle(arguments[0]);
                    const rect = arguments[0].getBoundingClientRect();
                    return {
                        overflowX: style.overflowX,
                        overflowY: style.overflowY,
                        scrollWidth: arguments[0].scrollWidth,
                        clientWidth: arguments[0].clientWidth,
                        scrollHeight: arguments[0].scrollHeight,
                        clientHeight: arguments[0].clientHeight
                    };
                """, element)
                
                overflow_x = style['overflowX']
                overflow_y = style['overflowY']
                scroll_width = style['scrollWidth']
                client_width = style['clientWidth']
                scroll_height = style['scrollHeight']
                client_height = style['clientHeight']

                # 转换为数字进行比较
                try:
                    scroll_width = int(scroll_width) if scroll_width else 0
                    client_width = int(client_width) if client_width else 0
                    scroll_height = int(scroll_height) if scroll_height else 0
                    client_height = int(client_height) if client_height else 0
                except (ValueError, TypeError):
                    print(f"尺寸值转换失败，跳过当前元素")
                    continue

                # 判断是否有文字溢出
                if (overflow_x == 'hidden' or overflow_y == 'hidden') and (scroll_width > client_width or scroll_height > client_height):
                    element_info = {
                        'tag': element.tag_name,
                        'text': element.text,
                        'html': element.get_attribute("outerHTML"),
                        'attributes': dict(element.get_attribute("attributes")) if element.get_attribute("attributes") else {},
                        'css_properties': {
                            'overflow_x': overflow_x,
                            'overflow_y': overflow_y,
                            'width': element.value_of_css_property('width'),
                            'height': element.value_of_css_property('height')
                        },
                        'dimensions': {
                            'scroll_width': scroll_width,
                            'client_width': client_width,
                            'scroll_height': scroll_height,
                            'client_height': client_height
                        }
                    }
                    overflow_elements.append(element_info)
                    print(f'文字溢出检测到: <{element.tag_name}> 溢出大小: {scroll_width-client_width}px(宽), {scroll_height-client_height}px(高)')
                break  # 如果成功则跳出重试循环

            except Exception as e:
                if retry == max_retries - 1:  # 最后一次重试失败
                    print(f"处理元素时出错 (重试{retry + 1}/{max_retries}): {e}",
                          f"元素: {element.tag_name if hasattr(element, 'tag_name') else '未知'}",
                          f"文本: {element.text if hasattr(element, 'text') else '未知'}")
                else:
                    print(f"重试处理元素 ({retry + 1}/{max_retries})...")
                    driver.implicitly_wait(1)  # 短暂等待后重试

    # 将结果写入文件
    if overflow_elements:
        with open('overflow_results.txt', 'w', encoding='utf-8') as f:
            for item in overflow_elements:
                f.write(f"标签: <{item['tag']}>\n")
                f.write(f"文本: {item['text']}\n")
                f.write(f"HTML: {item['html']}\n")
                f.write(f"属性: {item['attributes']}\n")
                f.write(f"CSS属性: {item['css_properties']}\n")
                f.write(f"尺寸: {item['dimensions']}\n")
                f.write("-" * 50 + "\n")
        print(f"已将溢出文本详情保存至: overflow_results.txt")
    else:
        print("未检测到文字溢出")


def main():
    driver = webdriver.Chrome()
    driver.maximize_window()
    try:
        driver.get('https://mapify.so/cn')
        print("开始检查文字溢出...")
        check_text_overflow(driver)
    finally:
        driver.quit()


if __name__ == '__main__':
    main()
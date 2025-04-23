from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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
            switch_language(driver, lang)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
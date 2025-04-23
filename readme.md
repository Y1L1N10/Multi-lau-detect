Que:设计并实现自动化测试工具，测试如下场景
1、访问https://mapify.so/cn
2、点击右上角语言切换按钮切换语言
3、检查是否正确切换到对应语言，文案显示是否正常（是否有显示不全，文案溢出，乱码等问题）
4、需要遍历所有语言
5、输出测试结果



实现思路：
python(3.10)+Selenium+webdriver+googletrans(用于判断网页中的文字内容是否正确)+langdetect（也是用于判断网页中的文字内容是否正确）

棘手的问题：
1.网页会自动重定向，当访问https://mapify.so时候会自动重定向到中文界面https://mapify.so/cn
2.脚本无法在本地局域网运行，必须挂梯子，因为原域名不属于国内域名？ 反正直接访问网页是无法完全加载出来的QAQ 必须挂梯子（并且有些库函数不允许开启代理，导致无法调用对应的方法，解决方法是换国内的）
3.无论什么语言都会有类似的文字（需要以英语为标准过滤），比如说Ai YouTube  PDF Email等专有名词，需要过滤掉，不然会影响判断



fun1：语言切换
语言切换按钮的button是:`<button data-v-7b86d9db="" class="text-fg-01-light hover:text-fg-02-darken-light" data-testid="homepage-locale-btn"></button>`
语言选择的a标签的js路径是：document.querySelector("body > div:nth-child(13) > div > div.content.relative.z-10.rounded-xl.bg-bg-03-light.dark\\:bg-fg-07-dark > div > div:nth-child(2) > div.p-2.box-border.z-50 > div:nth-child(7) > div > span > a")
例：`<a class="block px-4 py-2" href="/en">English</a>`对应的是英文界面
selenium定位到对应标签，匹配对应的语言类型标签click


fun2：语言切换_检查
​	不同语言对应的内容

​	如果是：English，则html标签中，lang="en-US"     对应url为：https://mapify.so/，   原网页
​	如果是：日本語，则html标签中，lang="ja"              对应url为： https://mapify.so/ja   原网页+/ja
​	如果是：繁體中文，则html标签中，lang="zh-TW"  对应url为： https://mapify.so/tc   原网页+/tc
​	如果是：简体中文：则html标签中，lang="zh-CN"   对应url为 https://mapify.so/cn     原网页+/cn
​                lang="id"   https://mapify.so/id
​                lang="de"   https://mapify.so/de
​                lang="es"   https://mapify.so/es
​                lang="fr"   https://mapify.so/fr
​                lang="pt"   https://mapify.so/pt
​                lang="ko"   https://mapify.so/ko
​                lang="hi"   https://mapify.so/hi
​                lang="ru"   https://mapify.so/ru
​                lang="th"   https://mapify.so/th
​                lang="vi"   https://mapify.so/vi
​	检查<html>标签里的 lang="*" ，检查不同语言对应的内容是否正确
​	或者检查url后缀



fun3：页面语言类型判断(先获取网页文字，过滤英文专属名词，根据url后缀和html lang确认语言类型进行核验。以英语为标准过滤，比如说Ai YouTube  PDF Email等专有名词)

最终实现：
1）使用多种语言检测方法（字符特征检测、langdetect库和Google Translate API）来准确识别页面文本语言；
2）通过滚动页面和提取DOM元素来获取完整的页面文本内容；
3）对文本进行预处理和分段处理以提高检测准确性；
4）通过置信度阈值和指数退避重试等机制来提高检测可靠性；
5）将检测结果与页面声明的语言进行比对，记录不匹配情况。

起初想法：

​	以h1为例子：`<h1 class="mt-4 whitespace-pre-line text-5xl font-bold leading-[51px] text-black max-xs:w-[calc(100vw-43px)] xs:text-6xl xs:leading-[64px] md:mt-16 md:text-[100px] md:leading-[100px]" data-v-5f9e16bc="">AI Mind Map Summarizer</h1>`

```
from googletrans import Translator, LANGUAGES
from bs4 import BeautifulSoup

def fun3(html_content):
    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 找到 <h1> 标签
    h1_tag = soup.find('h1')
    if not h1_tag:
        return "No <h1> tag found"
    
    # 提取文本内容
    text = h1_tag.get_text()
    
    # 创建翻译器实例
    translator = Translator()
    
    # 检测语言
    detection = translator.detect(text)
    detected_lang = detection.lang
    detected_lang_name = LANGUAGES.get(detected_lang, "Unknown")
    
    return detected_lang_name

# 示例 HTML 内容
html_content = '''
<h1 class="mt-4 whitespace-pre-line text-5xl font-bold leading-[51px] text-black max-xs:w-[calc(100vw-43px)] xs:text-6xl xs:leading-[64px] md:mt-16 md:text-[100px] md:leading-[100px]" data-v-5f9e16bc="">AI Mind Map Summarizer</h1>
'''

# 调用函数
language = fun3(html_content)
print(f"Detected language: {language}")
```



fun4：验证文字内容是否显示不全、文案溢出：
最后通过以下几个关键步骤实现：

1）使用Selenium获取页面中所有包含文本的元素；
2）对每个元素进行JavaScript样式分析，通过比较scrollWidth/scrollHeight和clientWidth/clientHeight来判断是否存在溢出；
3）采用重试机制处理动态加载和DOM变化导致的元素状态不稳定问题；
4）将检测到的溢出元素详细信息（包括标签、文本内容、HTML、属性、CSS属性和尺寸信息）保存到文件中。

起初想法：

1. **检查 `scrollWidth` 和 `clientWidth`**：
   - 如果 `scrollWidth > clientWidth`，说明文字在水平方向上显示不全。
2. **检查 `scrollHeight` 和 `clientHeight`**：
   - 如果 `scrollHeight > clientHeight`，说明文字在垂直方向上显示不全。

```
def check_text_overflow(element):
    scroll_width = element.get_attribute("scrollWidth")
    client_width = element.get_attribute("clientWidth")
    scroll_height = element.get_attribute("scrollHeight")
    client_height = element.get_attribute("clientHeight")
    
    if scroll_width > client_width or scroll_height > client_height:
        return True
    return False
```





1. **检查 `overflow` 和 `text-overflow` 样式**：

   如果 `overflow: hidden` 或 `text-overflow: ellipsis`，则可能存在文案溢出。

2. **结合 `scrollWidth` 和 `clientWidth` 检查**：

   如果 `scrollWidth > clientWidth`，说明文案在水平方向上溢出。

   ```
   def check_text_overflow(element):
       overflow_x = element.value_of_css_property("overflow-x")
       overflow_y = element.value_of_css_property("overflow-y")
       
       scroll_width = element.get_attribute("scrollWidth")
       client_width = element.get_attribute("clientWidth")
       scroll_height = element.get_attribute("scrollHeight")
       client_height = element.get_attribute("clientHeight")
       
       if (overflow_x == "hidden" or overflow_y == "hidden") and (scroll_width > client_width or scroll_height > client_height):
           return True
       return False
   ```

   

   fun6：验证乱码

   对于多语言环境，可以使用翻译API（如 Google Translate API）来辅助验证文本内容是否合法
   
   ```
   from googletrans import Translator
   
   def check_text_with_translation(text, language):
       translator = Translator()
       try:
           # 尝试将文本翻译为英文
           translation = translator.translate(text, src=language, dest='en')
           return translation.text
       except Exception as e:
           # 如果翻译失败，可能说明文本内容有问题
           return False
   ```







(最后弃用)还可以根据class内存储的文字用googletrans进行判断，存储文字的class有：
1.mt-4 whitespace-pre-line text-5xl font-bold leading-[51px] text-black max-xs:w-[calc(100vw-43px)] xs:text-6xl xs:leading-[64px] md:mt-16 md:text-[100px] md:leading-[100px]
2.underline-custom
3.text-center font-dm-sans text-[20px] font-semibold leading-[30px] text-white max-md:text-base
4，text-[#000] font-dm-sans font-normal md:leading-[30px] text-[12px] md:text-[20px]
5.max-md:hidden
6.whitespace-nowrap text-[13px] font-bold
7.text-[11px] text-fg-04-light max-lg:whitespace-nowrap lg:text-xs
8.text-fg-03-light font-medium
9.mx-auto max-w-[851px] text-center text-[50px] font-bold max-md:text-4xl
10.mx-auto mt-8 max-w-3xl text-center text-xl font-medium text-fg-03-light
11.transition-all duration-500 break-all mt-1 font-bold text-black
12.text-fg-03-light overflow-hidden transition-all duration-500 break-words
13.mt-6 break-words text-xl font-bold
14.mt-4 break-words text-fg-02-light
15.font-inter text-white
16.text-center text-[36px] font-bold leading-[43.2px] max-md:text-4xl md:text-[50px] md:leading-[70px]
17.mb-8 mt-8 max-w-[737px] text-center text-base font-medium leading-6 text-fg-03-light md:mb-12 md:text-xl md:leading-7
18.absolute rounded-full bg-fg-06-light dark:bg-fg-03-dark cursor-pointer rounded-md opacity-100 transition-all duration-300 ease-[cubic-bezier(0.175,0.75,0.19,1.015)]
19.text-white mt-40 max-w-[792px] text-center text-[50px] font-bold max-md:mt-20 max-md:text-4xl
20.text-white text-opacity-50 mt-8 text-center text-xl
21.absolute rounded-full bg-fg-06-light dark:bg-fg-03-dark cursor-pointer !rounded-md opacity-100 transition-all duration-300 ease-[cubic-bezier(0.175,0.75,0.19,1.015)]
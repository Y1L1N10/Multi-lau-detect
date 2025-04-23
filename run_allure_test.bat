@echo off

REM 清理之前的测试结果
if exist allure-results rmdir /s /q allure-results

REM 创建新的测试结果目录
mkdir allure-results

REM 运行测试并生成结果
pytest web_lau_detect\tests\test_language_switch_get_page_detect.py -v --alluredir=allure-results
@REM pytest web_lau_detect\tests\test_check_text_overflow.py -v --alluredir=allure-results

REM 启动Allure服务器显示报告
allure serve allure-results
@REM cmd.exe /c run_allure_test.bat
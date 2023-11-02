from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import psutil
import functools
import time

def profile(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 获取初始时间
        start_time = time.time()

        # 获取初始内存使用情况
        process = psutil.Process()
        start_mem = process.memory_info().rss

        # 执行函数
        result = func(*args, **kwargs)

        # 获取结束时间和内存使用情况
        end_time = time.time()
        end_mem = process.memory_info().rss

        # 计算并打印结果
        elapsed_time = end_time - start_time
        mem_usage = end_mem - start_mem
        print(f"Function {func.__name__} took {elapsed_time:.2f} seconds and used {mem_usage / (1024 * 1024):.2f} MB of memory.")

        return result
    return wrapper
def fetch_data(driver,url):

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 1)

        # 定义XPath（基础信息)
        gender_age_xpath = '//*[@id="seo-text"]/div/div[1]/div[2]/div[1]/div[1]/div[2]/div[1]'
        location_xpath = '//*[@id="seo-text"]/div/div[1]/div[2]/div[1]/div[2]/div/div[2]'
        expert_type_xpath = '//*[@id="seo-text"]/div/div[1]/div[2]/div[1]/div[3]/div/div[2]/div'
        mcn_xpath = '//*[@id="seo-text"]/div/div[1]/div[2]/div[1]/div[4]/div/div[2]'
        certification_xpath = '//*[@id="seo-text"]/div/div[1]/div[2]/div[1]/div[5]/div/div[2]'
        bio_xpath = '//*[@id="seo-text"]/div/div[1]/div[2]/div[2]/div[2]/div'
        fans_xpath = '//*[@id="seo-text"]/div/div[1]/div[3]/div[1]/div[1]/div[2]/div[1]'
        fans_group_xpath = '//*[@id="seo-text"]/div/div[1]/div[3]/div[1]/div[2]/div[2]/div/div'
        reputation_xpath = '//*[@id="seo-text"]/div/div[1]/div[3]/div[1]/div[3]/div[2]/div'
        star_chart_xpath = '//*[@id="seo-text"]/div/div[1]/div[3]/div[1]/div[4]/div[2]'
        live_sales_xpath = '//*[@id="seo-text"]/div/div[1]/div[3]/div[1]/div[5]/div/div/div'
        video_sales_xpath = '//*[@id="seo-text"]/div/div[1]/div[3]/div[1]/div[6]/div/div/div'
        fans_level_xpath = '//*[@id="seo-text"]/div/div[1]/div[3]/div[2]/div[1]/div[2]/div'
        main_type_xpath = '//*[@id="seo-text"]/div/div[1]/div[3]/div[2]/div[2]/div[2]'
        sales_level_xpath = '//*[@id="seo-text"]/div/div[1]/div[3]/div[1]/div[5]/div[2]/div'
        sales_info_xpath = '//*[@id="seo-text"]/div/div[1]/div[3]/div[2]/div[4]/div[2]/div'

        #



        # 尝试获取信息并处理异常
        try:
            gender_age = wait.until(EC.presence_of_element_located((By.XPATH, gender_age_xpath))).text
        except TimeoutException:
            gender_age = "-"

        try:
            location = wait.until(EC.presence_of_element_located((By.XPATH, location_xpath))).text
        except TimeoutException:
            location = "-"

        try:
            expert_type = wait.until(EC.presence_of_element_located((By.XPATH, expert_type_xpath))).text
        except TimeoutException:
            expert_type = "-"

        try:
            mcn = wait.until(EC.presence_of_element_located((By.XPATH, mcn_xpath))).text
        except TimeoutException:
            mcn = "-"

        try:
            certification = wait.until(EC.presence_of_element_located((By.XPATH, certification_xpath))).text
        except TimeoutException:
            certification = "-"

        try:
            bio = wait.until(EC.presence_of_element_located((By.XPATH, bio_xpath))).text
        except TimeoutException:
            bio = "-"

        try:
            fans = wait.until(EC.presence_of_element_located((By.XPATH, fans_xpath))).text
        except TimeoutException:
            fans = "-"

        try:
            fans_group = wait.until(EC.presence_of_element_located((By.XPATH, fans_group_xpath))).text
        except TimeoutException:
            fans_group = "-"

        try:
            reputation = wait.until(EC.presence_of_element_located((By.XPATH, reputation_xpath))).text
        except TimeoutException:
            reputation = "-"

        try:
            star_chart = wait.until(EC.presence_of_element_located((By.XPATH, star_chart_xpath))).text
        except TimeoutException:
            star_chart = "-"

        try:
            live_sales = wait.until(EC.presence_of_element_located((By.XPATH, live_sales_xpath))).text
        except TimeoutException:
            live_sales = "-"

        try:
            video_sales = wait.until(EC.presence_of_element_located((By.XPATH, video_sales_xpath))).text
        except TimeoutException:
            video_sales = "-"

        try:
            fans_level = wait.until(EC.presence_of_element_located((By.XPATH, fans_level_xpath))).text
        except TimeoutException:
            fans_level = "-"

        try:
            main_type = wait.until(EC.presence_of_element_located((By.XPATH, main_type_xpath))).text
        except TimeoutException:
            main_type = "-"

        try:
            sales_level = wait.until(EC.presence_of_element_located((By.XPATH, sales_level_xpath))).text
        except TimeoutException:
            sales_level = "-"

        try:
            sales_info = wait.until(EC.presence_of_element_located((By.XPATH, sales_info_xpath))).text
        except TimeoutException:
            sales_info = "-"

        # 打印获取的数据
        print(f"Gender/Age: {gender_age}")
        print(f"Location: {location}")
        print(f"Expert Type: {expert_type}")
        print(f"MCN: {mcn}")
        print(f"Certification: {certification}")
        print(f"Bio: {bio}")
        print(f"Fans: {fans}")
        print(f"Fans Group: {fans_group}")
        print(f"Reputation: {reputation}")
        print(f"Star Chart: {star_chart}")
        print(f"Live Sales: {live_sales}")
        print(f"Video Sales: {video_sales}")
        print(f"Fans Level: {fans_level}")
        print(f"Main Type: {main_type}")
        print(f"Sales Level: {sales_level}")
        print(f"Sales Info: {sales_info}")


    except Exception as e:

        print(f"An error occurred: {e}")

    finally:

        # 关闭当前标签页并返回之前的标签页

        if len(driver.window_handles) > 1:
            driver.close()

            driver.switch_to.window(driver.window_handles[-1])


# 调用函数
chrome_options = Options()
chrome_options.headless = True
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(executable_path='C:\\Program Files\\Google\\Chrome\\Application\\chromedriver.exe', options=chrome_options)
urls = [
    "https://www.chanmama.com/authorDetail/597777635089248",
    "https://www.chanmama.com/authorDetail/3302560861541796",
    "https://www.chanmama.com/authorDetail/104668612937",
    "https://www.chanmama.com/authorDetail/101531655586",
    "https://www.chanmama.com/authorDetail/1284685414020615"
]
@profile
def text(driver,urls):
    for url in urls:
        fetch_data(driver, url)
text(driver,urls)
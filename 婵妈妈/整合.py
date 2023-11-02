from selenium import webdriver
import socket
import time
import pandas as pd
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import random
from lxml import etree
import os

def is_chrome_running_on_debugger_address(address):
    host, port = address.split(':')
    try:
        socket.create_connection((host, int(port)))
        return True  # Chrome is running on the specified address
    except ConnectionRefusedError:
        return False  # Chrome is not running on the specified address

class WebScraper:
    def __init__(self,max_merchandise_pages = 10,url_prefix='https://www.chanmama.com'):
        self.debugger_address = "127.0.0.1:9222"
        self.max_merchandise_pages = max_merchandise_pages  # 设置最大页面数
        self.table_name = 'default_table_name'  # 设置表格名称
        self.merchandise_page_interval = 2  # 设置页面切换间隔
        self.merchandise_page_autosave_interval = 60  # 设置自动保存间隔
        self.driver = None  # 初始化 driver
        self.url_prefix=url_prefix
        self.column_lst = None
        self.directory_name = '婵妈妈excel数据'
        self.path = ''
    # 初始化网页
    def current_date(self):
        today = datetime.today()
        formatted_date = today.strftime('%yyyy.%m.%d')
        return formatted_date##

    def wait_loading_data(self, driver):
        while 1:
            driver.implicitly_wait(0)
            if driver.find_elements_by_class_name('vue-loading'):
                time.sleep(0.01)
            else:
                break

    def configure_chrome_debugger_address(self):
        while True:
            if is_chrome_running_on_debugger_address(self.debugger_address):
                print("Chrome浏览器已被正确打开.")
                break
            else:
                print("Chrome浏览器未被正确打开，请你打开正确的浏览器")
                print('请在cmd端口输入以下代码:')
                print('"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\\seleniumAutomationProfile"')
                user_input = input("如果已打开浏览器，请输入 1,然后回车: ")
                if user_input == "1":
                    continue
                else:
                    print("你的输入不正确，请打通过cmd端口打开浏览器后，再次尝试")
                    time.sleep(5)

    def check_and_maximize_window(self):
        if not self.driver:
            self.initialize_driver()  # 如果尚未初始化驱动，请进行初始化

        # 获取窗口位置
        window_position = self.driver.get_window_position()
        is_maximized = window_position['x'] == 0 and window_position['y'] == 0

        if not is_maximized:
            self.driver.maximize_window()  # 如果窗口不是最大化，将其最大化
            print("窗口已最大化。")
        else:
            print("窗口已经是最大化的，不需要进行操作.")

    def initialize_driver(self):
        # 初始化 WebDriver
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", self.debugger_address)
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(20)

    # 每一个库的爬虫
    def xiaodian_data(self):
        table_name = '小店库数据'
        url_prefix = self.url_prefix
        if self.column_lst is None:
            column_lst = ['抖音小店title', '抖音小店链接', '商家体验分', '动销商品数', '客单价', '销量', '销售额', '关联达人数', '关联直播数', '关联视频数']

        # Add your web scraping logic here
        # Get current date
        date_str = self.current_date()
        # Generate a random number
        rand_num = random.randint(0, 9999)
        rand_num_str = f"{rand_num:04d}"

        df_table = pd.DataFrame()

        cur_page = 1
        while cur_page <= self.max_merchandise_pages:
            self.wait_loading_data(self.driver)
            time.sleep(self.merchandise_page_interval)
            page_lst = []  # 收集每一页的数据
            print(f'当前页是第{cur_page}页!')

            tree = etree.HTML(self.driver.page_source)  # 将页面源码转为etree格式，加快解析速度

            row_lst = tree.xpath('//*[@id="app"]/div[1]/div[2]/div/div/div/div[2]/div[2]/div[1]/div/div/table/tbody/tr')

            for _row in row_lst:
                row_lst = []  # 收集每一行的数据
                tikstore_url = url_prefix + _row.xpath('.//td[1]/div/div[2]/div/div[1]/a/@href')[0].strip()
                tikstore_title = _row.xpath('.//td[1]/div/div[2]/div/div[1]/a')[0].text.strip()
                merchant_experience_score = _row.xpath('.//td[2]/div')[0].text.strip()
                onsale_merchandise_num = _row.xpath('.//td[3]/div')[0].text.strip()
                per_customer_price = _row.xpath('.//td[4]/div')[0].text.strip()
                sales_volume = _row.xpath('.//td[5]/div')[0].text.strip()
                sales = _row.xpath('.//td[6]/div')[0].text.strip()
                related_blogger_num = _row.xpath('.//td[7]/div')[0].text.strip()
                related_live_num = _row.xpath('.//td[8]/div')[0].text.strip()
                related_video_num = _row.xpath('.//td[9]/div')[0].text.strip()

                row_lst.append(tikstore_title)
                row_lst.append(tikstore_url)
                row_lst.append(merchant_experience_score)
                row_lst.append(onsale_merchandise_num)
                row_lst.append(per_customer_price)
                row_lst.append(sales_volume)
                row_lst.append(sales)
                row_lst.append(related_blogger_num)
                row_lst.append(related_live_num)
                row_lst.append(related_video_num)

                page_lst.append(row_lst)

            df_table = pd.concat([df_table, pd.DataFrame(page_lst, columns=column_lst,
                                                         index=[x + len(df_table) for x in range(len(page_lst))])],
                                 axis=0,
                                 sort=False)

            self.driver.implicitly_wait(0)
            right_arrow_button = self.driver.find_elements_by_class_name('btn-next')
            if right_arrow_button and right_arrow_button[0].is_enabled():
                print('翻至下一页！')
                self.driver.implicitly_wait(5)
                right_arrow_button[0].click()
            else:
                print('翻至最后一页！退出！')
                break

            if cur_page % self.merchandise_page_autosave_interval == 0:
                writer = pd.ExcelWriter(f'{table_name}-{date_str}-{rand_num_str}.xlsx', engine='xlsxwriter',
                                        options={'strings_to_urls': False})
                df_table.to_excel(writer, index=None)
                writer.close()
                print('自动保存！')

            cur_page += 1

        writer = pd.ExcelWriter(os.path.join(self.path, f'{table_name}-{self.current_date()}-{rand_num_str}.xlsx'),
                                engine='xlsxwriter')
        df_table.to_excel(writer, index=None)
        writer.close()

    def shangping_data(self):
        table_name = '商品库'
        url_prefix = self.url_prefix
        rand_num = random.randint(0, 9999)
        rand_num_str = f"{rand_num:04d}"
        if self.column_lst is None:
            column_lst = ['商品名称', '商品链接', '商品价格', '佣金比例', '近XX天销量', '直播销量', '视频销量', '商品卡销量', '关联达人', '关联直播', '关联视频']

        df_table = pd.DataFrame()

        cur_page = 1
        while cur_page <= self.max_merchandise_pages:
            self.wait_loading_data(self.driver)
            time.sleep(self.merchandise_page_interval)
            page_lst = []  # 收集每一页的数据
            print(f'当前页是第{cur_page}页!')

            tree = etree.HTML(self.driver.page_source)  # 将页面源码转为etree格式，加快解析速度
            row_lst = tree.xpath('//*[@id="e2e-product-search-table"]/tbody/tr')

            for _row in row_lst:
                row_lst = []  # 收集每一行的数据
                merchandise_url = url_prefix + _row.xpath('./td[1]/div/a/@href')[0].strip()
                merchandise_title = _row.xpath('./td[1]/div/div/div[1]/a')[0].text.strip()
                merchandise_price = _row.xpath('./td[1]/div/div/div[2]/div[1]/span')[0].text.strip()

                commision_rate = ''.join(_row.xpath('./td[2]/div//text()'))
                if '蝉选' in commision_rate:
                    commision_rate = ''.join(_row.xpath('./td[2]/div/div/div[1]//text()'))
                else:
                    commision_rate = _row.xpath('./td[2]/div/span')[0].text.strip()

                near_day_sales = _row.xpath('./td[3]/div/div')[0].text.strip()
                live_sales = _row.xpath('./td[4]/div')[0].text.strip()
                video_sales = _row.xpath('./td[5]/div')[0].text.strip()
                merchandise_card_sales = _row.xpath('./td[6]/div')[0].text.strip()
                related_blogger_num = _row.xpath('./td[7]/div')[0].text.strip()
                related_live_num = _row.xpath('./td[8]/div')[0].text.strip()
                related_video_num = _row.xpath('./td[9]/div')[0].text.strip()

                row_lst.append(merchandise_title)
                row_lst.append(merchandise_url)
                row_lst.append(merchandise_price)
                row_lst.append(commision_rate)
                row_lst.append(near_day_sales)
                row_lst.append(live_sales)
                row_lst.append(video_sales)
                row_lst.append(merchandise_card_sales)
                row_lst.append(related_blogger_num)
                row_lst.append(related_live_num)
                row_lst.append(related_video_num)

                page_lst.append(row_lst)

            df_table = pd.concat([df_table, pd.DataFrame(page_lst, columns=column_lst,
                                                         index=[x + len(df_table) for x in range(len(page_lst))])],
                                 axis=0,
                                 sort=False)

            right_arrow_button = self.driver.find_elements_by_class_name('btn-next')
            if (not right_arrow_button) or (not right_arrow_button[0].is_enabled()) or (len(df_table) == 0):
                print('翻至最后一页！退出！')
                break
            else:
                self.driver.implicitly_wait(5)
                right_arrow_button[0].click()

            if cur_page % self.merchandise_page_autosave_interval == 0:
                writer = pd.ExcelWriter(f'{table_name}-{self.current_date()}-{rand_num_str}.xlsx',
                                        engine='xlsxwriter')
                df_table.to_excel(writer, index=None)
                writer.close()
                print('自动保存！')

            cur_page += 1
        print(self.path)
        writer = pd.ExcelWriter(os.path.join(self.path, f'{table_name}-{self.current_date()}-{rand_num_str}.xlsx'),
                                engine='xlsxwriter')
        df_table.to_excel(writer, index=None)
        writer.close()

    def blogger_data(self):
        table_name = '达人库'
        url_prefix = self.url_prefix
        rand_num = random.randint(0, 9999)
        rand_num_str = f"{rand_num:04d}"
        if self.column_lst is None:
            column_lst = ['达人title','达人链接','粉丝总量','粉丝增量','平均点赞数','平均赞粉比','直播场次','平均直播场观','场均销售额']

        df_table = pd.DataFrame()

        cur_page = 1
        while cur_page <= self.max_merchandise_pages:
            self.wait_loading_data(self.driver)
            time.sleep(self.merchandise_page_interval)
            page_lst = []  # 收集每一页的数据
            print(f'当前页是第{cur_page}页!')

            tree = etree.HTML(self.driver.page_source)  # 将页面源码转为etree格式，加快解析速度
            row_lst = tree.xpath('//*[@id="app"]/div[1]/div[2]/div/div[1]/div/div[2]/div[2]/div[1]/div/div/div/div[2]/table/tbody/tr')

            for _row in row_lst:
                row_lst = []
                # 达人链接
                # //*[@id="app"]/div[1]/div[2]/div/div[1]/div/div[2]/div[2]/div[1]/div/div/div/div[2]/table/tbody/tr[1]/td[1]/div/div/div[1]/a
                blogger_url = url_prefix + _row.xpath('./td[1]/div/div/div[1]/a/@href')[0].strip()
                # print(blogger_url)

                # 达人title
                # //*[@id="app"]/div[1]/div[2]/div/div[1]/div/div[2]/div[2]/div[1]/div/div/div/div[2]/table/tbody/tr[1]/td[1]/div/div/div[1]/a
                blogger_title = _row.xpath('./td[1]/div/div/div[1]/a')[0].text.strip()
                # print(blogger_title)

                # 粉丝总量
                # //*[@id="app"]/div[1]/div[2]/div/div[1]/div/div[2]/div[2]/div[1]/div/div/div/div[2]/table/tbody/tr[1]/td[2]/div
                fans_total_num = _row.xpath('./td[2]/div')[0].text.strip()
                # print(fans_total_num)

                # 粉丝增量
                # //*[@id="app"]/div[1]/div[2]/div/div[1]/div/div[2]/div[2]/div[1]/div/div/div/div[2]/table/tbody/tr[1]/td[3]/div
                fans_increment_num = _row.xpath('./td[3]/div')[0].text.strip()
                # print(fans_increment_num)

                # 平均点赞数
                # //*[@id="app"]/div[1]/div[2]/div/div[1]/div/div[2]/div[2]/div[1]/div/div/div/div[2]/table/tbody/tr[1]/td[4]/div
                avg_like_num = _row.xpath('./td[4]/div')[0].text.strip()
                # print(avg_like_num)

                # 平均赞粉比
                # //*[@id="app"]/div[1]/div[2]/div/div[1]/div/div[2]/div[2]/div[1]/div/div/div/div[2]/table/tbody/tr[1]/td[5]/div
                avg_like_fans_ratio = _row.xpath('./td[5]/div')[0].text.strip()
                # print(avg_like_fans_ratio)

                # 直播场次
                # //*[@id="app"]/div[1]/div[2]/div/div[1]/div/div[2]/div[2]/div[1]/div/div/div/div[2]/table/tbody/tr[1]/td[6]/div
                live_num = _row.xpath('./td[6]/div')[0].text.strip()
                # print(live_num)

                # 平均直播场观
                # //*[@id="app"]/div[1]/div[2]/div/div[1]/div/div[2]/div[2]/div[1]/div/div/div/div[2]/table/tbody/tr[1]/td[7]/div
                avg_live_watch_num = _row.xpath('./td[7]/div')[0].text.strip()
                # print(avg_live_watch_num)

                # 场均销售额
                # //*[@id="app"]/div[1]/div[2]/div/div[1]/div/div[2]/div[2]/div[1]/div/div/div/div[2]/table/tbody/tr[1]/td[8]/div
                avg_live_sales = _row.xpath('./td[8]/div')[0].text.strip()
                # print(avg_live_sales)

                row_lst.append(blogger_title)
                row_lst.append(blogger_url)
                row_lst.append(fans_total_num)
                row_lst.append(fans_increment_num)
                row_lst.append(avg_like_num)
                row_lst.append(avg_like_fans_ratio)
                row_lst.append(live_num)
                row_lst.append(avg_live_watch_num)
                row_lst.append(avg_live_sales)

                page_lst.append(row_lst)

            df_table = pd.concat([df_table, pd.DataFrame(page_lst,
                                                        columns=column_lst,
                                                        index=[x + len(df_table) for x in range(len(page_lst))])],
                                axis=0,
                                sort=False)

            right_arrow_button = self.driver.find_elements_by_class_name('btn-next')
            if (not right_arrow_button) or (not right_arrow_button[0].is_enabled()) or (len(df_table) == 0):
                print('翻至最后一页！退出！')
                break
            else:
                self.driver.implicitly_wait(5)
                right_arrow_button[0].click()

            if cur_page % self.merchandise_page_autosave_interval == 0:
                writer = pd.ExcelWriter(f'{table_name}-{self.current_date()}-{rand_num_str}.xlsx',
                                        engine='xlsxwriter')
                df_table.to_excel(writer, index=None)
                writer.close()
                print('自动保存！')

            cur_page += 1

        writer = pd.ExcelWriter(os.path.join(self.path, f'{table_name}-{self.current_date()}-{rand_num_str}.xlsx'),
                                engine='xlsxwriter')
        df_table.to_excel(writer, index=None)
        writer.close()

    def daihuo_video_data(self):
        table_name = '带货视频库'
        url_prefix = self.url_prefix
        rand_num = random.randint(0, 9999)
        rand_num_str = f"{rand_num:04d}"

        if self.column_lst is None:
            column_lst = ['视频title', '视频链接', '达人title', '达人url', '点赞数', '评论数', '转发数', '销量', '销售额']

        df_table = pd.DataFrame()

        cur_page = 1
        while cur_page <= self.max_merchandise_pages:
            self.wait_loading_data(self.driver)
            time.sleep(self.merchandise_page_interval)
            page_lst = []  # 收集每一页的数据
            print(f'当前页是第{cur_page}页!')

            tree = etree.HTML(self.driver.page_source)
            row_lst = tree.xpath(
                '//*[@id="app"]/div[1]/div[2]/div/div/div/div[2]/div/div[2]/div/div/div[2]/table/tbody/tr')


            for _row in row_lst:
                video_url_element = _row.xpath('./td[1]/div/div[2]/div[1]/a')
                if not video_url_element:
                    continue  # 跳过没有视频链接的行

                video_url = url_prefix + video_url_element[0].get("href").strip()
                video_title = video_url_element[0].text.strip()

                blogger_url_element = _row.xpath('./td[2]/div/div[2]/div[1]/a')
                if not blogger_url_element:
                    continue  # 跳过没有达人链接的行

                blogger_url = url_prefix + blogger_url_element[0].get("href").strip()
                blogger_title = blogger_url_element[0].text.strip()

                like_num = _row.xpath('./td[3]/div')[0].text.strip()
                comment_num = _row.xpath('./td[4]/div')[0].text.strip()
                forward_num = _row.xpath('./td[5]/div')[0].text.strip()
                sales_volume = _row.xpath('./td[6]/div')[0].text.strip()
                sales = _row.xpath('./td[7]/div')[0].text.strip()

                row_lst = [video_title, video_url, blogger_title, blogger_url, like_num, comment_num, forward_num,
                           sales_volume, sales]
                page_lst.append(row_lst)

            df_table = pd.concat([df_table, pd.DataFrame(page_lst, columns=column_lst)], axis=0, sort=False)

            right_arrow_button = self.driver.find_elements_by_class_name('btn-next')
            if (not right_arrow_button) or (not right_arrow_button[0].is_enabled()) or (len(df_table) == 0):
                print('翻至最后一页！退出！')
                break
            else:
                self.driver.implicitly_wait(5)
                right_arrow_button[0].click()

            if cur_page % self.merchandise_page_autosave_interval == 0:
                writer = pd.ExcelWriter(f'{table_name}-{self.current_date()}-{rand_num_str}.xlsx', engine='xlsxwriter')
                df_table.to_excel(writer, index=None)
                writer.close()
                print('自动保存！')

            cur_page += 1

        writer = pd.ExcelWriter(os.path.join(self.path, f'{table_name}-{self.current_date()}-{rand_num_str}.xlsx'),
                                engine='xlsxwriter')
        df_table.to_excel(writer, index=None)
        writer.close()

    def hot_video_data(self):
        table_name = '热门视频库'
        url_prefix = self.url_prefix
        rand_num = random.randint(0, 9999)
        rand_num_str = f"{rand_num:04d}"

        if self.column_lst is None:
            column_lst = ['视频title','视频链接','达人title','达人url','点赞数','评论数','转发数']

        df_table = pd.DataFrame()

        cur_page = 1
        while cur_page <= self.max_merchandise_pages:
            self.wait_loading_data(self.driver)
            time.sleep(self.merchandise_page_interval)
            page_lst = []  # 收集每一页的数据
            print(f'当前页是第{cur_page}页!')

            tree = etree.HTML(self.driver.page_source)
            row_lst = tree.xpath('//*[@id="app"]/div[1]/div[2]/div/div/div/div[2]/div[2]/div/div/div[2]/table/tbody/tr')
            print(len(row_lst))
            for _row in row_lst:
                row_lst = []  # 收集每一行的数据

                # 视频链接
                # //*[@id="app"]/div[1]/div[2]/div/div/div/div[2]/div[2]/div/div/div[2]/table/tbody/tr[1]/td[1]/div/div[2]/div/a
                video_url = url_prefix + _row.xpath('.//td[1]/div/div[2]/div/a/@href')[0].strip()
                # print(video_url)

                # 视频title
                # //*[@id="app"]/div[1]/div[2]/div/div/div/div[2]/div[2]/div/div/div[2]/table/tbody/tr[1]/td[1]/div/div[2]/div/a
                video_title = _row.xpath('.//td[1]/div/div[2]/div/a')[0].text.strip()
                # print(video_title)

                # 达人url
                # //*[@id="app"]/div[1]/div[2]/div/div/div/div[2]/div[2]/div/div/div[2]/table/tbody/tr[1]/td[2]/div/div[2]/div[1]/a
                blogger_url = url_prefix + _row.xpath('.//td[2]/div/div[2]/div[1]/a/@href')[0].strip()
                # print(blogger_url)

                # 达人title
                # //*[@id="app"]/div[1]/div[2]/div/div/div/div[2]/div[2]/div/div/div[2]/table/tbody/tr[1]/td[2]/div/div[2]/div[1]/a
                blogger_title = _row.xpath('.//td[2]/div/div[2]/div[1]/a')[0].text.strip()
                # print(blogger_title)

                # 点赞数
                # //*[@id="app"]/div[1]/div[2]/div/div/div/div[2]/div[2]/div/div/div[2]/table/tbody/tr[1]/td[3]/div
                like_num = _row.xpath('.//td[3]/div')[0].text.strip()
                # print(like_num)

                # 评论数
                # //*[@id="app"]/div[1]/div[2]/div/div/div/div[2]/div[2]/div/div/div[2]/table/tbody/tr[1]/td[4]/div
                comment_num = _row.xpath('.//td[4]/div')[0].text.strip()
                # print(comment_num)

                # 转发数
                # //*[@id="app"]/div[1]/div[2]/div/div/div/div[2]/div[2]/div/div/div[2]/table/tbody/tr[1]/td[5]/div
                forward_num = _row.xpath('.//td[5]/div')[0].text.strip()
                # print(forward_num)
                row_lst.append(video_title)
                row_lst.append(video_url)
                row_lst.append(blogger_title)
                row_lst.append(blogger_url)
                row_lst.append(like_num)
                row_lst.append(comment_num)
                row_lst.append(forward_num)

                page_lst.append(row_lst)

            df_table = pd.concat([df_table, pd.DataFrame(page_lst, columns=column_lst)], axis=0, sort=False)

            right_arrow_button = self.driver.find_elements_by_class_name('btn-next')
            if (not right_arrow_button) or (not right_arrow_button[0].is_enabled()) or (len(df_table) == 0):
                print('翻至最后一页！退出！')
                break
            else:
                self.driver.implicitly_wait(5)
                right_arrow_button[0].click()

            if cur_page % self.merchandise_page_autosave_interval == 0:
                writer = pd.ExcelWriter(f'{table_name}-{self.current_date()}-{rand_num_str}.xlsx', engine='xlsxwriter')
                df_table.to_excel(writer, index=None)
                writer.close()
                print('自动保存！')

            cur_page += 1

        writer = pd.ExcelWriter(os.path.join(self.path, f'{table_name}-{self.current_date()}-{rand_num_str}.xlsx'),engine='xlsxwriter')
        df_table.to_excel(writer, index=None)
        writer.close()

    def pingpai_data(self):
        table_name = '品牌库'
        url_prefix = self.url_prefix
        rand_num = random.randint(0, 9999)
        rand_num_str = f"{rand_num:04d}"

        if self.column_lst is None:
            column_lst = ['品牌title','品牌url','商品数','销量','销售额','关联达人数','关联视频数','关联直播数','关联小店数']

        df_table = pd.DataFrame()

        cur_page = 1
        while cur_page <= self.max_merchandise_pages:
            self.wait_loading_data(self.driver)
            time.sleep(self.merchandise_page_interval)
            page_lst = []  # 收集每一页的数据
            print(f'当前页是第{cur_page}页!')

            tree = etree.HTML(self.driver.page_source)
            row_lst = tree.xpath('//*[@id="app"]/div[1]/div[2]/div/div/div/div[2]/div[2]/div[1]/div/div/table/tbody/tr')
            #print(len(row_lst))
            row_num = 0
            for _row in row_lst:
                row_lst = []  # 收集每一行的数据

                # 品牌url
                # //*[@id="app"]/div[1]/div[2]/div/div/div/div[2]/div[2]/div[1]/div/div/table/tbody/tr[1]/td[1]/div/div[2]/div/div[1]/a
                # brand_url = _row.find_element_by_xpath('./td[1]/div/div[2]/div/div[1]/a').get_attribute('href').strip()
                brand_url = url_prefix + _row.xpath('./td[1]/div/div[2]/div/div[1]/a/@href')[0].strip()
                # print(brand_url)

                # 品牌title
                # //*[@id="app"]/div[1]/div[2]/div/div/div/div[2]/div[2]/div[1]/div/div/table/tbody/tr[1]/td[1]/div/div[2]/div/div[1]/a
                # brand_title = _row.find_element_by_xpath('./td[1]/div/div[2]/div/div[1]/a')[0].text.strip()
                brand_title = _row.xpath('./td[1]/div/div[2]/div/div[1]/a')[0].text.strip()
                # print(brand_title)

                # 商品数
                # //*[@id="app"]/div[1]/div[2]/div/div/div/div[2]/div[2]/div[1]/div/div/table/tbody/tr[1]/td[2]/div
                # merchandise_num = _row.find_element_by_xpath('./td[2]/div').text.strip()
                merchandise_num = _row.xpath('./td[2]/div')[0].text.strip()
                # print(merchandise_num)

                # 销量
                # //*[@id="app"]/div[1]/div[2]/div/div/div/div[2]/div[2]/div[1]/div/div/table/tbody/tr[1]/td[3]/div
                # sales_volume = _row.find_element_by_xpath('./td[3]/div').text.strip()
                sales_volume = _row.xpath('./td[3]/div')[0].text.strip()
                # print(sales_volume)

                # 销售额
                # //*[@id="app"]/div[1]/div[2]/div/div/div/div[2]/div[2]/div[1]/div/div/table/tbody/tr[1]/td[4]/div
                # sales = _row.find_element_by_xpath('./td[4]/div').text.strip()
                sales = _row.xpath('./td[4]/div')[0].text.strip()
                # print(sales)

                # 关联达人数
                # //*[@id="app"]/div[1]/div[2]/div/div/div/div[2]/div[2]/div[1]/div/div/table/tbody/tr[1]/td[5]/div
                # related_blogger_num = _row.find_element_by_xpath('./td[5]/div').text.strip()
                related_blogger_num = _row.xpath('./td[5]/div')[0].text.strip()
                # print(related_blogger_num)

                # 关联视频数
                # //*[@id="app"]/div[1]/div[2]/div/div/div/div[2]/div[2]/div[1]/div/div/table/tbody/tr[1]/td[6]/div
                # related_video_num = _row.find_element_by_xpath('./td[6]/div').text.strip()
                related_video_num = _row.xpath('./td[6]/div')[0].text.strip()
                # print(related_video_num)

                # 关联直播数
                # //*[@id="app"]/div[1]/div[2]/div/div/div/div[2]/div[2]/div[1]/div/div/table/tbody/tr[1]/td[7]/div
                # related_live_num = _row.find_element_by_xpath('./td[7]/div').text.strip()
                related_live_num = _row.xpath('./td[7]/div')[0].text.strip()
                # print(related_live_num)

                # 关联小店数
                # //*[@id="app"]/div[1]/div[2]/div/div/div/div[2]/div[2]/div[1]/div/div/table/tbody/tr[1]/td[8]/div
                # related_tikstore_num = _row.find_element_by_xpath('./td[8]/div').text.strip()
                related_tikstore_num = _row.xpath('./td[8]/div')[0].text.strip()
                # print(related_tikstore_num)

                row_lst.append(brand_title)
                row_lst.append(brand_url)
                row_lst.append(merchandise_num)
                row_lst.append(sales_volume)
                row_lst.append(sales)
                row_lst.append(related_blogger_num)
                row_lst.append(related_video_num)
                row_lst.append(related_live_num)
                row_lst.append(related_tikstore_num)

                page_lst.append(row_lst)

                # print(row_num)
                row_num += 1

            df_table = pd.concat([df_table, pd.DataFrame(page_lst, columns=column_lst)], axis=0, sort=False)

            right_arrow_button = self.driver.find_elements_by_class_name('btn-next')
            if (not right_arrow_button) or (not right_arrow_button[0].is_enabled()) or (len(df_table) == 0):
                print('翻至最后一页！退出！')
                break
            else:
                self.driver.implicitly_wait(5)
                right_arrow_button[0].click()

            if cur_page % self.merchandise_page_autosave_interval == 0:
                writer = pd.ExcelWriter(f'{table_name}-{self.current_date()}-{rand_num_str}.xlsx', engine='xlsxwriter')
                df_table.to_excel(writer, index=None)
                writer.close()
                print('自动保存！')

            cur_page += 1

        writer = pd.ExcelWriter(os.path.join(self.path, f'{table_name}-{self.current_date()}-{rand_num_str}.xlsx'),
                                engine='xlsxwriter')
        df_table.to_excel(writer, index=None)
        writer.close()

    def live_data(self):
        table_name = '直播库'
        url_prefix = self.url_prefix
        rand_num = random.randint(0, 9999)
        rand_num_str = f"{rand_num:04d}"

        if self.column_lst is None:
            column_lst = ['直播title','直播（静态）链接','达人title','达人url','开播时间','直播时长','人气峰值','观看人次','商品数','销售额','销量']

        df_table = pd.DataFrame()

        cur_page = 1
        while cur_page <= self.max_merchandise_pages:
            self.wait_loading_data(self.driver)
            time.sleep(self.merchandise_page_interval)
            page_lst = []  # 收集每一页的数据
            print(f'当前页是第{cur_page}页!')

            tree = etree.HTML(self.driver.page_source)
            row_element_lst = tree.xpath('//*[@id="e2e-live-search-table"]/tbody/tr')
            # print(len(row_lst))
            row_num = 0
            for _row in row_element_lst:
                row_lst = []  # 收集每一行的数据

                # 直播（静态）链接
                # //*[@id="e2e-live-search-table"]/tbody/tr[1]/td[1]/div/div[2]/div/a
                # print(type(_row))
                # todo-
                live_static_url = url_prefix + _row.xpath('./td[1]/div/div[2]/div/a/@href')[0].strip()
                # print(live_static_url)
                # exit(0)

                # 直播title
                # //*[@id="app"]/div[1]/div[2]/div/div[1]/div/div[2]/div[2]/div[1]/div/div/div/div[2]/table/tbody/tr[1]/td[1]/div/div/div[1]/a
                live_title = _row.xpath('./td[1]/div/div[2]/div/a')[0].text.strip()
                # print(live_title)

                # 达人url
                # //*[@id="e2e-live-search-table"]/tbody/tr[1]/td[2]/div/div/div[1]/a
                blogger_url = url_prefix + _row.xpath('./td[2]/div/div/div[1]/a/@href')[0].strip()
                # print(blogger_url)

                # 达人title
                # //*[@id="e2e-live-search-table"]/tbody/tr[1]/td[2]/div/div/div[1]/a
                blogger_title = _row.xpath('./td[2]/div/div/div[1]/a')[0].text.strip()
                # print(blogger_title)

                # 开播时间
                # //*[@id="e2e-live-search-table"]/tbody/tr[1]/td[3]/div
                live_begin_time = _row.xpath('./td[3]/div')[0].text.strip()
                # print(live_begin_time)

                # 直播时长
                # //*[@id="e2e-live-search-table"]/tbody/tr[1]/td[4]/div
                live_duration = _row.xpath('./td[4]/div')[0].text.strip()
                # print(live_duration)

                # 人气峰值
                # //*[@id="e2e-live-search-table"]/tbody/tr[1]/td[5]
                popularity_peek = _row.xpath('./td[5]')[0].text.strip()
                # print(popularity_peek)

                # 观看人次
                # //*[@id="e2e-live-search-table"]/tbody/tr[1]/td[6]
                watch_num = _row.xpath('./td[6]')[0].text.strip()
                # print(watch_num)

                # 商品数
                # //*[@id="e2e-live-search-table"]/tbody/tr[1]/td[7]/div
                # 商品数
                merchandise_elements = _row.xpath('.//td[7]/div')
                if merchandise_elements and merchandise_elements[0].text is not None:
                    merchandise_num = merchandise_elements[0].text.strip()
                else:
                    merchandise_num = "-"  # 或者选择一个合适的默认值或占位符

                # 销售额
                sales_elements = _row.xpath('.//td[8]/div')
                if sales_elements and sales_elements[0].text is not None:
                    sales = sales_elements[0].text.strip()
                else:
                    sales = "-"  # 或者选择一个合适的默认值或占位符

                # 销量
                sales_volume_elements = _row.xpath('.//td[9]/div')
                if sales_volume_elements and sales_volume_elements[0].text is not None:
                    sales_volume = sales_volume_elements[0].text.strip()
                else:
                    sales_volume = "-"  # 或者选择一个合适的默认值或占位符

                row_lst.append(live_title)
                row_lst.append(live_static_url)
                row_lst.append(blogger_title)
                row_lst.append(blogger_url)
                row_lst.append(live_begin_time)
                row_lst.append(live_duration)
                row_lst.append(popularity_peek)
                row_lst.append(watch_num)
                row_lst.append(merchandise_num)
                row_lst.append(sales)
                row_lst.append(sales_volume)

                page_lst.append(row_lst)

            df_table = pd.concat([df_table, pd.DataFrame(page_lst, columns=column_lst)], axis=0, sort=False)

            right_arrow_button = self.driver.find_elements_by_class_name('btn-next')
            if (not right_arrow_button) or (not right_arrow_button[0].is_enabled()) or (len(df_table) == 0):
                print('翻至最后一页！退出！')
                break
            else:
                self.driver.implicitly_wait(5)
                right_arrow_button[0].click()

            if cur_page % self.merchandise_page_autosave_interval == 0:
                writer = pd.ExcelWriter(f'{table_name}-{self.current_date()}-{rand_num_str}.xlsx', engine='xlsxwriter')
                df_table.to_excel(writer, index=None)
                writer.close()
                print('自动保存！')

            cur_page += 1

        writer = pd.ExcelWriter(os.path.join(self.path, f'{table_name}-{self.current_date()}-{rand_num_str}.xlsx'), engine='xlsxwriter')
        df_table.to_excel(writer, index=None)
        writer.close()

    def xlsx_path(self):
        current_directory = os.getcwd()
        # 拼接文件夹路径
        directory_path = os.path.join(current_directory, self.directory_name)
        self.path = directory_path
        # 检查文件夹是否已存在
        if not os.path.exists(directory_path):
            # 如果不存在，创建文件夹
            os.makedirs(directory_path)
            print(f"文件夹 '{self.directory_name}' 创建成功")
        else:
            print(f"文件夹 '{self.directory_name}' 已存在")

    def set_params(self, param1):
        self.max_merchandise_pages = int(param1)

def main():
    s = WebScraper()
    s.xlsx_path()
    s.configure_chrome_debugger_address()
    s.check_and_maximize_window()
    print('使用说明:必须访问到相对应的数据库才能使用对应的功能，否则会报错！！')
    print('默认爬虫页数为10页，如您需要修改，请按照下面的指示修改')
    print('您可以先找到对应的库，然后输入好您所需要的内容和页数，详情看文档！')
    while True:
        print("\n请选择你要爬的数据库功能:")
        print("1. 小店库")
        print("2. 商品库")
        print("3. 达人库")
        print("4. 带货视频库")
        print("5. 热门视频库")
        print("6. 品牌库")
        print("7. 直播库")
        print("8. 修改爬虫页数")
        print("0. 退出程序")

        choice = input("\n请按数字输入您的选择: ")

        if choice == "1":
            s.xiaodian_data()
        elif choice == "2":
            s.shangping_data()
        elif choice == "3":
            s.blogger_data()
        elif choice == "4":
            s.daihuo_video_data()
        elif choice == "5":
            s.hot_video_data()
        elif choice == "6":
            s.pingpai_data()
        elif choice == "7":
            s.live_data()
        elif choice == "8":
            new_param = input("请输入新的爬虫页数: ")
            s.set_params(new_param)
        elif choice == "0":
            print("程序结束")
            break
        else:
            print("无效选择，请重新输入")
if __name__ == '__main__':
    main()


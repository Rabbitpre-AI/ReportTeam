from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import *
import asyncio
import time
import pandas as pd
import os
from pyppeteer import connect
from datetime import datetime, timedelta
import random



class WebScraper:
    def __init__(self):
        self.debugger_address = "127.0.0.1:9222"
        self.table_name = 'default_table_name'  # 设置表格名称
        self.driver = None  # 初始化 driver
        self.url_prefix = 'https://www.chanmama.com'
        self.column_lst = None
        self.directory_name = '婵妈妈excel数据'
        self.path = ''
        self.canvas_selector = None
        self.time_selector = None
        self.data_selectors = None
        self.data_selectors = None
        self.custom_scroll_num = 300
        self.test = 3
    async def init(self):
        self.browser = await connect(browserURL='http://127.0.0.1:9222', defaultViewport=None)
        self.pages = await self.browser.pages()
        self.page = self.pages[0]
    # 鼠标点击--关键字
    async def mouse_text(self,page, text):
        try:
            # 使用XPath选择器来定位文本内容为给定text的元素
            target_elements = await page.xpath(f"//*[text()='{text}']")

            if target_elements:
                await target_elements[0].click()
                # print(f'"{text}"按钮已被点击')
            else:
                print(f'没有找到文本为"{text}"的元素')
        except Exception as e:
            print(f"处理文本为'{text}'的元素时出错: {e}")
    # 鼠标点击--xpath
    async def mouse(self,page, xpath):
        try:
            target_elements = await page.xpath(xpath)

            if target_elements:
                await target_elements[0].click()
                await asyncio.sleep(1)  # 异步等待，非阻塞
            else:
                print(f'没有找到xpath为"{xpath}"的元素')
        except Exception as e:
            print(f"处理xpath为'{xpath}'的元素时出错: {e}")

    # 从下往上滚动
    async def fans_up_to_down(self,page, num_data_points, canvas_xpath, time_xpath, data_xpaths, data_names, test ,timeout=5000):
        data_list = []  # 用于存储所有行的列表

        try:
            # 检查canvas元素是否存在
            canvas_elements = await page.xpath(canvas_xpath)
            if not canvas_elements:
                print("Canvas元素不存在或不可见")
                return None

            # 获取canvas的位置信息
            canvas_info = await page.evaluate(f"""
                (element) => {{
                    const {{ x, y, width, height }} = element.getBoundingClientRect();
                    return {{ x, y, width, height }};
                }}
            """, canvas_elements[0])

            bottom_y = canvas_info['y'] + canvas_info['height']
            top_y = canvas_info['y']
            interval = (bottom_y - top_y) / (num_data_points - 1)

            for i in range(num_data_points):
                hover_y = bottom_y - interval * i
                # print('x的数据：',canvas_info['x'] + canvas_info['width'] /test)
                await page.mouse.move(canvas_info['x'] + canvas_info['width'] / test, hover_y)

                data_content = {}
                for j, xpath in enumerate(data_xpaths):
                    try:
                        elements = await page.xpath(xpath)
                        if elements:
                            content = await page.evaluate('(element) => element.textContent', elements[0])
                            data_content[data_names[j]] = content
                    except Exception as e:
                        print(f"Error encountered while processing data: {e}")  # 更详细的错误信息

                # 获取时间数据
                try:
                    time_elements = await page.xpath(time_xpath)
                    if time_elements:
                        time_content = await page.evaluate('(element) => element.textContent', time_elements[0])
                        data_content['时间'] = time_content  # 使用'时间'而不是'time'，与data_names保持一致
                        data_list.append(data_content)  # 添加到列表中
                except Exception as e:
                    print(f"Error encountered while retrieving time: {e}")  # 更详细的错误信息

        except Exception as e:
            print(f"Error encountered while processing chart: {e}")
            return None

        # 如果获得了数据，创建DataFrame
        if data_list:
            df = pd.DataFrame(data_list)

            # 删除重复项，您可以根据需要调整此处。
            # 如果'时间'列是唯一标识符，您可以仅基于它删除重复项
            df_no_duplicates = df.drop_duplicates()
            df_reset = df_no_duplicates.reset_index(drop=True)

            # 反转列的顺序
            reversed_columns = df_reset.columns.tolist()[::-1]
            df_reversed = df_reset[reversed_columns]

            return df_reversed
        else:
            print("没有收集到数据。")
            return None
    # 鼠标滑动
    async def custom_scroll(self,page):
        await self.page.evaluate(f'window.scrollBy(0, {self.custom_scroll_num})')  # 向下滚动100像素

    # 图表读取（css路径）
    async def gr_xp(self,page, num_data_points, canvas_selector, time_selector, data_selectors, data_names, timeout=5000):
        data_list = []
        unique_times = set()  # 用于存储已经遇到的时间，以避免重复
        try:
            # 等待Canvas元素可见
            await page.waitForXPath(canvas_selector, {"visible": True, "timeout": timeout})

            # 获取canvas信息
            canvas_info = await page.evaluate(f"""
                (selector) => {{
                    const element = document.evaluate(selector, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    const {{ x, y, width, height }} = element.getBoundingClientRect();
                    return {{ x, y, width, height }};
                }}
            """, canvas_selector)

            left_x = canvas_info['x']
            right_x = canvas_info['x'] + canvas_info['width']
            interval = (right_x - left_x) / (num_data_points - 1)

            for i in range(num_data_points):
                hover_x = left_x + interval * i
                await page.mouse.move(hover_x, canvas_info['y'] + canvas_info['height'] / 2)

                # 尝试获取时间标签
                try:
                    time_content = await page.evaluate('''(selector) => {
                        const element = document.evaluate(selector, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                        return element.textContent;
                    }''', time_selector)

                    # 检查时间是否重复
                    if time_content in unique_times:
                        continue  # 如果时间重复，则跳过当前循环的剩余部分
                    unique_times.add(time_content)

                except Exception as e:
                    continue  # 如果获取时间时出错，则跳过当前循环的剩余部分

                data_content = {'时间': time_content}  # 首先添加时间

                # 现在，获取数据点
                for j, selector in enumerate(data_selectors):
                    try:
                        content = await page.evaluate('''(selector) => {
                            const element = document.evaluate(selector, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                            return element.textContent;
                        }''', selector)
                        data_content[data_names[j]] = content
                    except Exception as e:
                        # 如果需要，这里可以处理错误
                        pass

                # 添加到数据列表
                data_list.append(data_content)

            # 转换为DataFrame
            dataframe = pd.DataFrame(data_list)

            # 如果需要，可以进一步处理dataframe，例如排序或其他操作
            # ...

            return dataframe

        except Exception as e:
            # 这里可以添加对整体错误的处理
            print(f"An error occurred: {e}")
            return None  # 或者其他适当的错误处理

            return dataframe
        except Exception as e:
            # print(f"Error during data extraction: {e}")
            return None

    async def gr_test(self, page, num_data_points, canvas_selector, data_selectors, data_names, timeout=5000):
        data_list = []
        unique_data_set = set()

        try:
            await page.waitForXPath(canvas_selector, {"visible": True, "timeout": timeout})

            canvas_info = await page.evaluate("""
                (selector) => {
                    const element = document.evaluate(selector, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    const { x, y, width, height } = element.getBoundingClientRect();
                    return { x, y, width, height };
                }
            """, canvas_selector)

            left_x = canvas_info['x']
            right_x = canvas_info['x'] + canvas_info['width']
            interval = (right_x - left_x) / (num_data_points - 1)

            for i in range(num_data_points):
                hover_x = left_x + interval * i
                await page.mouse.move(hover_x, canvas_info['y'] + canvas_info['height'] / 2)

                data_point_content = []
                for selector in data_selectors:
                    try:
                        content = await page.evaluate('''(selector) => {
                            const result = document.evaluate(selector, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                            const node = result.singleNodeValue;
                            return node ? node.textContent.trim() : '';
                        }''', selector)
                        data_point_content.append(content)
                    except Exception as e:
                        print(f"Error while extracting data: {e}")

                print(f"Data point {i}: {data_point_content}")  # Debugging line

                data_point_str = " | ".join(data_point_content)
                if data_point_str not in unique_data_set:
                    unique_data_set.add(data_point_str)
                    data_list.append(data_point_content)

            if len(data_list) < 30:
                print("Warning: Fewer than 30 unique data points collected.")

            today = datetime.now()
            date_list = [(today - timedelta(days=days_back)).strftime('%Y-%m-%d') for days_back in range(1, len(data_list) + 1)][::-1]

            for i, data_point in enumerate(data_list):
                date_data = {'日期': date_list[i]}
                date_data.update(dict(zip(data_names, data_point)))
                data_list[i] = date_data

            dataframe = pd.DataFrame(data_list)

            return dataframe

        except Exception as e:
            print(f"An error occurred: {e}")
            return None


    '''品牌概览'''
    async def sales_trends(self,page):
        self.canvas_selector = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[1]/div[2]/div[2]/div[2]/div/div/div/canvas'
        self.time_selector = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[1]/div[2]/div[2]/div[2]/div/div/div/div/div'
        self.data_selectors = [
            '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[1]/div[2]/div[2]/div[2]/div/div/div/div/ul/li[1]/span[3]',
            '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[1]/div[2]/div[2]/div[2]/div/div/div/div/ul/li[2]/span[3]'
        ]
        self.data_names = ['商品数', '带货销量']
        data = await self.gr_xp(self.page, 200, self.canvas_selector, self.time_selector, self.data_selectors,
                                self.data_names, timeout=5000)
        return data
    async def live_sales_trends(self,page):
        self.canvas_selector = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[2]/div[2]/div[2]/div[2]/div/div/div/canvas'
        self.time_selector = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[2]/div[2]/div[2]/div[2]/div/div/div/div/div'
        self.data_selectors = [
            '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[2]/div[2]/div[2]/div[2]/div/div/div/div/ul/li[1]/span[3]',
            '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[2]/div[2]/div[2]/div[2]/div/div/div/div/ul/li[2]/span[3]'
        ]
        self.data_names = ['直播场次', '直播销量']
        data = await self.gr_xp(self.page, 200, self.canvas_selector, self.time_selector, self.data_selectors,
                                self.data_names, timeout=5000)
        return data
    '''品类商品'''
    async def category_trends(self,page):
        self.canvas_selector = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[2]/div[2]/div/div/div/div[3]/div/div[1]/canvas'
        self.data_selectors = [
            '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[2]/div[2]/div/div/div/div[3]/div/div[2]/div/div[2]/div[1]/span[2]',
            '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[2]/div[2]/div/div/div/div[3]/div/div[2]/div/div[2]/div[2]/span[2]',
            '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[2]/div[2]/div/div/div/div[3]/div/div[2]/div/div[2]/div[3]/span[2]'
        ]
        self.data_names = ['当日总量', '食品饮料', '钟表配饰']
        data = await self.gr_test(self.page, 30, self.canvas_selector, self.data_selectors,
                                self.data_names, timeout=5000)
        return data

    def current_date(self):
        today = datetime.today()
        formatted_date = today.strftime('%Y.%m.%d')
        return formatted_date

    def initialize_driver(self):
        # 初始化 WebDriver
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", self.debugger_address)
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(20)

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

    def find_and_click_element(self, css_selector, sleep, selected_sign=""):  # 定位并选中某元素
        element = self.driver.find_elements_by_css_selector(css_selector)[0]
        if not (selected_sign and selected_sign in element.get_attribute('class').strip()):
            _actions = ActionChains(self.driver)
            _actions.move_to_element(element).click().perform()
            self.driver.implicitly_wait(1)
            time.sleep(sleep)

        return element

    def click_element(self, element, sleep, selected_sign=""):  # 仅选中某元素
        if not (selected_sign and selected_sign in element.get_attribute('class').strip()):
            _actions = ActionChains(self.driver)
            _actions.move_to_element(element).click().perform()
            self.driver.implicitly_wait(1)
            time.sleep(sleep)

    async def get_brand_info(self, selected_plate=(),):  # 默认都是近30天
        await self.init()
        root_dict = dict()
        graph = {}
        _xpath_for_plate = '//*[@id="scrollLayoutContent"]/div/div[2]/div[2]/div[2]/div/div/a'
        _plate_lst = self.driver.find_elements_by_xpath(_xpath_for_plate)

        for _plate in _plate_lst:

            # if _plate in {'overview', 'commodity', 'live'}:  # 调试用
            #     continue

            # 定位并跳转至对应的版块
            _plate_info = _plate.get_attribute('href').split('/')[-2]
            if _plate_info not in selected_plate:
                continue

            if _plate.get_attribute('class') == '_QV-uvgcI':
                _actions = ActionChains(self.driver)
                _actions.move_to_element(_plate).click().perform()
                self.driver.implicitly_wait(1)
                time.sleep(1.5)

            if _plate_info == 'overview':  # 品牌概览

                overview = root_dict.setdefault('品牌概览', dict())
                ## 基本信息
                basic_info = overview.setdefault('基本信息', dict())
                ### 品牌自播账号&相关小店号
                _xpath_for_account_lst = '//*[@id="scrollLayoutContent"]/div/div[1]/div/div/div[1]/div[2]/div[2]/div[1]/div[2]/div/div'
                _account_lst = self.driver.find_elements_by_xpath(_xpath_for_account_lst)
                # print('相关自播账号有：{}个'.format(len(_account_lst)))
                basic_info['自播账号数'] = len(_account_lst)
                _account_title_lst = []
                for _account in _account_lst:
                    _account_title = _account.find_elements_by_xpath('./div/div/span[2]')[0].text.strip()
                    _account_title_lst.append(_account_title)
                # print(_account_title_lst)
                basic_info['自播账号'] = ','.join(_account_title_lst)
                _xpath_for_shop_lst = '//*[@id="scrollLayoutContent"]/div/div[1]/div/div/div[1]/div[2]/div[2]/div[2]/div[2]/div/div'
                _shop_lst = self.driver.find_elements_by_xpath(_xpath_for_shop_lst)
                # print('相关小店账号有：{}个'.format(len(_shop_lst)))
                basic_info['相关小店数'] = len(_shop_lst)
                _shop_title_lst = []
                for _shop in _shop_lst:
                    _shop_title = _shop.find_elements_by_xpath('./div/div/span')[0].text.strip()
                    _shop_title_lst.append(_shop_title)
                # print(_shop_title_lst)
                basic_info['相关小店'] = ','.join(_shop_title_lst)

                ### 近30天数据
                _xpath_for_data_item = '//*[@id="scrollLayoutContent"]/div/div[1]/div/div/div[3]/div[2]/div'
                _data_item_lst = self.driver.find_elements_by_xpath(_xpath_for_data_item)
                for _data_item in _data_item_lst:
                    _key = _data_item.find_elements_by_xpath('./span[1]')[0].text.strip()
                    _val = _data_item.find_elements_by_xpath('./span[2]')[0].text.strip()
                    basic_info[_key] = _val
                # print(basic_info)

                ## 推广商品概览
                merchandise_promotion_general = overview.setdefault('推广商品概览', dict())
                _xpath_for_general = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[1]/div[2]/div[1]/div/div/div[1]'
                _general = self.driver.find_elements_by_xpath(_xpath_for_general)[0].text.strip()
                merchandise_promotion_general['整体描述'] = _general

                for _idx in range(1, 3):
                    _xpath_for_key = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[1]/div[2]/div[1]/div/div/div[2]/div[{}]/div[2]/p[2]'.format(_idx)
                    _xpath_for_val = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[1]/div[2]/div[1]/div/div/div[2]/div[{}]/div[2]/p[1]'.format(_idx)
                    _key = self.driver.find_elements_by_xpath(_xpath_for_key)[0].text.strip()
                    _val = self.driver.find_elements_by_xpath(_xpath_for_val)[0].text.strip()

                    merchandise_promotion_general[_key] = _val

                ### 销量最好的区间
                _xpath_for_best_sell_price_interval = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[1]/div[2]/div[1]/div/div/div[3]/div[2]/div/div[1]'
                _best_sell_price_interval_lst = self.driver.find_elements_by_xpath(_xpath_for_best_sell_price_interval)
                merchandise_promotion_general['销量最好的区间'] = ','.join([x.text.replace('、', '').strip() for x in _best_sell_price_interval_lst])
                ### 销售额最高的类别为
                _xpath_for_best_sell_category = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[1]/div[2]/div[1]/div/div/div[4]/div[2]/div'
                _best_sell_category_lst = self.driver.find_elements_by_xpath(_xpath_for_best_sell_category)
                merchandise_promotion_general['销售额最高的类别'] = ','.join([x.text.strip() for x in _best_sell_category_lst])

                ## 带货直播概览
                live_selling_general = overview.setdefault('带货直播概览',dict())
                _xpath_for_general = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[2]/div[2]/div[1]/div/div/div[1]'
                _general = self.driver.find_elements_by_xpath(_xpath_for_general)[0].text.strip()
                live_selling_general['整体描述'] = _general

                for _idx in range(1, 5):
                    _xpath_for_key = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[2]/div[2]/div[1]/div/div/div[2]/div[{}]/div[2]/p[2]'.format(_idx)
                    _xpath_for_val = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[2]/div[2]/div[1]/div/div/div[2]/div[{}]/div[2]/p[1]'.format(_idx)
                    _key = self.driver.find_elements_by_xpath(_xpath_for_key)[0].text.strip()
                    _val = self.driver.find_elements_by_xpath(_xpath_for_val)[0].text.strip()
                    live_selling_general[_key] = _val

                ## 关联主播概览
                related_anchor_general = overview.setdefault('关联主播概览',dict())
                _xpath_for_general = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[3]/div[2]/div[1]/div/div/div[1]'
                _general = self.driver.find_elements_by_xpath(_xpath_for_general)[0].text.strip()
                related_anchor_general['整体描述'] = _general

                ### 销售额TOP主播类别
                _xpath_for_top_anchor_category = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[3]/div[2]/div[1]/div/div/div[2]/div[2]/div'
                _top_anchor_category_lst = self.driver.find_elements_by_xpath(_xpath_for_top_anchor_category)
                related_anchor_general['销售额TOP主播类别'] = ','.join([x.text.replace('、', '').strip() for x in _top_anchor_category_lst])
                ### 主要粉丝量级
                _xpath_for_main_fans_level = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[3]/div[2]/div[1]/div/div/div[3]/div[2]/div/div[1]'
                _main_fans_level_lst = self.driver.find_elements_by_xpath(_xpath_for_main_fans_level)
                related_anchor_general['主要粉丝量级'] = ','.join([x.text.replace('、', '').strip() for x in _main_fans_level_lst])

                ## 带货小店概览
                promotion_shop_general = overview.setdefault('带货小店概览',dict())
                _xpath_for_general = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[4]/div[2]/div[1]/div/div/div[1]'
                _general = self.driver.find_elements_by_xpath(_xpath_for_general)[0].text.strip()
                promotion_shop_general['整体描述'] = _general

                ###  销售额TOP小店主营行业
                _xpath_for_top_shop_industry = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[4]/div[2]/div[1]/div/div/div[2]/div[2]/div'
                _top_shop_industry_lst = self.driver.find_elements_by_xpath(_xpath_for_top_shop_industry)
                promotion_shop_general['销售额TOP小店主营行业'] = ','.join([x.text.strip() for x in _top_shop_industry_lst])
                ### 平均评分
                _xpath_for_avg_rating = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[4]/div[2]/div[1]/div/div/div[3]/div[2]/div[1]'
                _avg_rating = self.driver.find_elements_by_xpath(_xpath_for_avg_rating)[0].text.strip()
                promotion_shop_general['平均评分'] = _avg_rating
                graph['品牌概览-商品数量/销量趋势'] = await self.sales_trends(self)
                graph['品牌概览-直播场次/销量趋势'] = await self.live_sales_trends(self)



            elif _plate_info == 'commodity':  # 品类商品
                commodity = root_dict.setdefault('品类商品', dict())

                ## 数据表现
                data_behaviour = commodity.setdefault('数据表现', dict())
                _item_lst = self.driver.find_elements_by_class_name('normal-item')
                for _item in _item_lst:
                    _key = _item.find_elements_by_xpath('./p[1]')[0].text.strip()
                    _val = _item.find_elements_by_xpath('./p[2]')[0].text.strip()
                    data_behaviour[_key] = _val
                # print(data_behaviour)

                ## 品类趋势
                category_trend = commodity.setdefault('品类趋势', dict())

                ### 趋势总览
                gross_trend = category_trend.setdefault('趋势总览', dict())
                _xpath = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[2]/div[2]/div/div/div/div[1]'
                _describe = self.driver.find_elements_by_xpath(_xpath)[0].text.strip()
                # print(_describe)
                gross_trend['整体描述'] = _describe

                ### todo-品类分布
                ### 品类销售贡献top5
                top5_category = category_trend.setdefault('品类销售贡献top5', dict())
                _xpath = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[2]/div[3]/div[2]/div[2]'
                _describe = self.driver.find_elements_by_xpath(_xpath)[0].text.replace('· ', '').strip()
                top5_category['整体描述'] = _describe

                _xpath_for_table_col_names = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[2]/div[3]/div[2]/div[3]/div/div/div/div/div/div/div[1]/table/thead/tr/th'
                _col_name_lst = [x.text.strip() for x in self.driver.find_elements_by_xpath(_xpath_for_table_col_names)]

                # print(_col_name_lst)

                _xpath_for_row = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[2]/div[3]/div[2]/div[3]/div/div/div/div/div/div/div[2]/table/tbody/tr'

                _row_lst = self.driver.find_elements_by_xpath(_xpath_for_row)[1:]

                table = [_col_name_lst]
                for _row in _row_lst:

                    row = []
                    _cell_lst = _row.find_elements_by_xpath('./td')
                    for _idx, _cell in enumerate(_cell_lst):

                        row.append(_cell.text.strip())
                    table.append(row)
                # print(table)
                top5_category['详细数据'] = table

                # print(top5_category)

                ## 商品价格分布
                merchandise_price_distribution = commodity.setdefault('商品价格分布', dict())
                _xpath_for_describe = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[3]/div[2]/div/div[1]/div/div[1]'
                _describe = self.driver.find_elements_by_xpath(_xpath_for_describe)[0].text.strip()
                merchandise_price_distribution['整体描述'] = _describe

                ## TOP10品类竞争度
                top10_category_competity = commodity.setdefault('TOP10品类竞争度', dict())
                _xpath_for_describe = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[4]/div[2]/div[2]/div[1]'
                _describe = self.driver.find_elements_by_xpath(_xpath_for_describe)[0].text.strip()
                top10_category_competity['整体描述'] = _describe

                # print(await self.category_trends(self))
                ## todo-带货商品列表

            elif _plate_info == 'live':  # 带货直播

                live = root_dict.setdefault('live', dict())
                ## 数据表现
                data_behaviour = live.setdefault('数据表现', dict())

                _normal_item_lst = self.driver.find_elements_by_class_name('normal-item')
                # print(len(_normal_item_lst))
                for _normal_item in _normal_item_lst:

                    _key = _normal_item.find_elements_by_xpath('./p[1]')[0].text.strip()
                    _val = _normal_item.find_elements_by_xpath('./p[2]')[0].text.strip()

                    data_behaviour[_key] = _val

                ### 品牌&非品牌专场
                for _idx in range(1, 3):

                    _xpath_for_p = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[1]/div[2]/div/div/div[4]/p[{}]'.format(_idx)
                    _key = self.driver.find_elements_by_xpath(_xpath_for_p + '/span[1]')[0].text.strip()
                    _val = self.driver.find_elements_by_xpath(_xpath_for_p + '/span[2]')[0].text.strip()

                    data_behaviour[_key] = _val

                ## todo-直播列表
                # live_list = live.setdefault("直播列表", dict())

            elif _plate_info == 'anchor':  # 关联主播

                anchor = root_dict.setdefault("关联主播", dict())

                ## 数据概览
                data_general = anchor.setdefault("数据概览", dict())
                _xpath_for_item1 = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[1]/div[2]/div/div/div[1]/p'
                _xpath_for_item2 = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[1]/div[2]/div/div/div[2]'
                _xpath_for_item3 = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[1]/div[2]/div/div/div[3]'

                for _key, _xpath in zip(['总体达人带货数据', '品牌自播数据', '品牌他播数据'], [_xpath_for_item1, _xpath_for_item2, _xpath_for_item3]):
                    _val = self.driver.find_elements_by_xpath(_xpath)[0].text.replace('\n', '').strip()
                    data_general[_key] = _val
                    # print('{}: {}'.format(_key, _val))

                ## 主播分类
                anchor_category = anchor.setdefault("主播分类", dict())

                _xpath_for_anchor_category_describe_1 = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[2]/div[2]/div[1]/div[1]/span'
                _anchor_category_describe_1 = self.driver.find_elements_by_xpath(_xpath_for_anchor_category_describe_1)[0].text.strip()
                anchor_category['整体描述-账号类型'] = _anchor_category_describe_1

                _xpath_for_anchor_category_detail_btn = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[2]/div[2]/div[1]/div[2]/div/label[2]/span[1]'
                _anchor_category_detail_btn = self.driver.find_elements_by_xpath(_xpath_for_anchor_category_detail_btn)[0]
                if 'ant-radio-button-checked' not in _anchor_category_detail_btn.get_attribute('class'):
                    _actions = ActionChains(self.driver)
                    _actions.move_to_element(_anchor_category_detail_btn).click().perform()
                    self.driver.implicitly_wait(1)
                    time.sleep(1)

                _xpath_for_col_name = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[2]/div[2]/div[1]/div[3]/div/div/div/div/div/div/div/div/div/div/div[1]/table/thead/tr/th'
                _col_name_lst = [x.text.strip() for x in self.driver.find_elements_by_xpath(_xpath_for_col_name)]

                _xpath_for_row = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[2]/div[2]/div[1]/div[3]/div/div/div/div/div/div/div/div/div/div/div[2]/table/tbody/tr'
                _row_lst = self.driver.find_elements_by_xpath(_xpath_for_row)[1:]
                _table = [_col_name_lst]
                for _row in _row_lst:

                    _cell_lst = [x.text.strip() for x in _row.find_elements_by_xpath('./td/span')]
                    _table.append(_cell_lst)

                anchor_category['主播分类明细'] = _table

                _xpath_for_anchor_category_describe_2 = '//*[@id="scrollLayoutContent"]/div/div[3]/div/div[2]/div[2]/div[2]/div/div/div[1]'
                _anchor_category_describe_2 = self.driver.find_elements_by_xpath(_xpath_for_anchor_category_describe_2)[0].text.strip()
                anchor_category['整体描述-账号画像'] = _anchor_category_describe_2

                # print(anchor_category)
                ## todo-关联主播列表

                ##



                pass

            elif _plate_info == 'store':  # 带货小店

                pass
            # break

        # print(root_dict)
        return root_dict,graph
def clean_sheet_name(sheet_name):
    invalid_chars = r'\/?*[]'  # You can add more characters that you want to remove
    for char in invalid_chars:
        sheet_name = sheet_name.replace(char, '_')
    return sheet_name[:31]
async def main():
    s = WebScraper()

    s.initialize_driver()
    s.check_and_maximize_window()

    data, graph = await s.get_brand_info([
        'overview',
        'commodity',
        'live',
        'anchor',
        'store',
    ])
    final_data = {}

    new_data1 = {}
    data1 = data['品牌概览']
    # print(data1)
    for key in data1:
        sub1 = data1[key]
        # print(sub1)
        for key1 in sub1.keys():
            new_data1[f'{key}-{key1}'] = sub1[key1]
    df1 = pd.DataFrame([new_data1])
    # print(df1)

    final_data['品牌概览'] = df1
    final_data['品牌概览-商品数量/销量趋势'] = graph['品牌概览-商品数量/销量趋势']
    final_data['品牌概览-直播场次/销量趋势'] = graph['品牌概览-直播场次/销量趋势']

    new_data2 = {}
    data2 = data['品类商品']
    df2 = None
    df2_1 = None
    for key in data2:
        sub2 = data2[key]

        if key == '数据表现':
            df2 = pd.DataFrame([data2['数据表现']])
        elif key == '品类趋势':
            df2 = pd.concat([df2, pd.DataFrame([sub2['趋势总览']])], axis=1)
            data2_1 =sub2['品类销售贡献top5']
            new_data2['品类销售贡献top5-整体描述'] = data2_1['整体描述']
            data2_table =data2_1['详细数据']
            df2_1 = pd.DataFrame(data2_table[1:], columns=data2_table[0])
        elif key =='商品价格分布':
            new_data2['商品价格分布-整体描述'] = sub2['整体描述']
        elif key =='TOP10品类竞争度':
            new_data2['TOP10品类竞争度-整体描述'] = sub2['整体描述']
        else:
            print(sub2)
    df2 = pd.concat([df2, pd.DataFrame(new_data2,index=[0])], axis=1)
    # print(df2)
    # print(df2_1)
    final_data['品类商品'] = df2
    final_data['品类商品-品类销售贡献TOP5'] =df2_1

    data3 = data['live']
    df3 = pd.DataFrame(data3['数据表现'],index=[0])
    final_data['live'] = df3

    new_data4 ={}
    data4 = data['关联主播']
    data4_table =None
    for key in data4.keys():
        if key =='数据概览':
            new_data4 = data4[key]
        elif key =='主播分类':
            data4_1 = data4[key]
            new_data4['主播分类-整体描述-账号类型'] = data4_1['整体描述-账号类型']
            data4_table = data4_1['主播分类明细']
            data4_table = pd.DataFrame(data4_table[1:], columns=data4_table[0])
            # print(data4[key])
            new_data4['主播分类-整体描述-账号画像'] = data4_1['整体描述-账号画像']
        else:
            print(data4[key])
    df4 =pd.DataFrame(new_data4,index=[0])
    # print(data4_table)
    # print(df4)
    final_data['主播分类'] =df4
    final_data['主播分类-主播分类明细'] =data4_table

    # 设置您想要创建的目录的名称
    folder_name = '新快-品牌主页'
    # 当前文件的绝对路径
    current_directory = os.getcwd()
    # 拼接完整的文件夹路径
    folder_path = os.path.join(current_directory, folder_name)

    # 检查文件夹是否存在，如果不存在则创建
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # print(final_data)
    # 指定新Excel文件的完整路径
    # 获取当前日期并格式化为年月日
    current_date = datetime.now().strftime('%Y-%m-%d')
    random_number = random.randint(0, 1000)
    excel_path = os.path.join(folder_path, f'output_快手品牌{current_date}-{random_number}.xlsx')

    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        for sheet_name, df in final_data.items():
            df.to_excel(writer, sheet_name = clean_sheet_name(sheet_name))
    print(f'{excel_path}文件已生成')
if __name__ == '__main__':
    asyncio.run(main())





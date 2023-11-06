import asyncio
import time
import pandas as pd
import re
from pyppeteer import connect
class Blogger_detail:
    def __init__(self, page):
        self.page = page

    # 横向图像爬取
    async def gr_xp(self, page, num_data_points, canvas_selector, time_selector, data_selectors, data_names,timeout=50000,y=2):
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
                await page.mouse.move(hover_x, canvas_info['y'] + canvas_info['height'] /y)
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
            df = pd.DataFrame(data_list)
            try:
                df['时间'] = pd.to_datetime(df['时间'])
                # # Sort DataFrame by '时间' column
                df_sorted = df.sort_values(by='时间', ascending=True)
                return df_sorted
            # 如果需要，可以进一步处理dataframe，例如排序或其他操作
            # ...
            except:
                return df

        except Exception as e:
            # 这里可以添加对整体错误的处理
            print(f"An error occurred: {e}")
            return None  # 或者其他适当的错误处理

        except Exception as e:
            # print(f"Error during data extraction: {e}")
            return None
    # 纵向图像爬取
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
    # 获取url
    async def get_data_row_key(self,page, row_element):
        data_row_key = await page.evaluate('(element) => element.getAttribute("data-row-key")', row_element)
        return data_row_key
    # 下拉table
    async def scrape_table_data(self, table_xpath, rows_xpath):
        all_data = []
        data_row_keys = []
        table_header = None
        _pre_lst_len = 0

        # 定位表格
        table = await self.page.xpath(table_xpath)
        if not table:
            print("Table not found!")
            return pd.DataFrame()

        timeout = 3  # 设置3秒的超时时间
        start_time = asyncio.get_event_loop().time()

        while True:
            # 滚动页面
            await self.page.evaluate('(element) => { element.scrollIntoView(false); }', table[0])


            # 等待一段时间，让页面有机会加载新内容
            await asyncio.sleep(0.5)

            # 检查新的数据条数
            rows = await self.page.xpath(rows_xpath)
            new_data_count = len(rows)

            # 如果数据条数没有增加，或者超过3秒没有新数据，则停止滚动
            if new_data_count == _pre_lst_len:
                if asyncio.get_event_loop().time() - start_time > timeout:
                    break
            else:
                start_time = asyncio.get_event_loop().time()  # 重置开始时间

                # 提取当前获取的所有行的数据
                for row_element in rows[_pre_lst_len:]:  # 只处理新加载的行
                    # 获取行内所有单元格的数据
                    cell_data = await self.page.evaluate('''(row) => {
                                        return Array.from(row.querySelectorAll("td")).map(cell => cell.innerText);
                                    }''', row_element)

                    # 获取行的data-row-key属性值
                    data_row_key = await self.get_data_row_key(self.page, row_element)
                    if data_row_key:
                        data_row_keys.append(
                            'http://121.40.92.153:50888/d/account/overview/' + data_row_key)  # 将data-row-key添加到data_row_keys列表中

                    all_data.append(cell_data)  # 添加到数据列表中

                _pre_lst_len = new_data_count  # 更新旧的列表长度

            # 获取表头文本
            if table_header is None:
                table_header = await self.page.evaluate('''() => {
                        const ths = Array.from(document.querySelectorAll('table thead tr th'));
                        return ths.map(th => th.innerText);
                    }''')
                # 使用正则表达式清理表头
                table_header = [re.sub(r'[^a-zA-Z\u4e00-\u9fa5\d]+', '', th) for th in table_header]

        # 创建 DataFrame
        if all_data:
            df = pd.DataFrame(all_data, columns=table_header)  # 使用表头创建DataFrame
            df = df.drop(df.index[0])
            df['url'] = data_row_keys
        else:
            print("未收集到数据")
            df = pd.DataFrame()

        return df
    # 爬取数据
    async def extract_data_from_xpath(self, xpath):
        elements = await self.page.xpath(xpath)
        if not elements:
            return None
        return await self.page.evaluate('(element) => element.textContent', elements[0])

    """personal"""
    async def extract_content_labels(self):
        # 使用XPath来匹配内容标签的span元素
        xpath = '//*[@id="scrollLayoutContent"]/div[1]/div/div[1]/div/div/div[1]/div[1]/div[5]/div/div'

        # 获取匹配的元素列表
        elements = await self.page.xpath(xpath)

        # 初始化一个空的内容标签列表
        content_labels = []

        # 遍历匹配的元素，提取文本信息并添加到列表中
        for element in elements:
            label_text = await self.page.evaluate('(element) => element.textContent', element)
            content_labels.append(label_text)

        return content_labels
    # 个人信息
    async def personal_data(self):
        # 初始化浏览器等操作

        # 假设你有一个包含多个 XPath 的列表
        xpaths = [
            '//*[@id="scrollLayoutContent"]/div[1]/div/div[1]/div/div/div[1]/div[1]/div[2]/div/div/span',
            '//*[@id="scrollLayoutContent"]/div[1]/div/div[1]/div/div/div[1]/div[1]/div[2]/div/div/div/span',
            '//*[@id="scrollLayoutContent"]/div[1]/div/div[1]/div/div/div[1]/div[1]/div[6]/div/div/div/span',
            '//*[@id="scrollLayoutContent"]/div[1]/div/div[1]/div/div/div[2]/div[3]/div/div[3]/div/div[1]/span[2]',
            '//*[@id="scrollLayoutContent"]/div[1]/div/div[1]/div/div/div[2]/div[3]/div/div[2]/div/div[2]/span[2]',
            '//*[@id="scrollLayoutContent"]/div[1]/div/div[1]/div/div/div[2]/div[3]/div/div[2]/div/div[1]/span[2]',
            '//*[@id="scrollLayoutContent"]/div[1]/div/div[1]/div/div/div[2]/div[3]/div/div[4]/div/div[2]/span'

            # 添加更多 XPath
        ]

        # 创建一个空的 DataFrame
        attributes = ['名字', '标签', '认证', '年龄', '地区', '性别', '简介']

        # 创建一个空的 DataFrame
        daren_data = {}
        for i in range(len(attributes)):
            # print(attributes[i],await self.extract_data_from_xpath(xpaths[i]))
            daren_data[attributes[i]] = await self.extract_data_from_xpath(xpaths[i])
            # print(daren_data)
        content_labels = await self.extract_content_labels()
        # 将内容标签列表中的元素转换为字符串并使用逗号分隔
        content_labels_str = ', '.join(map(lambda x: x.replace("内容标签：", ""), content_labels))
        # print(content_labels_str)
        daren_data['内容标签'] = content_labels_str
        df = pd.DataFrame(daren_data, index=[0])
        return df

    """overview"""
    async def extract_overview_data(self):
        data_rows = []

        # 定义_aux_lst
        _aux_lst = ['绝对值', '环比', '同级平均水平']

        # 数据表现部分
        sections = [
            {
                "name": "账号活跃",
                "keys": ['新增作品数' + '-' + x for x in _aux_lst],
                "xpaths": [
                    '//*[@id="performace"]/div[2]/div/div/div[1]/div[1]/div[1]/div[2]/div[2]/span',
                    '//*[@id="performace"]/div[2]/div/div/div[1]/div[1]/div[1]/div[2]/div[2]/div[1]/span[2]',
                    '//*[@id="performace"]/div[2]/div/div/div[1]/div[1]/div[1]/div[2]/div[3]'
                ]
            },
            {
                "name": "粉丝数据",
                "keys": ['粉丝增量' + '-' + x for x in _aux_lst],
                "xpaths": [
                    '//*[@id="performace"]/div[2]/div/div/div[1]/div[1]/div[2]/div[2]/div[2]/div[1]',
                    '//*[@id="performace"]/div[2]/div/div/div[1]/div[1]/div[2]/div[2]/div[2]/div[2]/span[2]',
                    '//*[@id="performace"]/div[2]/div/div/div[1]/div[1]/div[2]/div[2]/div[3]'
                ]
            },
            {
                "name": "作品表现",
                "keys": ['平均互动数' + '-' + x for x in _aux_lst],
                "xpaths": [
                    '//*[@id="performace"]/div[2]/div/div/div[1]/div[2]/div[2]/div[1]/div[2]/div[1]',
                    '//*[@id="performace"]/div[2]/div/div/div[1]/div[2]/div[2]/div[1]/div[2]/div[2]/span[2]',
                    '//*[@id="performace"]/div[2]/div/div/div[1]/div[2]/div[2]/div[1]/div[3]'
                ]
            },
            {
                "name": "作品表现",
                "keys": ['互动中位数' + '-' + x for x in _aux_lst],
                "xpaths": [
                    '//*[@id="performace"]/div[2]/div/div/div[1]/div[2]/div[2]/div[2]/div[2]/div[1]',
                    '//*[@id="performace"]/div[2]/div/div/div[1]/div[2]/div[2]/div[2]/div[2]/div[2]/span[2]',
                    '//*[@id="performace"]/div[2]/div/div/div[1]/div[2]/div[2]/div[2]/div[3]'
                ]
            },
            {
                "name": "作品表现",
                "keys": ['爆文数' + '-' + x for x in _aux_lst],
                "xpaths": [
                    '//*[@id="performace"]/div[2]/div/div/div[1]/div[2]/div[2]/div[3]/div[2]/div[1]',
                    '//*[@id="performace"]/div[2]/div/div/div[1]/div[2]/div[2]/div[3]/div[2]/div[2]/span[2]',
                    '//*[@id="performace"]/div[2]/div/div/div[1]/div[2]/div[2]/div[3]/div[3]'
                ]
            },
            {
                "name": "商业数据",
                "keys": ['直播场次数' + '-' + x for x in _aux_lst],
                "xpaths": [
                    '//*[@id="performace"]/div[2]/div/div/div[2]/div[2]/div[1]/div[1]/div/div[2]/span',
                    '//*[@id="performace"]/div[2]/div/div/div[2]/div[2]/div[1]/div[1]/div/div[2]/div/span[2]',
                    '//*[@id="performace"]/div[2]/div/div/div[2]/div[2]/div[1]/div[1]/div/div[3]'
                ]
            },
            {
                "name": "商业数据",
                "keys": ['平均场观人数' + '-' + x for x in _aux_lst],
                "xpaths": [
                    '//*[@id="performace"]/div[2]/div/div/div[2]/div[2]/div[1]/div[2]/div/div[2]/span',
                    '//*[@id="performace"]/div[2]/div/div/div[2]/div[2]/div[1]/div[2]/div/div[2]/div/span[2]',
                    '//*[@id="performace"]/div[2]/div/div/div[2]/div[2]/div[1]/div[2]/div/div[3]'
                ]
            }
        ]

        for section in sections:
            for _key, _xpath in zip(section["keys"], section["xpaths"]):
                value = await self.extract_data_from_xpath(_xpath)
                data_rows.append((_key, value))

        # 将数据转换为DataFrame
        df = pd.DataFrame(data_rows, columns=['Key', 'Value']).set_index('Key').T

        return df
    # overview_粉丝趋势
    async def overview_fans_trends(self):
        self.canvas_selector = '//*[@id="trend"]/div[2]/div/div[3]/div[2]/div/div/div/canvas'
        self.time_selector = '//*[@id="trend"]/div[2]/div/div[3]/div[2]/div/div/div/div[3]/div/div[1]'
        self.data_selectors = [
            '//*[@id="trend"]/div[2]/div/div[3]/div[2]/div/div/div/div[3]/div/div[3]/div[1]/span/text()[2]',
            '//*[@id="trend"]/div[2]/div/div[3]/div[2]/div/div/div/div[3]/div/div[3]/div[2]/span/text()[2]',
            '//*[@id="trend"]/div[2]/div/div[3]/div[2]/div/div/div/div[3]/div/div[3]/div[3]/div[2]',
            '//*[@id="trend"]/div[2]/div/div[3]/div[2]/div/div/div/div[3]/div/div[3]/div[4]/div[2]'
        ]

        self.data_names = ['直播数', '作品数', '粉丝数量', '粉丝增量']
        data = await self.gr_xp(self.page, 50, self.canvas_selector, self.time_selector, self.data_selectors,
                                self.data_names, timeout=5000)
        return data

    """work_analysis"""
    async def extract_works_analysis(self):
        # 初始化一个空的DataFrame
        df = pd.DataFrame()

        # 定位并选中近90天选项
        xpath_for_recent90days_btn = '//*[@id="scrollLayoutContent"]/div[2]/div[2]/div[2]/div[2]/div[2]/div[1]/div[1]/div[2]/label[4]/span[1]'
        recent90days_status = await self.extract_data_from_xpath(xpath_for_recent90days_btn)
        if 'ant-radio-button-checked' not in recent90days_status:
            recent90days_btn = await self.page.xpath(xpath_for_recent90days_btn)
            await recent90days_btn[0].click()
            await asyncio.sleep(1)

        _key_lst = ['新增作品数', '点赞总数', '分享总数', '评论总数', '收藏总数', '播放总数']

        for _index, _key in enumerate(_key_lst):
            if _index == 0:
                _aux_lst = ['绝对值', '环比', '平均赞享比', '爆文率']
            else:
                _suffix = _key[:2]
                _aux_lst = ['绝对值', '环比', '集均{}数'.format(_suffix), '{}中位数'.format(_suffix)]

            _key_lst_1 = [_key + '-' + _aux for _aux in _aux_lst]

            _xpath_lst = [
                '//*[@id="work-analysis"]/div[2]/div/div/div[{}]/div[1]/div[2]/div[1]'.format(_index + 1),
                '//*[@id="work-analysis"]/div[2]/div/div/div[{}]/div[1]/div[2]/div[2]/span[2]'.format(_index + 1),
                '//*[@id="work-analysis"]/div[2]/div/div/div[{}]/div[3]/div[1]/div[2]'.format(_index + 1),
                '//*[@id="work-analysis"]/div[2]/div/div/div[{}]/div[3]/div[2]/div[2]'.format(_index + 1),
            ]

            for _key_1, _xpath in zip(_key_lst_1, _xpath_lst):
                value = await self.extract_data_from_xpath(_xpath)
                if value:
                    df.at[0, _key_1] = value.strip()

        return df
    # 近15个作品表现
    async def worksAnalysis_top15(self):
        self.time_selector = '//*[@id="work-feature"]/div[2]/div[2]/div/div[2]/div/div/div/div/div/div[1]'
        self.canvas_selector = '//*[@id="work-feature"]/div[2]/div[2]/div/div[2]/div/div/div/canvas'
        self.data_selectors = [
            '//*[@id="work-feature"]/div[2]/div[2]/div/div[2]/div/div/div/div/div/div[3]/div/div/div[1]',
            '//*[@id="work-feature"]/div[2]/div[2]/div/div[2]/div/div/div/div/div/div[3]/div/div/div[2]/div[1]/span',
            '//*[@id="work-feature"]/div[2]/div[2]/div/div[2]/div/div/div/div/div/div[3]/div/div/div[2]/div[2]/span[2]',
            '//*[@id="work-feature"]/div[2]/div[2]/div/div[2]/div/div/div/div/div/div[3]/div/div/div[2]/div[3]/span',
            '//*[@id="work-feature"]/div[2]/div[2]/div/div[2]/div/div/div/div/div/div[3]/div/div/div[2]/div[4]/span',
            '//*[@id="work-feature"]/div[2]/div[2]/div/div[2]/div/div/div/div/div/div[3]/div/div/div[2]/div[5]/span'
        ]
        self.data_names = ['作品名称', '点赞数', '播放数', '分享数', '评论数', '收藏数']
        data = await self.gr_xp(self.page, 100, self.canvas_selector, self.time_selector, self.data_selectors,
                                self.data_names, timeout=5000)
        return data
    # 近15个作品表现2
    async def worksAnalysis_top15_2(self):
        self.time_selector = '//*[@id="work-feature"]/div[2]/div[2]/div/div[2]/div/div/div/div/div/div[1]'
        self.canvas_selector = '//*[@id="work-feature"]/div[2]/div[2]/div/div[2]/div/div/div/canvas'
        self.data_selectors = [
            '//*[@id="work-feature"]/div[2]/div[2]/div/div[2]/div/div/div/div/div/div[3]/div/div[2]/div[1]',
            '//*[@id="work-feature"]/div[2]/div[2]/div/div[2]/div/div/div/div/div/div[3]/div/div[2]/div[2]/div[1]/span',
            '//*[@id="work-feature"]/div[2]/div[2]/div/div[2]/div/div/div/div/div/div[3]/div/div[2]/div[2]/div[2]/span[2]',
            '//*[@id="work-feature"]/div[2]/div[2]/div/div[2]/div/div/div/div/div/div[3]/div/div[2]/div[2]/div[3]/span',
            '//*[@id="work-feature"]/div[2]/div[2]/div/div[2]/div/div/div/div/div/div[3]/div/div[2]/div[2]/div[4]/span',
            '//*[@id="work-feature"]/div[2]/div[2]/div/div[2]/div/div/div/div/div/div[3]/div/div[2]/div[2]/div[5]/span'
        ]
        self.data_names = ['作品名称', '点赞数', '播放数', '分享数', '评论数', '收藏数']
        self.test = 3
        data = await self.gr_xp(self.page, 100, self.canvas_selector, self.time_selector, self.data_selectors,
                                self.data_names, self.test, timeout=5000)
        return data
    # work_analysis_近15个作品表现
    async def extract_works_analysis_top15_data(self):
        graph_data_work = await self.worksAnalysis_top15()
        try:
            graph_data_work_2 = await self.worksAnalysis_top15_2()
            df = pd.concat([graph_data_work, graph_data_work_2], ignore_index=True)
        except:
            df = graph_data_work

        # 删除所有列中的NaN值，除了'时间'列
        df = df.dropna(how='all', subset=[col for col in df.columns if col != '时间'])

        # 转换日期列为datetime对象并排序
        df['时间'] = pd.to_datetime(df['时间'], format='%Y-%m-%d')
        df = df.sort_values(by='时间').reset_index(drop=True)

        return df
    # work_analysis_发布时间
    async def extract_works_analysis_post_time_distrubution(self):
        self.canvas_selector = '//*[@id="work-feature"]/div[2]/div[1]/div[2]/div[2]/div/div[2]/div/canvas'
        self.time_selector = '//*[@id="work-feature"]/div[2]/div[1]/div[2]/div[2]/div/div[2]/div/div/div'
        self.data_selectors = [
            '//*[@id="work-feature"]/div[2]/div[1]/div[2]/div[2]/div/div[2]/div/div/ul/li/span[3]'
        ]

        self.data_names = ['占比']
        data = await self.gr_xp(self.page, 500, self.canvas_selector, self.time_selector, self.data_selectors,
                                self.data_names, timeout=1000,y=3.5)
        return data
    # work_analysis-作品列表
    async def extract_works_analysis_vedio(self):
        # 您需要根据实际情况替换为正确的XPath
        _xpath_for_table = '//*[@id="work-list"]'
        _xpath_for_row = '//*[@id="work-list"]/div[3]/div/div[1]/div/div/div/div/div/div[2]/table/tbody/tr'

        df = await self.scrape_table_data(_xpath_for_table, _xpath_for_row)
        return df

    """fanPortrait"""
    async def extract_fan_portrait(self):
        df = pd.DataFrame()

        _xpath_prefix = '//*[@id="scrollLayoutContent"]/div[2]/div[2]/div[2]/div/div[2]/div[1]'
        _xpath_postfix_lst = [
            '/div[{}]/div[{}]',
            '/div[{}]/div[1]/div[2]/div/div[{}]',
            '/div[{}]/div[2]/div[2]/div/div[{}]',
            '/div[{}]/div[3]/div[2]/div/div[{}]',
        ]
        _key_lst = ['总粉丝数', '粉丝特征', '粉丝设备', '粉丝分布']

        for _index, (_xpath_postfix, _key) in enumerate(zip(_xpath_postfix_lst, _key_lst)):
            if _index == 0:
                _num_1 = 1
                _num_2_lst = [x for x in range(2, 4)]
                _aux_lst = ['绝对值', '描述']

            else:
                _num_1 = 2
                if _index == 3:
                    _num_2_lst = [x for x in range(1, 4)]
                    _aux_lst = ['占比最高城市', '占比最高城市等级', '渗透率最高城市']

                else:
                    _num_2_lst = [x for x in range(1, 3)]
                    if _index == 1:
                        _aux_lst = ['占比最高性别', '占比最高年龄段']
                    else:
                        _aux_lst = ['占比最高设备', '占比最高设备价位']

            for _num_2, _aux in zip(_num_2_lst, _aux_lst):
                _xpath = _xpath_prefix + _xpath_postfix.format(_num_1, _num_2)
                _key_name = _key + '-' + _aux

                element = await self.page.xpath(_xpath)
                if element:
                    text = await self.page.evaluate('(element) => element.textContent', element[0])
                    df.at[0, _key_name] = text.strip()

        return df
    # 地域粉丝分布
    async def extract_fan_portrait_get_fans_region_data(self):
        data_dict = {}

        for _index, _key in enumerate(['省份渗透', '省份占比']):
            provinces = []
            ratios = []

            _xpath_for_region_rank_btn = f'//*[@id="scrollLayoutContent"]/div[2]/div[2]/div[2]/div/div[2]/div[3]/div[3]/div[2]/div/div[2]/div/div[1]/button[{_index + 1}]'
            _region_rank_btn = await self.page.xpath(_xpath_for_region_rank_btn)

            if _region_rank_btn:
                btn_class = await self.page.evaluate('(element) => element.getAttribute("class")', _region_rank_btn[0])
                if btn_class == 'ant-btn ant-btn-default _9MnJtqZ6':
                    await _region_rank_btn[0].click()
                    await asyncio.sleep(1)

            _xpath_for_rank_row = '//*[@id="scrollLayoutContent"]/div[2]/div[2]/div[2]/div/div[2]/div[3]/div[3]/div[2]/div/div[2]/div/div[2]/div[2]/div'
            _rank_row_lst = await self.page.xpath(_xpath_for_rank_row)

            for _rank_row in _rank_row_lst:
                province_elements = await _rank_row.xpath('./div[2]')
                province = await self.page.evaluate('(element) => element.textContent', province_elements[0])
                province = province.strip()

                ratio_elements = await _rank_row.xpath('./div[4]')
                ratio = await self.page.evaluate('(element) => element.textContent', ratio_elements[0])
                ratio = ratio.strip()
                provinces.append(province.strip())
                ratios.append(ratio.strip())

            df = pd.DataFrame({
                '省份': provinces,
                '占比': ratios
            })

            data_dict[_key] = df

        return data_dict
    # 粉丝年龄分布
    async def fans_age_distution(self):
        self.canvas_selector = '//*[@id="scrollLayoutContent"]/div[2]/div[2]/div[2]/div/div[2]/div[3]/div[2]/div[2]/div/div/div/canvas'
        self.time_selector = '//*[@id="scrollLayoutContent"]/div[2]/div[2]/div[2]/div/div[2]/div[3]/div[2]/div[2]/div/div/div/div/ul/li/span[2]'
        self.data_selector = [
            '//*[@id="scrollLayoutContent"]/div[2]/div[2]/div[2]/div/div[2]/div[3]/div[2]/div[2]/div/div/div/div/ul/li/span[3]']
        self.data_names = ['占比']
        self.test = 20
        data = await self.fans_up_to_down(self.page,100, self.canvas_selector, self.time_selector,
                                          self.data_selector, self.data_names, self.test, timeout=3000)
        return data
    # 粉丝手机品牌
    async def fans_phone_brand(self):
        self.canvas_selector = '//*[@id="scrollLayoutContent"]/div[2]/div[2]/div[2]/div/div[2]/div[3]/div[5]/div[2]/div/div/div/canvas'
        self.time_selector = '//*[@id="scrollLayoutContent"]/div[2]/div[2]/div[2]/div/div[2]/div[3]/div[5]/div[2]/div/div/div/div/ul/li/span[2]'
        self.data_selectors = [
            '//*[@id="scrollLayoutContent"]/div[2]/div[2]/div[2]/div/div[2]/div[3]/div[5]/div[2]/div/div/div/div/ul/li/span[3]']
        self.data_names = ['占比']
        data = await self.gr_xp(self.page, 50, self.canvas_selector, self.time_selector, self.data_selectors,
                                self.data_names)
        return data
    """live"""
    async def get_live_overview(self):
        data_dict = {}

        for _row_index in [1, 3]:
            _xpath_for_row_prefix = f'//*[@id="data-overview"]/div[2]/div/div/div[{_row_index}]'

            for _col_index in range(1, 7):
                _xpath_for_key_postfix = f'/div[{_col_index}]/div[1]'
                _xpath_for_absolute_val_postfix = f'/div[{_col_index}]/div[2]'
                _xpath_for_relative_ratio_postfix = f'/div[{_col_index}]/div[3]/span'

                _xpath_for_key = _xpath_for_row_prefix + _xpath_for_key_postfix
                _xpath_for_absolute_val = _xpath_for_row_prefix + _xpath_for_absolute_val_postfix
                _xpath_for_relative_ratio = _xpath_for_row_prefix + _xpath_for_relative_ratio_postfix

                _key = await self.extract_data_from_xpath(_xpath_for_key)
                _absolute_val = await self.extract_data_from_xpath(_xpath_for_absolute_val)
                _relative_ratio = await self.extract_data_from_xpath(_xpath_for_relative_ratio)

                for _aux, _val in zip(['绝对值', '环比'], [_absolute_val, _relative_ratio]):
                    _key_name = _key + '-' + _aux
                    data_dict[_key_name] = _val

        df = pd.DataFrame([data_dict])
        return df
    # 日期分布
    async def live_date_distubuction(self):
        self.canvas_selector = '//*[@id="live-feature"]/div[2]/div/div/div[1]/div[2]/div[2]/div/canvas'
        self.time_selector = '//*[@id="live-feature"]/div[2]/div/div/div[1]/div[2]/div[2]/div/div/ul/li/span[2]'
        self.data_selector = [
            '//*[@id="live-feature"]/div[2]/div/div/div[1]/div[2]/div[2]/div/div/ul/li/span[3]']
        self.data_names = ['占比']
        self.test = 4
        data = await self.fans_up_to_down(self.page, 100, self.canvas_selector, self.time_selector, self.data_selector,
                                          self.data_names, self.test,timeout=3000)
        return data
    # 数据趋势
    async def live_performance(self):
        self.canvas_selector = '//*[@id="data-trend"]/div[2]/div[2]/div/canvas'
        self.time_selector = '//*[@id="data-trend"]/div[2]/div[2]/div/div/div'
        self.data_selectors = [
            '//*[@id="data-trend"]/div[2]/div[2]/div/div/ul/li[1]/span[3]','//*[@id="data-trend"]/div[2]/div[2]/div/div/ul/li[2]/span[3]','//*[@id="data-trend"]/div[2]/div[2]/div/div/ul/li[3]/span[3]'
        ]
        self.data_names = ['累计观看人数','直播销售额','直播销量']
        data = await self.gr_xp(self.page, 100, self.canvas_selector, self.time_selector, self.data_selectors,
                                self.data_names,timeout=3000)
        return data
    """categoryPromotion"""
    # 01 数据概览
    async def get_category_overview(self):
        data_overview = {}

        # 定位并选中&#8203;``【oaicite:0】``&#8203;
        _xpath_for_rencent90days_btn = '//*[@id="scrollLayoutContent"]/div[2]/div[2]/div[2]/div/div[1]/div[1]/div[2]/label[5]/span[1]'
        recent90days_btn_class = await self.extract_data_from_xpath(_xpath_for_rencent90days_btn + "/@class")
        if 'ant-radio-button-checked' not in recent90days_btn_class:
            recent90days_btn = await self.page.xpath(_xpath_for_rencent90days_btn)
            await recent90days_btn[0].click()
            await asyncio.sleep(1)

        # 数据概览
        for _level_1_index in range(1, 4):
            for _level_2_index in range(1, 3):
                _xpath_prefix = f'//*[@id="scrollLayoutContent"]/div[2]/div[2]/div[2]/div/div[2]/div[1]' \
                                f'/div[2]/div[{_level_1_index}]/div[{_level_2_index}]'

                _key = await self.extract_data_from_xpath(_xpath_prefix + '/div[1]')
                _absolute_val = await self.extract_data_from_xpath(_xpath_prefix + '/div[2]')
                _relative_ratio = await self.extract_data_from_xpath(_xpath_prefix + '/div[3]/span')

                for _aux, _val in zip(['绝对值', '环比'], [_absolute_val, _relative_ratio]):
                    _key_name = _key + '-' + _aux
                    data_overview[_key_name] = _val

        return pd.DataFrame([data_overview])
    # 02 品类分布
    async def categoryPromotion_distrubuction(self):
        self.canvas_selector = '//*[@id="scrollLayoutContent"]/div[2]/div[2]/div[2]/div/div[2]/div[2]/div[2]/div[2]/div/div[2]/div/canvas'
        self.time_selector = '//*[@id="scrollLayoutContent"]/div[2]/div[2]/div[2]/div/div[2]/div[2]/div[2]/div[2]/div/div[2]/div/div/div/div[1]'
        self.data_selectors = [
            '//*[@id="scrollLayoutContent"]/div[2]/div[2]/div[2]/div/div[2]/div[2]/div[2]/div[2]/div/div[2]/div/div/div/div[2]/div[2]',
            '//*[@id="scrollLayoutContent"]/div[2]/div[2]/div[2]/div/div[2]/div[2]/div[2]/div[2]/div/div[2]/div/div/div/div[3]/div[2]',
            '//*[@id="scrollLayoutContent"]/div[2]/div[2]/div[2]/div/div[2]/div[2]/div[2]/div[2]/div/div[2]/div/div/div/div[4]/div[2]',
            '//*[@id="scrollLayoutContent"]/div[2]/div[2]/div[2]/div/div[2]/div[2]/div[2]/div[2]/div/div[2]/div/div/div/div[5]/div[2]',
            '//*[@id="scrollLayoutContent"]/div[2]/div[2]/div[2]/div/div[2]/div[2]/div[2]/div[2]/div/div[2]/div/div/div/div[6]/div[2]'
        ]
        self.data_names = ['商品数', '关联品牌', '直播场数','品类销量','品类销售额']
        data = await self.gr_xp(self.page, 50, self.canvas_selector, self.time_selector, self.data_selectors,
                                self.data_names)
        return data
    # 03品类推广明细
    async def get_category_promotion_detail(self):
        category_promotion_detail = {}

        _xpath_for_frst_level_category = '//*[@id="scrollLayoutContent"]/div[2]/div[2]/div[2]/div/div[2]/div[3]/div[2]/div[1]/div[2]/div/span'
        _xpath_for_scnd_level_category = '//*[@id="scrollLayoutContent"]/div[2]/div[2]/div[2]/div/div[2]/div[3]/div[2]/div[2]/div[2]/div/span'

        frst_level_category_elements = await self.page.xpath(_xpath_for_frst_level_category)
        for frst_index, _ in enumerate(frst_level_category_elements):
            # 重新构建每个一级品类的Xpath
            current_frst_xpath = f'({_xpath_for_frst_level_category})[{frst_index + 1}]'

            frst_level_category_class = await self.extract_data_from_xpath(current_frst_xpath + "/@class")
            if '_bYgvLata' not in frst_level_category_class:
                # 使用新的Xpath来定位并点击
                element_to_click = await self.page.xpath(current_frst_xpath)
                if element_to_click:
                    await element_to_click[0].click()  # 点击一级品类
                    time.sleep(2)

            frst_level_category_name = await self.extract_data_from_xpath(current_frst_xpath)

            scnd_level_category_elements = await self.page.xpath(_xpath_for_scnd_level_category)
            for scnd_index, _ in enumerate(scnd_level_category_elements):
                # 重新构建每个二级品类的Xpath
                current_scnd_xpath = f'({_xpath_for_scnd_level_category})[{scnd_index + 1}]'

                scnd_level_category_class = await self.extract_data_from_xpath(current_scnd_xpath + "/@class")
                if '_bYgvLata' not in scnd_level_category_class:
                    # 使用新的Xpath来定位并点击
                    element_to_click = await self.page.xpath(current_scnd_xpath)
                    if element_to_click:
                        await element_to_click[0].click()  # 点击二级品类
                        time.sleep(2)

                scnd_level_category_name = await self.extract_data_from_xpath(current_scnd_xpath)

                _category_detail_str = frst_level_category_name + '-' + scnd_level_category_name
                _category_detail_tmp_dict = {}

                # 获取XX一级品类/XX二级品类下的数据
                for _col_index in range(1, 5):
                    _xpath_for_key = f'//*[@id="scrollLayoutContent"]/div[2]/div[2]/div[2]/div/div[2]/div[3]/div[2]/div[3]/div[1]/div[1]/div[{_col_index}]/span[1]'
                    _xpath_for_val = f'//*[@id="scrollLayoutContent"]/div[2]/div[2]/div[2]/div/div[2]/div[3]/div[2]/div[3]/div[1]/div[1]/div[{_col_index}]/span[2]'

                    _key = await self.extract_data_from_xpath(_xpath_for_key)
                    _val = await self.extract_data_from_xpath(_xpath_for_val)

                    _category_detail_tmp_dict[_key] = _val
                    # print(f'{_category_detail_str}的{_key}: {_val}')

                category_promotion_detail[_category_detail_str] = _category_detail_tmp_dict

        # 将详细数据扁平化为一个新的字典列表
        flattened_details = [
            {**{'品类': category}, **attributes}
            for category, attributes in category_promotion_detail.items()
        ]

        return pd.DataFrame(flattened_details)

    """整合"""
    async def get_account_info(self, selected_plate):
        final_data = {}

        for _plate in selected_plate:
            postfix = self.page.url.split('/')[-1]
            # print(postfix)
            xpath_for_plate_btn = f'//*[@id="rc-tabs-0-tab-/d/account/{_plate}/{postfix}"]'
            # print(xpath_for_plate_btn)
            await self.page.waitForXPath(xpath_for_plate_btn, timesout = 10000)
            _plate_btn_elements = await self.page.xpath(xpath_for_plate_btn)
            # print(_plate_btn_elements)
            _plate_btn = _plate_btn_elements[0]
            aria_selected = await self.page.evaluate('(btn) => btn.getAttribute("aria-selected")', _plate_btn)

            if aria_selected == 'false':
                await _plate_btn.click()
                await asyncio.sleep(1)

            final_data['个人信息'] = await self.personal_data()
            if _plate == 'overview':
                final_data['账号概览'] = await self.extract_overview_data()
                final_data['账号概览-趋势表现'] = await self.overview_fans_trends()
            elif _plate == 'worksAnalysis':
                final_data['作品分析'] = await self.extract_works_analysis()
                final_data['作品分析-近15个作品表现'] = await self.extract_works_analysis_top15_data()
                final_data['作品分析-作品列表'] = await self.extract_works_analysis_vedio()
            elif _plate =='fanPortrait':
                final_data['个人信息'] = await self.personal_data()
                final_data['粉丝画像'] = await self.extract_fan_portrait()
                a = await self.extract_fan_portrait_get_fans_region_data()
                final_data['粉丝地域分布-省份渗透'] = a['省份渗透']
                final_data['粉丝地域分布-省份占比'] = a['省份占比']
                final_data['粉丝画像-粉丝年龄分布'] = await self.fans_age_distution()
                final_data['粉丝画像-粉丝手机品牌占比'] = await self.fans_phone_brand()
            elif _plate =='liveAnalysis':
                final_data['直播分析'] = await self.get_live_overview()
                final_data['直播分析-直播日期分布'] = await self.live_date_distubuction()
                # final_data['直播分析-直播趋势'] = await self.live_performance()
            elif _plate =='categoryPromotion':
                final_data['品类商品'] = await self.get_category_overview()
                final_data['品类商品-品类分布'] = await self.categoryPromotion_distrubuction()
                final_data['品类商品-品类推广明细'] = await self.get_category_promotion_detail()
        return final_data

# async def main():
#     browser = await connect(browserURL='http://127.0.0.1:9222', defaultViewport=None)
#     pages = await browser.pages()
#     page = pages[0]
#     data = Blogger_detail(page)
#     final_data = await data.get_account_info(selected_plate=['overview'])
#     print(final_data)
#
# asyncio.run(main())
import asyncio
import time
import pandas as pd
import os
from pyppeteer import connect,errors
from datetime import datetime
import random

# 鼠标点击--关键字
async def mouse_text(page,text):
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
# 鼠标滑动
async def custom_scroll(num):
    browser = await connect(browserURL='http://127.0.0.1:9222', defaultViewport={'width': 1280, 'height': 720})
    pages = await browser.pages()
    page = pages[0]
    await page.evaluate(f'window.scrollBy(0, {num})')  # 向下滚动100像素
# 图表读取

async def gr_xp(page, num_data_points, canvas_selector, time_selector, data_selectors, data_names, timeout=50000):
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

            data_content = {'Time': time_content}  # 首先添加时间

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

async def mouse(page,xpath):
    try:
        target_elements = await page.xpath(xpath)

        if target_elements:
            await target_elements[0].click()
            await asyncio.sleep(1)  # 异步等待，非阻塞
        else:
            print(f'没有找到xpath为"{xpath}"的元素')
    except Exception as e:
        print(f"处理xpath为'{xpath}'的元素时出错: {e}")

async def check_button_enabled(page, xpath_expression):
    try:
        is_enabled = await page.evaluate('''
            (xpath) => {
                const element = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                return !element || !element.disabled;
            }
        ''', xpath_expression)

        return is_enabled
    except Exception as e:
        print(f"检查元素是否可用时出错: {e}")
        return False  # 如果出现错误，假设按钮不可用

# table数据
async def click_next_page(page, next_button_xpath):
    # 先检查按钮是否可用
    if not await check_button_enabled(page, next_button_xpath):
        print("下一页按钮不可用或已是最后一页.")
        return False

    try:
        next_button = await page.waitForXPath(next_button_xpath, timeout=3000)  # 等待元素出现
        if next_button:
            await next_button.click()  # 如果按钮可用，则点击按钮
            print("已点击下一页.")
            await asyncio.sleep(2)  # 异步等待，确保页面有足够的时间加载新内容
            return True  # 表示成功点击并可能已加载新内容
        else:
            print("下一页按钮未找到.")
    except Exception as e:
        print(f"点击下一页时出错: {e}")
    return False

async def get_table_data(page, header_xpath, rows_xpath):
    # 这个列表将存储表格的数据
    all_data = []

    try:
        # 等待表格元素加载完成（确保行和表头都已加载）
        await page.waitForXPath(header_xpath)
        await page.waitForXPath(rows_xpath)

        # 获取表头数据
        headers_elements = await page.xpath(header_xpath)
        headers = []
        for header_element in headers_elements:
            header_text = await page.evaluate('(element) => element.textContent', header_element)
            headers.append(header_text.strip())  # 清理空格

        # 获取所有行的数据
        rows_elements = await page.xpath(rows_xpath)

        # 遍历每一行，获取数据
        for row_element in rows_elements:
            # 获取行内所有单元格的数据
            row_data = await page.evaluate('''
                (row) => {
                    const cells = Array.from(row.querySelectorAll('td'));
                    return cells.map(cell => cell.textContent.trim());
                }
            ''', row_element)

            all_data.append(row_data)  # 添加到列表中

        # 创建 DataFrame
        df = pd.DataFrame(all_data, columns=headers)
        return df

    except Exception as e:
        print(f"获取表格数据时出现错误: {e}")
        return None  # 在这里返回 None 或其他适当的响应


async def table(page, url, nums):
    url_fans = url + '/fans'
    result = {}

    try:
        await page.goto(url_fans, wait_until='domcontentloaded')  # 等待页面加载完成
        time.sleep(3)
        # 检查页面上是否存在指示“暂无数据”的元素
        no_data_xpath = '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[4]/div[4]/div[3]/div/div[2]/div/p'
        empty_boxes = await page.Jx(no_data_xpath)

        if empty_boxes:
            # 如果找到该元素，则跳过此网站
            print(f"Skipping {url} because it has no data.")
            return None  # 没有数据，直接返回None

        # 页面有数据，继续处理
        button_names = ['商品评价', '视频评论']
        for name in button_names:
            await custom_scroll(700)  # 假设这是滚动的函数
            await mouse_text(page, name)  # 假设这是定位文本并点击的函数

            # 这些是您之前代码中的XPath
            mouse_xpath = '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[4]/div[4]/div[3]/div[2]/div/div/button[2]'
            header_xpath = '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[4]/div[4]/div[3]/div[1]/table/thead/tr/th'
            rows_xpath = '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[4]/div[4]/div[3]/div[1]/table/tbody/tr'

            # 循环，直到没有更多的页面或达到指定的nums
            for _ in range(nums):
                # 尝试获取数据
                df = await get_table_data(page, header_xpath, rows_xpath)  # 假设这是您用来抓取数据的函数
                if df is not None and not df.empty:
                    if name in result:
                        result[name] = pd.concat([result[name], df])  # 合并数据
                    else:
                        result[name] = df

                    # 尝试点击下一页
                    if not await click_next_page(page, mouse_xpath):  # 假设这是翻页函数
                        break  # 如果无法点击，可能是最后一页了，所以跳出循环
                    else:
                        await click_next_page(page, mouse_xpath)
                        await custom_scroll(300)
                else:
                    print(f"没有在'{name}'中找到数据或已到最后一页.")
                    break  # 没有数据，跳出循环

        return result  # 返回最终收集到的数据

    except errors.TimeoutError:
        print(f"访问 {url} 时超时了。")
        return None  # 访问超时，返回None
    except Exception as e:
        print(f"处理 {url} 时出现错误: {e}")
        return None  # 出现其它错误，返回None

# url ='https://www.chanmama.com/promotionDetail/s_gA2LegZVOcclGgVZmrbl4v3M24qyuS'
# print(asyncio.run(table(url,10)))
# 图数据

async def blogger_graph(page,url,po_nums):
    url_blogger = url + '/author'
    await page.goto(url_blogger)
    time.sleep(3)
    await custom_scroll(800)
    canvas_selector ='//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div[1]/div[5]/div/div[2]/div/div/div[1]/div[1]/canvas'
    await page.waitForXPath(canvas_selector)
    time_selector ='//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div[1]/div[5]/div/div[2]/div/div/div[1]/div[2]/div[1]/div/div[1]'
    data_selectors =['//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div[1]/div[5]/div/div[2]/div/div/div[1]/div[2]/div[1]/div/div[2]/div/span[3]',
                     '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div[1]/div[5]/div/div[2]/div/div/div[1]/div[2]/div[2]/div/div/div/span[3]',
                     '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div[1]/div[5]/div/div[2]/div/div/div[1]/div[2]/div[3]/div/div/div/span[3]']
    data_names =['关联达人数','直播大人数','视频达人数']
    data = await gr_xp(page,po_nums,canvas_selector,time_selector,data_selectors,data_names)
    return data

def create_excel_file(task_name, directory_name):
    current_directory = os.getcwd()
    # 拼接文件夹路径
    directory_path = os.path.join(current_directory, directory_name)

    # 检查文件夹是否已存在
    if not os.path.exists(directory_path):
        # 如果不存在，创建文件夹
        os.makedirs(directory_path)
        print(f"文件夹 '{directory_name}' 创建成功")
    else:
        print(f"文件夹 '{directory_name}' 已存在")

    # 获取当前日期并格式化为年月日
    current_date = datetime.now().strftime('%Y-%m-%d')

    # 生成一个随机数（范围可以根据需求调整）
    random_number = random.randint(1, 1000)

    # 构建Excel文件名
    excel_file = os.path.join(directory_path, f'{current_date}_{task_name}_{random_number}.xlsx')

    if not os.path.isfile(excel_file):
        # 如果文件不存在，创建一个新的Excel文件
        with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
            writer.save()

    return excel_file

def create_combined_dataframe(data):
    # 创建一个空的DataFrame来存储所有数据
    all_data = pd.DataFrame()

    # 将所有日期的数据合并到一个DataFrame中
    for date, data_dict in data.items():
        df = pd.DataFrame(data_dict, index=[date])
        all_data = pd.concat([all_data, df])

    return all_data

def write_combined_data_to_excel(output_file, data):
    # 获取合并后的数据框架
    all_data = create_combined_dataframe(data)

    # 将合并后的数据写入Excel文件的一个sheet中
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        all_data.to_excel(writer, sheet_name='AllData', index=True)

def write_data(output_file, data):
    """
    将多个日期数据合并到一个Excel文件的单独sheet中。

    参数：
    output_file (str) - 输出Excel文件名
    data (dict) - 包含日期数据的字典，每个键是日期，每个值是包含数据的字典

    返回：
    无返回值，直接将数据写入Excel文件
    """
    # 创建一个空的DataFrame来存储所有数据
    all_data = pd.DataFrame()

    # 将所有日期的数据合并到一个DataFrame中
    for date, data_dict in data.items():
        df = pd.DataFrame(data_dict, index=[date])
        all_data = pd.concat([all_data, df])

    # 将合并后的数据写入Excel文件的一个sheet中
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        all_data.to_excel(writer, sheet_name=str(random.randint(0,1000)), index=True)

    # 保存Excel文件
    writer.save()

def write_dataframes_to_excel(existing_excel_file, data):
    """
    将多个DataFrame写入已有的Excel文件，并为每个DataFrame生成新的sheet。

    参数：
    existing_excel_file (str) - 已有的Excel文件的路径
    data (dict) - 包含DataFrame的字典，键为sheet名称，值为DataFrame

    返回：
    无返回值，直接将数据写入Excel文件
    """
    sheet_name = random.randint(0,1000)
    with pd.ExcelWriter(existing_excel_file, engine='openpyxl', mode='a') as writer:
        for df in data.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

async def main():
    browser = await connect(browserURL='http://127.0.0.1:9222', defaultViewport={'width': 1280, 'height': 720})
    pages = await browser.pages()
    page = pages[0]

    urls = [
        'https://www.chanmama.com/promotionDetail/s_gA2LegZVOcclGgVZmrbl4v3M24qyuS',
        # 'https://www.chanmama.com/promotionDetail/DkI48oquSupm9E4mRj_KPD7e6kIDF2dC',
        # 'https://www.chanmama.com/promotionDetail/rlrDLnj0QS5O8JPihH0cSJIE1LJbgyag',
        # 'https://www.chanmama.com/promotionDetail/bEYuPLdkbbCYO3aX2yu3p6eci0kTKmSS',
        # 'https://www.chanmama.com/promotionDetail/dhvQN_Rctgop_uxvF-zwmaztq1cstTTd'
        # ... [其他URLs] ...
    ]
    folder_name = 'output_婵妈妈商品页'
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    for url in urls:
        data = await table(page, url, 10)  # 收集表格数据
        graph = await blogger_graph(page, url, 20)  # 收集图形数据

        # 创建一个具有特定格式名称的Excel文件名
        random_number = random.randint(0, 1000)
        current_date = datetime.now().strftime('%Y%m%d')  # 今天的日期，格式为'YYYYMMDD'
        url_token = url.split('/')[-1]  # 或者使用任何方法来提取URL的特定部分
        filename = f"{current_date}_{url_token}_{random_number}.xlsx"
        file_path = os.path.join(folder_name, filename)  # 这确保文件在正确的文件夹中

        # 创建一个Excel写入器
        writer = pd.ExcelWriter(file_path, engine='openpyxl')
        print(data)
        # 如果data不为空，并且是字典类型
        if data and isinstance(data, dict):
            for sheet_name, df in data.items():
                if isinstance(df, pd.DataFrame):
                    # 将数据框写入以其键命名的单独工作表中
                    df.to_excel(writer, sheet_name=sheet_name)
        print(graph)
        # 对于图表数据，我们需要检查DataFrame是否不为空
        if graph is not None and not graph.empty:  # 更改这里
            graph_df = pd.DataFrame(graph)
            graph_df.to_excel(writer, sheet_name='Graph')  # 写入一个名为'Graph'的新工作表

        # 保存Excel文件
        writer.save()

        print(f"Data has been written to {file_path}")


asyncio.run(main())
    # 调用表格方法
    # df = pd.read_excel(excel_file)
    # urls = df['url']
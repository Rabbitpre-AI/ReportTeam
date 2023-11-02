import asyncio
import sys
import time

from pyppeteer import connect
import pandas as pd
import os
import datetime
import random

async def wait_loading(page, _xpath_for_row):
    has_finished_loading = False
    loop_counter = 0  # 添加计数器
    max_retries = 50  # 设置最大重试次数
    timeout = 2  # 设置超时时间为2秒

    try:
        await asyncio.wait_for(_wait_loading_inner(page, _xpath_for_row, has_finished_loading, loop_counter, max_retries), timeout)
    except asyncio.TimeoutError:
        print("尝试加载数据超时。")

async def _wait_loading_inner(page, _xpath_for_row, has_finished_loading, loop_counter, max_retries):
    while True:
        # 检查加载动画
        loading_element = await page.xpath('//div[contains(@class, "ant-spin-spinning")]')
        if loading_element:
            print("正在加载数据...")  # 打印提示信息
            has_finished_loading = True
            await asyncio.sleep(0.01)  # 避免CPU过载
            loop_counter += 1  # 增加计数器的值
            if loop_counter >= max_retries:  # 检查是否超过最大重试次数
                print("尝试加载数据超时。")
                break
            continue
        elif has_finished_loading:
            # 检查数据行数
            row_elements = await page.xpath(_xpath_for_row)
            current_count = len(row_elements)
            print(f"当前已加载 {current_count} 条数据。")  # 打印当前加载的数据行数
            time.sleep(1.5)
            if current_count >= 501:
                print("数据超过501条，暂停执行。")
                return
            break
        else:
            await asyncio.sleep(0.01)  # 避免CPU过载

async def get_data_row_key(page, row_element):
    data_row_key = await page.evaluate('(element) => element.getAttribute("data-row-key")', row_element)
    return data_row_key

async def pull_down_until_end(page, _xpath_for_table, _xpath_for_row):
    _pre_lst_len = 0
    all_data = []  # 用于存储所有行的数据
    data_row_keys = []  # 新建一个列表来存储所有的data-row-key
    table_header = None  # 存储表头文本

    while True:
        # 获取表格元素
        elements = await page.xpath(_xpath_for_table)
        _table = elements[0] if elements else None

        if not _table:
            print("未找到表格")
            break  # 如果没有找到表格，退出循环

        # 滚动到表格的底部
        scroll_distance = sys.maxsize  # 或者您可以使用一个特定的滚动值
        await page.evaluate('''(table, distance) => {
            table.scrollTop += distance;
        }''', _table, scroll_distance)

        await wait_loading(page, _xpath_for_row)

        # 检查数据行数
        row_elements = await page.xpath(_xpath_for_row)
        _cur_lst_len = len(row_elements)

        # 提取当前获取的所有行的数据
        for row_element in row_elements[_pre_lst_len:]:  # 只处理新加载的行
            # 获取行内所有单元格的数据
            cell_data = await page.evaluate('''(row) => {
                    return Array.from(row.querySelectorAll("td")).map(cell => cell.innerText);
                }''', row_element)

            # 获取行的data-row-key属性值
            data_row_key = await get_data_row_key(page, row_element)
            if data_row_key:
                data_row_keys.append('http://121.40.92.153:50888/d/account/overview/'+data_row_key)  # 将data-row-key添加到data_row_keys列表中

            all_data.append(cell_data)  # 添加到数据列表中

        if _cur_lst_len >= 501:
            print("数据超过501条，暂停执行。")
            break

        _pre_lst_len = _cur_lst_len  # 更新旧的列表长度

        # 获取表头文本
        if table_header is None:
            table_header = await page.evaluate('''() => {
                    const ths = Array.from(document.querySelectorAll('table thead tr th'));
                    return ths.map(th => th.innerText);
                }''')

    # 创建 DataFrame
    if all_data:
        df = pd.DataFrame(all_data, columns=table_header)  # 使用表头创建DataFrame
        df = df.drop(df.index[0])
        # 对第一列数据进行进一步切割
        if '快手号' in df.columns:
            # 从'快手号'列中提取'名字'
            df['名字'] = df['快手号'].apply(lambda x: str(x).split('\n', 5)[0])

            # 删除原始的'快手号'列
            df = df.drop(columns=['快手号','操作'])

            # 将'名字'列移动到DataFrame的最前面
            df = df[['名字'] + [col for col in df.columns if col != '名字']]

            # 将"data-row-key"放在最后
            df['url'] = data_row_keys

            # 打印DataFrame
            folder_name = "新快_快手账号库"
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)

            # 生成文件名
            current_date = datetime.datetime.now().strftime('%Y%m%d')
            random_number = random.randint(0, 1000)
            file_name = f"快手号_{current_date}_{random_number}.xlsx"
            file_path = os.path.join(folder_name, file_name)

            # 将DataFrame写入Excel文件
            df.to_excel(file_path, index=False)
            print(f"数据已保存到 {file_path}")
        else:
            print("没有找到名为'快手号'的列")
    else:
        print("未收集到数据")
        return None


async def main():
    # 这里，我们假设您已经有一个运行的浏览器，可以通过WebSocket连接。
    browser = await connect(browserURL='http://127.0.0.1:9222', defaultViewport=None)
    pages = await browser.pages()
    page = pages[0]  # 假设您想要与第一个标签页交互

    # 您需要根据实际情况替换为正确的XPath
    _xpath_for_table = '//*[@id="scrollLayoutContent"]'
    _xpath_for_row = '//*[@id="scrollLayoutContent"]/div[5]/div[2]/div[1]/div/div/div/div/div/div[2]/table/tbody/tr'

    await pull_down_until_end(page, _xpath_for_table, _xpath_for_row)

asyncio.run(main())

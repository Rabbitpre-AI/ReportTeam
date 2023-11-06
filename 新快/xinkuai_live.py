import asyncio
import sys
from pyppeteer import connect
import pandas as pd
import os
import datetime
import random

async def get_data_row_key(page, row_element):
    data_row_key = await page.evaluate('(element) => element.getAttribute("data-row-key")', row_element)
    return data_row_key

async def pull_down_until_end(page, _xpath_for_table, _xpath_for_row):
    _pre_lst_len = 0
    all_data = []  # Used to store all rows of data
    data_row_keys = []  # Create a list to store all the data-row-key
    table_header = None  # Store table header text
    timeout_seconds = 5  # Set the timeout to 5 seconds

    while True:
        # Get the table element
        elements = await page.xpath(_xpath_for_table)
        _table = elements[0] if elements else None

        if not _table:
            print("Table not found")
            break  # If no table is found, exit the loop

        # Scroll to the bottom of the table
        scroll_distance = sys.maxsize  # Or you can use a specific scroll value
        await page.evaluate('''(table, distance) => {
            table.scrollTop += distance;
        }''', _table, scroll_distance)

        # Initialize a counter for the timeout
        elapsed_time = 0

        # Check for new data until the timeout is reached
        while elapsed_time < timeout_seconds:
            await asyncio.sleep(1)  # Wait for 1 second
            elapsed_time += 1  # Increment the elapsed time

            # Check the number of data rows
            row_elements = await page.xpath(_xpath_for_row)
            _cur_lst_len = len(row_elements)

            if _cur_lst_len > _pre_lst_len:
                break  # New data found, break the timeout loop

        if elapsed_time >= timeout_seconds:
            print("No new data within 5 seconds, stopping the scroll.")
            break  # Timeout reached, no new data found

        # Extract the data from all the rows currently fetched
        for row_element in row_elements[_pre_lst_len:]:  # Only process newly loaded rows
            # Get data from all cells in the row
            cell_data = await page.evaluate('''(row) => {
                return Array.from(row.querySelectorAll("td")).map(cell => cell.innerText);
            }''', row_element)

            # Get the data-row-key attribute value of the row
            data_row_key = await get_data_row_key(page, row_element)
            if data_row_key:
                data_row_keys.append(data_row_key)  # Add the data-row-key to the list

            all_data.append(cell_data)  # Add to the data list

        _pre_lst_len = _cur_lst_len  # Update the old list length

        # Get the table header text
        if table_header is None:
            table_header = await page.evaluate('''() => {
                const ths = Array.from(document.querySelectorAll('table thead tr th'));
                return ths.map(th => th.innerText);
            }''')

    # Create DataFrame
    if all_data:
        df = pd.DataFrame(all_data, columns=table_header)
        return data_row_keys, df
    else:
        print("No data collected")
        return None




async def main():
    # 这里，我们假设您已经有一个运行的浏览器，可以通过WebSocket连接。
    browser = await connect(browserURL='http://127.0.0.1:9222', defaultViewport=None)
    pages = await browser.pages()
    page = pages[0]  # 假设您想要与第一个标签页交互

    # 您需要根据实际情况替换为正确的XPath
    _xpath_for_table = '//*[@id="scrollLayoutContent"]'
    _xpath_for_row = '//*[@id="scrollLayoutContent"]/div[6]/div[1]/div[1]/div/div/div/div/div/div[2]/table/tbody/tr'

    data_row_keys,df = await pull_down_until_end(page, _xpath_for_table, _xpath_for_row)
    df = df.drop(df.index[0])

    # # 对第一列数据进行进一步切割
    if '主播' in df.columns:
        # 从'主播'列中提取'名字'
        df['主播名字'] = df['主播'].str.split('\n').str[0]

        # 从'主播'列中提取'标签'
        df['标签'] = df['主播'].str.split('\n').str[1]

        # 从'主播'列中提取'快手号'，假设'快手号'总是跟在'快手号：'后面
        df['快手号'] = df['主播'].apply(lambda x: str(x).split('快手号：')[1].split('\n')[0] if '快手号：' in str(x) else '无')

        # 判断是否存在认证信息，并提取
        df['认证'] = df['主播'].apply(lambda x: str(x).split('\n')[3] if len(str(x).split('\n')) > 4 else '无')

        # 从'主播'列中提取'粉丝数'，假设'粉丝数'总是位于最后
        df['粉丝数'] = df['主播'].apply(lambda x: str(x).split('\n')[-1].split('：')[1] if '粉丝数：' in str(x) else '无')


        # 删除原始的'快手号'列
        df = df.drop(columns=['主播', '操作'])
    #
        # 将'名字'列移动到DataFrame的最前面
        columns_order = ['排名', '主播名字', '标签', '快手号', '认证', '粉丝数', '带货直播场次', '直播商品数', '销售额']

        # 重新排列 DataFrame 的列
        df = df[columns_order]

        # 将"data-row-key"放在最后
        df['row-key'] = data_row_keys
    #
        # 打印DataFrame
        folder_name = "新快_快手主播带货排行榜"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        # 生成文件名
        current_date = datetime.datetime.now().strftime('%Y%m%d')
        random_number = random.randint(0, 1000)
        file_name = f"主播带货排行榜_{current_date}_{random_number}.xlsx"
        file_path = os.path.join(folder_name, file_name)

        # 将DataFrame写入Excel文件
        df.to_excel(file_path, index=False)
        print(f"数据已保存到 {file_path}")
    else:
        print("没有找到名为'主播'的列")
asyncio.run(main())
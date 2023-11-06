import asyncio
from pyppeteer import connect
import pandas as pd
import os
from datetime import datetime
import random

async def main():
    # 这里，我们假设您已经有一个运行的浏览器，可以通过WebSocket连接。
    browser = await connect(browserURL='http://127.0.0.1:9222', defaultViewport=None)
    pages = await browser.pages()
    page = pages[0]  # 假设您想要与第一个标签页交互
    df = pd.read_excel('新快-医生账号数据/快手号医生（已筛选）.xlsx')
    names = df['名字']
    urls = df['url']
    # 设置您想要创建的目录的名称
    folder_name = '新快-医生账号数据'
    # 当前文件的绝对路径
    current_directory = os.getcwd()
    for i in range(10):
        print(f'当前在执行第{i}个，名为{names[i]}')
        await page.goto(urls[i])
        final_data = await test.main()
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
        excel_path = os.path.join(folder_path, f'output_快手{names[i]}{current_date}-{random_number}.xlsx')

        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            for sheet_name, df in final_data.items():
                df.to_excel(writer, sheet_name=sheet_name)
        print(excel_path)
asyncio.run(main())
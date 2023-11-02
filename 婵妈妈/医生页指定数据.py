import asyncio
import time
import pandas as pd
import os
from pyppeteer import connect,errors
from datetime import datetime
import random

async def wait_for_wechat_login_popup(page):
    try:
        # 等待微信登录弹窗出现，设置一个合理的超时时间（例如10秒）
        await page.waitForSelector('div.wechat-pop', timeout=1000)
        print("检测到微信登录弹窗，请手动扫码登录后，输入'开始'以继续程序。")
        # 等待用户输入“开始”以继续
        while True:
            user_input = input("输入'开始'以继续：")
            if user_input.strip() == "开始":
                break
    except:
        # 如果超时（即10秒内未出现微信弹窗），则不执行任何操作，继续程序
        pass
# 数据抓取（静态文字）
async def handle_captcha(page, selector_str, captcha_event):
    while True:
        try:
            captcha_element = await page.querySelector(selector_str)
            if captcha_element:
                print("Captcha detected. Attempting to solve...")
                await captcha_element.click()
                print("Captcha clicked, waiting for 10 seconds for it to resolve.")
                await asyncio.sleep(10)  # 等待10秒以确保验证码得到处理
                print("Captcha should be resolved now, resuming data scraping.")
            else:
                print("No captcha appeared. Continuing with data scraping.")

            captcha_event.set()  # 无论是否出现验证码，都通知系统继续进行
            break  # 跳出循环
        except Exception as e:
            print(f"Error during captcha handling: {str(e)}")
            break  # 如果发生错误，跳出循环
# 粉丝页常用数据
async def fetch_data(page, xpath, field_name, data_dict):
    try:
        # 假设您有一个基于XPath获取数据的函数
        element = await page.waitForXPath(xpath, timeout=5000)  # 等待元素加载，这里设定5秒超时
        text = await page.evaluate('(element) => element.textContent', element)

        # 以下代码根据实际情况进行调整，如果数据清洗或验证是必要的
        data_dict[field_name] = text.strip() if text else None  # 去除可能的空白字符
        return True if text else False
    except Exception as e:
        print(f"在抓取'{field_name}'时发生错误: {e}")
        return False

async def base_data(page, data_dict):
    fields_status = {}  # 用于记录每个字段是否成功获取

    # 抓取各个字段的数据
    fields_status['达人简介'] = await fetch_data(page, '//*[@id="seo-text"]/div/div[1]/div[2]/div[2]/div[2]/div', '达人简介', data_dict)
    fields_status['粉丝总数'] = await fetch_data(page, '//*[@id="seo-text"]/div/div[1]/div[3]/div[1]/div[1]/div[2]/div[1]', '粉丝总数', data_dict)
    fields_status['达人类型'] = await fetch_data(page, '//*[@id="seo-text"]/div/div[1]/div[2]/div[1]/div[3]/div/div[2]/div', '达人类型', data_dict)
    fields_status['认证信息'] = await fetch_data(page, '//*[@id="seo-text"]/div/div[1]/div[2]/div[1]/div[5]/div/div[2]', '认证信息', data_dict)
    fields_status['MCN机构'] = await fetch_data(page, '//*[@id="seo-text"]/div/div[1]/div[2]/div[1]/div[4]/div/div[2]', 'MCN机构', data_dict)

    # 检查是否所有数据都未能抓取成功
    if all(not status for status in fields_status.values()):
        print("所有数据都未能成功抓取，整体数据获取失败。")
        return False  # 整体获取失败，返回失败状态

    # 如果不是所有数据都失败了，那么对于“达人简介”，如果它独自失败了，我们填充默认值
    if not fields_status['达人简介']:
        data_dict['达人简介'] = '-'

    # 检查除了“达人简介”之外是否有其他字段失败
    failed_fields = [field for field, succeeded in fields_status.items() if not succeeded and field != '达人简介']
    if failed_fields:
        print(f"以下字段未能成功抓取: {', '.join(failed_fields)}")  # 列出未成功获取的字段

    return True  # 如果程序能执行到这里，即使有些字段失败，也返回整体操作的成功状态


# 主函数开始
# 假设 handle_captcha 是一个有效的函数，其定义应处理验证码并触发事件
async def main():
    browser = await connect(browserURL='http://127.0.0.1:9222', defaultViewport={'width': 1280, 'height': 720})
    pages = await browser.pages()
    page = pages[0]

    MAX_URLS = 1500
    START_INDEX = 0  # 开始索引

    gender_xpaths = ['//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[5]/div[3]/div/span[1]',
                     '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[5]/div[3]/div/span[2]']

    try:
        df = pd.read_excel('婵妈妈excel数据/测试页.xlsx', engine='openpyxl')
    except Exception as e:
        print(f"无法读取Excel文件: {str(e)}")
        return

    updated_df = df.copy()
    urls = df['达人链接'].tolist()
    urls_to_process = urls[START_INDEX:START_INDEX + MAX_URLS]
    failed_urls = []

    columns_to_check = ['达人简介', '粉丝总数', '达人类型', '认证信息', 'MCN机构']

    for index, url in enumerate(urls_to_process, start=START_INDEX + 1):
        print(f'正在处理第{index}个链接: {url}')

        # 预先检查现有数据，避免重复工作
        existing_row = df[df['达人链接'] == url]
        if not existing_row.empty and all(not pd.isna(existing_row.iloc[0][col]) for col in columns_to_check):
            print(f"链接 {url} 的数据已存在，跳过处理。")
            continue

        try:
            # 添加延迟，避免对服务器造成过大压力
            await page.goto(url, waitUntil='networkidle2')  # 等待网络状态为空闲的时候结束

            captcha_event = asyncio.Event()
            captcha_handler = asyncio.create_task(handle_captcha(page, "#rectMask", captcha_event))

            try:
                # 在这里，我们等待页面可能出现的验证码
                await asyncio.wait_for(captcha_event.wait(), timeout=30.0)
            except asyncio.TimeoutError:
                print("等待验证码超时，继续进行。")
                captcha_event.set()  # 确保设置事件，以便流程可以继续

            data_dict = {}
            success = await base_data(page, data_dict)

            if success:
                row_index = df[df['达人链接'] == url].index
                if not row_index.empty:
                    for key, value in data_dict.items():
                        updated_df.at[row_index[0], key] = value
                else:
                    print(f"没有找到URL {url} 对应的行。")
            else:
                print(f"无法获取 {url} 的数据。")
                failed_urls.append(url)

            # 这里是关键，添加间隔以模拟人类用户的行为
            await asyncio.sleep(0.8)  # 例如，等待2秒钟。这个数值可以根据实际情况调整。

        except Exception as e:
            print(f"处理 {url} 时出错: {str(e)}")
            failed_urls.append(url)

        captcha_handler.cancel()

    try:
        updated_df.to_excel('婵妈妈excel数据/测试页.xlsx', index=False, engine='openpyxl')
        print("Excel文件已更新。")
    except Exception as e:
        print(f"保存Excel文件时出错: {str(e)}")

    if failed_urls:
        print(f'共有{len(failed_urls)}个链接失败。')
        with open('failed_urls.txt', 'w') as file:
            for url in failed_urls:
                file.write(f"{url}\n")
# 主程序入口
if __name__ == "__main__":
    asyncio.run(main())


# 运行主程序
asyncio.run(main())


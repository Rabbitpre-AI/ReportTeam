import asyncio
import time
import pandas as pd
import os
from pyppeteer import connect,errors
from datetime import datetime
import random
async def get_data_from_page(page, xpath):

    # 等待XPath所在的元素加载完成，获取元素的引用
    elements = await page.xpath(xpath)

    # 提取文本数据，如果是其他数据（如属性），您可能需要稍作修改
    results = []
    for element in elements:
        text_content = await page.evaluate('(element) => element.textContent', element)
        results.append(text_content.strip())  # 去除多余空白符，并添加到结果列表中
    # 返回提取到的数据
    return results
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
async def custom_scroll(page,num):
    await page.evaluate(f'window.scrollBy(0, {num})')  # 向下滚动100像素
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
# 横向XPATH版
async def gr_xp(page, num_data_points, canvas_selector, time_selector, data_selectors, data_names, timeout=1000):
    try:
        data_dict = {}

        # 检查canvas元素是否存在
        canvas_elements = await page.xpath(canvas_selector)
        if not canvas_elements:
            print("Canvas元素不存在或不可见")
            return None

        # 等待Canvas元素可见
        await page.waitForXPath(canvas_selector, {"visible": True, "timeout": timeout})

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

            # 直接提取需要的数据，假设是百分比，且它是第一个在data_selectors中的
            try:
                percentage_data = await page.evaluate('''(selector) => {
                    const element = document.evaluate(selector, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    return element.textContent;
                }''', data_selectors[0])  # 这里假设百分比数据是第一个selector

            except Exception as e:
                # print(f"Error while retrieving data: {e}")
                continue  # 如果获取数据时出错，则跳过此点

            try:
                # 提取时间数据
                time_content = await page.evaluate('''(selector) => {
                    const element = document.evaluate(selector, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    return element.textContent;
                }''', time_selector)

                # 构建数据字典
                if time_content not in data_dict:
                    data_dict[time_content] = percentage_data  # 使用百分比数据

            except Exception as e:
                print(f"Error while retrieving time: {e}")

        # 按时间排序数据
        sorted_data = dict(sorted(data_dict.items()))

        return sorted_data

    except Exception as e:
        print(f"处理图为'{canvas_selector}'的元素时出错: {e}")
        return None

async def fans_age_distribution(page,po_nums):
    canvas_selector = '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[5]/div[4]/div[1]/div[2]/div/div/div[1]/div[1]/canvas'
    time_selector = '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[5]/div[4]/div[1]/div[2]/div/div/div[1]/div[2]/div/div/div/div[1]'
    data_selectors = [
        '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[5]/div[4]/div[1]/div[2]/div/div/div[1]/div[2]/div/div/div/div[2]/span[2]']
    data_names = ['占比']
    data = await gr_xp(page, po_nums, canvas_selector, time_selector, data_selectors, data_names)
    return data

async def main():
    browser = await connect(browserURL='http://127.0.0.1:9222', defaultViewport={'width': 1280, 'height': 720})
    pages = await browser.pages()
    page = pages[0]
    START_INDEX = 200
    END_INDEX = 300  # 您可以根据需要调整这个值
    try:
        df = pd.read_excel('婵妈妈excel数据/测试页.xlsx', engine='openpyxl')
    except Exception as e:
        print(f"无法读取Excel文件: {str(e)}")
        return

    # 在处理博主之前，创建一个空的DataFrame来存储所有数据
    all_data_columns = ['博主名称', '粉丝量', '18-23岁', '24-30岁', '31-40岁', '41-50岁', '>50岁']  # 添加您需要的列
    all_data_df = pd.DataFrame(columns=all_data_columns)

    urls_to_process = df['达人链接'].tolist()
    blogger_names = df['达人title'].tolist()

    today_str = datetime.now().strftime('%Y%m%d')

    # 创建一个新文件夹来存储Excel文件
    folder_name = 'output_医生'
    os.makedirs(folder_name, exist_ok=True)

    error_urls = []  # 存储出错的URLs
    for index in range(START_INDEX, min(END_INDEX, len(urls_to_process))):
        url = urls_to_process[index] + '/fans'
        blogger_name = blogger_names[index]
        print(f'正在处理第{index + 1}个链接: {url}')

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
            await asyncio.sleep(0.5)
            fans_data = await get_data_from_page(page,'//*[@id="seo-text"]/div/div[1]/div[3]/div[1]/div[1]/div[2]/div[1]')

            await custom_scroll(page,600)
            await mouse_text(page, '视频观众')
            await asyncio.sleep(1)

            data = await fans_age_distribution(page,30)  # 例如：粉丝年龄分布

            # 准备新行数据
            new_row = data
            new_row['博主名称'] = blogger_name
            new_row['粉丝量'] = fans_data[0]
            print(new_row)
            # 添加到总数据集中
            current_data = pd.DataFrame([new_row], columns=all_data_columns)
            # 使用concat而不是append。这样可以避免在未来的pandas版本中可能出现的问题。
            all_data_df = pd.concat([all_data_df, current_data], ignore_index=True)
            captcha_handler.cancel()
        except Exception as e:
            print(f"处理 {url} 时出错: {e}")
            error_urls.append(url)  # 将有问题的URL添加到列表中
        # 循环结束后，保存所有数据到一个Excel文件
    if not all_data_df.empty:
        try:
            output_file_path = os.path.join(folder_name, f'all_bloggers_data_{today_str}.xlsx')
            all_data_df.to_excel(output_file_path, index=False)
            print(f"所有数据已保存到 {output_file_path}")
        except Exception as e:
            print(f"保存Excel文件出错: {str(e)}")
    else:
        print("没有数据可保存。")
    # 如果有出错的URLs，我们将它们写入到一个文件中以便之后分析
    if error_urls:
        with open('医生图表_error_urls.txt', 'w') as f:
            for url in error_urls:
                f.write(url + '\n')
        print(f"有 {len(error_urls)} 个URL处理出错. 详情请查看 '医生图表_error_urls.txt'.")
asyncio.run(main())
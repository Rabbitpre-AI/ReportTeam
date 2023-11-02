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
async def custom_scroll(page,num):
    await page.evaluate(f'window.scrollBy(0, {num})')  # 向下滚动100像素
# 图表读取（css路径）
async def gr(page,num_data_points, canvas_selector, time_selector, data_selectors, data_names, timeout=1000):
    data_dict = {}

    try:

        # 检查canvas元素是否存在
        canvas_element = await page.querySelector(canvas_selector)
        if canvas_element:
            await page.waitForSelector(canvas_selector, {"visible": True, "timeout": timeout})
        else:
            print("Canvas元素不存在或不可见")
            return None

        canvas_info = await page.evaluate(f"""
            (selector) => {{
                const element = document.querySelector(selector);
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

            data_content = {}
            for j, selector in enumerate(data_selectors):
                try:
                    content = await page.evaluate(f'(selector) => document.querySelector(selector).textContent',
                                                  selector)
                    data_content[data_names[j]] = content
                except Exception as e:
                    pass
            try:
                time_content = await page.evaluate(f'(selector) => document.querySelector(selector).textContent',
                                                   time_selector)
                if time_content not in data_dict:
                    data_dict[time_content] = data_content
            except Exception as e:
                pass

        # 按时间排序
        sorted_data = dict(sorted(data_dict.items()))
        return sorted_data

    except Exception as e:
        print(f"处理图为'{canvas_selector}'的元素时出错: {e}")
        return None

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
# 粉丝趋势
async def fans_trends(page,po_nums):
    canvas_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.flex > div:nth-child(1) > div.fans-chart.relative > div > div.full.chart-box > div:nth-child(1) > canvas'
    time_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.flex > div:nth-child(1) > div.fans-chart.relative > div > div.full.chart-box > div:nth-child(2) > div.cfff.font-weight-500.fs12'
    data_selectors = [
        '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.flex > div:nth-child(1) > div.fans-chart.relative > div > div.full.chart-box > div:nth-child(2) > div:nth-child(2) > span:nth-child(3)',
        '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.flex > div:nth-child(1) > div.fans-chart.relative > div > div.full.chart-box > div:nth-child(2) > div:nth-child(3) > span:nth-child(3)'
    ]
    data_names = ['总量', '销量']
    data = await gr(page, po_nums, canvas_selector, time_selector, data_selectors, data_names)

    if data is None:
        return None  # 如果没有数据，我们可能需要返回None或者一个空的结构

    fans_trend_data = []

    # 根据从 'gr' 函数收集的数据格式，这里可能需要一些调整。
    # 假设 'data' 的结构类似于之前提供的字典结构。
    for date, metrics in data.items():  # 去掉了['粉丝趋势']，因为看起来data就是我们需要的数据
        record = {
            '日期': date,
            # '总量' 和 '销量' 的值可能需要根据实际从网站获取的数据格式进行调整。
            '总量': metrics['总量'],
            '销量': metrics['销量']
        }
        fans_trend_data.append(record)
    if not fans_trend_data:  # 如果没有数据
        return False

    # 将列表转换为DataFrame
    df_fans_trend = pd.DataFrame(fans_trend_data)

    return df_fans_trend
# 粉丝画像

async def extract_gender_data(page, gender_xpaths):
    """
    根据提供的XPath列表从指定页面提取性别数据。

    参数:
        page: 页面对象，由pyppeteer库提供，用于页面交互。
        gender_xpaths (list of str): 性别数据元素的XPath列表。

    返回:
        DataFrame 或者 None: 如果提取到数据，返回包含性别和百分比数据的DataFrame；否则返回None。
    """
    gender_distribution_data = []  # 用于存储性别和百分比数据的列表

    for index, xpath in enumerate(gender_xpaths):
        try:
            element = await page.waitForXPath(xpath)  # 等待元素加载
            content = await page.evaluate('(element) => element.textContent', element)

            if content:
                parts = content.strip().split(' ')  # 假设文本内容格式为"男 33%"
                if len(parts) == 2:
                    gender, percentage = parts

                    # 如果是第二个xpath (索引为1)，则逆序
                    if index == 1:
                        gender, percentage = percentage, gender

                    gender_distribution_data.append({'性别': gender, '百分比': percentage})
        except Exception as e:
            print(f"Error occurred while extracting data: {e}")

    # 如果gender_distribution_data有数据，则转换为DataFrame
    if gender_distribution_data:
        return pd.DataFrame(gender_distribution_data)
    else:
        return None

async def extract_regional_data(page):
    regional_distribution_data = []  # 用于存储地域和百分比数据的列表
    for i in range(1, 10 + 1):
        # 构建XPath
        province_xpath = f'//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[5]/div[4]/div[2]/div[2]/div/div[{i}]/span[1]/span'
        percentage_xpath = f'//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[5]/div[4]/div[2]/div[2]/div/div[{i}]/span[2]'

        try:
            # 获取省份
            province_element = await page.waitForXPath(province_xpath, timeout=5000)
            province = await page.evaluate('(element) => element.textContent', province_element)

            # 获取百分比
            percentage_element = await page.waitForXPath(percentage_xpath, timeout=5000)
            percentage = await page.evaluate('(element) => element.textContent', percentage_element)

            # 如果成功获取数据，则添加到列表中
            if province and percentage:
                regional_distribution_data.append({'省份': province.strip(), '百分比': percentage.strip()})
        except Exception as e:
            print(f"Error fetching data for entry {i}: {e}")
    if not regional_distribution_data:  # 如果列表为空
        return False
    # 根据收集到的数据创建DataFrame
    df_regional = pd.DataFrame(regional_distribution_data)

    # 返回DataFrame
    return df_regional# 粉丝年龄分布

async def fans_age_distribution(page,po_nums):
    canvas_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.fans-pic-wrapper.pb20 > div.flex.mt35.mb20 > div.flex-1.mr20 > div.box-height.relative > div > div > div.full.chart-box > div:nth-child(1) > canvas'
    time_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.fans-pic-wrapper.pb20 > div.flex.mt35.mb20 > div.flex-1.mr20 > div.box-height.relative > div > div > div.full.chart-box > div:nth-child(2) > div > div > div > div:nth-child(1)'
    data_selectors = [
        '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.fans-pic-wrapper.pb20 > div.flex.mt35.mb20 > div.flex-1.mr20 > div.box-height.relative > div > div > div.full.chart-box > div:nth-child(2) > div > div > div > div.flex.align-items-center > span:nth-child(2)']
    data_names = ['占比']
    data = await gr(page, po_nums, canvas_selector, time_selector, data_selectors, data_names)


    # 准备一个列表，将数据字典转换为DataFrame所需的格式
    age_distribution_list = []

    for age_range, info in data.items():
        # 提取占比信息
        percentage_info = info.get('占比', '0')  # 如果没有'占比'数据，则默认为'0'
        age_distribution_list.append({
            '年龄区间': age_range,
            '占比': percentage_info
        })
    if not age_distribution_list:  # 如果没有数据
        # print('粉丝年龄分布没有完成')
        return False
    # 使用列表创建DataFrame
    df_age_distribution = pd.DataFrame(age_distribution_list)
    return df_age_distribution  # 返回创建的DataFrame

async def main():
    # 初始化浏览器和页面
    browser = await connect(browserURL='http://127.0.0.1:9222', defaultViewport=None)
    pages = await browser.pages()
    page = pages[0]
    gender_xpaths = ['//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[5]/div[3]/div/span[1]',
                     '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[5]/div[3]/div/span[2]']

    START_INDEX = 1060
    END_INDEX = 1500  # 您可以根据需要调整这个值

    # 从Excel读取数据
    try:
        df = pd.read_excel('婵妈妈excel数据/测试页.xlsx', engine='openpyxl')
    except Exception as e:
        print(f"无法读取Excel文件: {str(e)}")
        return

    urls_to_process = df['达人链接'].tolist()
    blogger_names = df['达人title'].tolist()

    today_str = datetime.now().strftime('%Y%m%d')
    shared_random_number = random.randint(0, 1000)

    # 创建一个新文件夹来存储Excel文件
    folder_name = 'output_医生'
    os.makedirs(folder_name, exist_ok=True)

    error_urls = []  # 存储出错的URLs
    # 设置观测器，在后台等待微信登录弹窗的出现
    # page.on('load', lambda: asyncio.ensure_future(wait_for_wechat_login_popup(page)))
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

            # 假设您有一系列的数据抓取函数，它们可能返回False或实际的数据
            data1 = await fans_trends(page, 30)  # 例如：获取粉丝趋势
            await custom_scroll(page,600)
            await mouse_text(page, '视频观众')
            data4 = await extract_gender_data(page, gender_xpaths)  # 例如：性别数据
            await asyncio.sleep(1)
            data3 = await fans_age_distribution(page, 5)  # 例如：粉丝年龄分布
            await asyncio.sleep(1)
            data2 = await extract_regional_data(page)  # 例如：提取地域数据

            # 检查哪些数据是有效的，并只收集有效的数据
            used_data = 0
            all_data = {}
            if data1 is not False:  # 假设函数在失败时返回False
                all_data["粉丝趋势"] = data1
                used_data += 1
            if data2 is not False:
                all_data["地域分布"] = data2
                used_data += 1
            if data3 is not False:
                all_data["粉丝年龄分布"] = data3
                used_data += 1
            if data4 is not False:
                all_data["性别分布"] = data4
                used_data += 1
            # 打印非False的键
            valid_keys = [key for key in all_data.keys() if all_data[key] is not False]
            print(f'共完成{used_data}个sheet，分别是：{", ".join(valid_keys)}')
            # 如果我们没有从该页面中提取到任何数据，我们记录下这个URL
            if not all_data:
                error_urls.append(url)
                print(f"无法从 {url} 提取数据.")
                continue  # 跳过此URL，继续处理下一个URL

            # 如果我们有数据，那么保存这些数据到一个新的Excel文件
            clean_blogger_name = ''.join(e for e in blogger_name if e.isalnum())
            filename = f"{clean_blogger_name}_{shared_random_number}.xlsx"
            filepath = os.path.join(folder_name, filename)

            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                for sheet_name, data_frame in all_data.items():
                    data_frame.to_excel(writer, sheet_name=sheet_name, index=False)

            print(f'数据已保存到 {filepath}')
            await asyncio.sleep(1.5)
            captcha_handler.cancel()
        except Exception as e:
            print(f"处理 {url} 时出错: {e}")
            error_urls.append(url)  # 将有问题的URL添加到列表中

    # 如果有出错的URLs，我们将它们写入到一个文件中以便之后分析
    if error_urls:
        with open('医生图表_error_urls.txt', 'w') as f:
            for url in error_urls:
                f.write(url + '\n')
        print(f"有 {len(error_urls)} 个URL处理出错. 详情请查看 'error_urls.txt'.")
# 启动异步事件循环
asyncio.run(main())
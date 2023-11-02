from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException,ElementNotInteractableException
import asyncio
import time
import pandas as pd
import os
from pyppeteer import connect
from datetime import datetime
import random

'''基础工具'''
async def custom_scroll(num):
    browser = await connect(browserURL='http://127.0.0.1:9222', defaultViewport={'width': 1280, 'height': 720})
    pages = await browser.pages()
    page = pages[0]
    await page.evaluate(f'window.scrollBy(0, {num})')  # 向下滚动100像素

async def gr(num_data_points, canvas_selector, time_selector, data_selectors, data_names, timeout=1000):
    data_dict = {}

    try:
        browser = await connect(browserURL='http://127.0.0.1:9222', defaultViewport={'width': 1280, 'height': 720})
        pages = await browser.pages()
        page = pages[0]

        # 检查canvas元素是否存在
        canvas_element = await page.querySelector(canvas_selector)
        if canvas_element:
            await page.waitForSelector(canvas_selector, {"visible": True, "timeout": timeout})
        else:
            print("Canvas元素不存在或不可见")
            await browser.disconnect()
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
        await browser.disconnect()

        return sorted_data

    except Exception as e:
        print(f"处理图为'{canvas_selector}'的元素时出错: {e}")
        return None

# 纵向
async def up_to_down(num_data_points, canvas_selector, time_selector, data_selectors, data_names,timeout=1000):
    data_dict = {}
    # 检查canvas元素是否存在或不可见
    try:
        browser = await connect(browserURL='http://127.0.0.1:9222', defaultViewport={'width': 1280, 'height': 720})
        pages = await browser.pages()
        page = pages[0]
        # 检查canvas元素是否存在
        canvas_element = await page.querySelector(canvas_selector)
        if canvas_element:
            await page.waitForSelector(canvas_selector, {"visible": True, "timeout": timeout})
        else:
            print("Canvas元素不存在或不可见")
            await browser.disconnect()
            return None

        await page.waitForSelector(canvas_selector, {"visible": True, "timeout": 1000})

        canvas_info = await page.evaluate(f"""
            (selector) => {{
                const element = document.querySelector(selector);
                const {{ x, y, width, height }} = element.getBoundingClientRect();
                return {{ x, y, width, height }};
            }}
        """, canvas_selector)

        bottom_y = canvas_info['y'] + canvas_info['height']
        top_y = canvas_info['y']
        interval = (bottom_y - top_y) / (num_data_points - 1)

        for i in range(num_data_points):
            hover_y = bottom_y - interval * i
            await page.mouse.move(canvas_info['x'] + canvas_info['width'] / 2, hover_y)

            data_content = {}
            for j, selector in enumerate(data_selectors):
                try:
                    # First, try to get the element
                    element = await page.querySelector(selector)
                    if element:
                        content = await page.evaluate('(element) => element.textContent', element)
                        data_content[data_names[j]] = content
                    else:
                        pass
                except Exception as e:
                    # print(f"Error for selector {selector}: {e}")
                    pass

            try:
                time_element = await page.querySelector(time_selector)
                if time_element:
                    time_content = await page.evaluate('(element) => element.textContent', time_element)
                    if time_content not in data_dict:
                        data_dict[time_content] = data_content
                else:
                    pass
                    # print(f"Element with time selector {time_selector} not found!")
            except Exception as e:
                pass
                # print(f"Error for time selector {time_selector}: {e}")
        sorted_data_dict = dict(sorted(data_dict.items(), key=lambda x: x[0]))
        await browser.disconnect()
        return sorted_data_dict
    except Exception as e:
        print(f"处理图为'{canvas_selector}'的元素时出错: {e}")
        return None

# 横向XPATH版
async def gr_xp(num_data_points, canvas_selector, time_selector, data_selectors, data_names,timeout=1000):
    try:
        data_dict = {}
        browser = await connect(browserURL='http://127.0.0.1:9222', defaultViewport={'width': 1280, 'height': 720})
        pages = await browser.pages()
        page = pages[0]

        # 检查canvas元素是否存在
        canvas_elements = await page.xpath(canvas_selector)
        if not canvas_elements:
            print("Canvas元素不存在或不可见")
            await browser.disconnect()
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

            data_content = {}
            for j, selector in enumerate(data_selectors):
                try:
                    content = await page.evaluate('''(selector) => {
                        const element = document.evaluate(selector, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                        return element.textContent;
                    }''', selector)
                    data_content[data_names[j]] = content
                except Exception as e:
                    # print(f"Error while processing data point {i} for {data_names[j]}: {e}")
                    pass
            try:
                time_content = await page.evaluate('''(selector) => {
                    const element = document.evaluate(selector, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    return element.textContent;
                }''', time_selector)
                if time_content not in data_dict:
                    data_dict[time_content] = data_content
            except:
                pass
        # 按时间排序
        sorted_data = dict(sorted(data_dict.items()))
        await browser.disconnect()

        return sorted_data
    except Exception as e:
        print(f"处理图为'{canvas_selector}'的元素时出错: {e}")
        return None

# 鼠标点击
async def mouse(text):
        browser = await connect(browserURL='http://127.0.0.1:9222', defaultViewport={'width': 1280, 'height': 720})
        pages = await browser.pages()
        page = pages[0]
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

def fetch_data(wait, xpath, key_name, data_dict):
    """
    尝试获取网页上的特定数据。

    :param driver: WebDriver 实例
    :param xpath: 要查找元素的 XPATH
    :param key_name: 字典中的键名
    :param data_dict: 存储数据的字典
    """
    try:
        element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        data_text = element.text
    except TimeoutException:
        data_text = "0"  # 如果发生超时异常，设置默认值
    data_dict[key_name] = data_text

def base_data(driver,url,data_dict):
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 1)
        # 使用fetch_data函数获取数据
        fetch_data(wait,'//*[@id="seo-text"]/div/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]','账号名称',data_dict)
        fetch_data(wait, '//*[@id="seo-text"]/div/div[1]/div[2]/div[1]/div[1]/div[2]/div[1]', '性别', data_dict)
        fetch_data(wait,'//*[@id="seo-text"]/div/div[1]/div[2]/div[1]/div[1]/div[2]/div[2]/div','年龄',data_dict)
        fetch_data(wait, '//*[@id="seo-text"]/div/div[1]/div[2]/div[1]/div[2]/div/div[2]', '地区', data_dict)
        fetch_data(wait, '//*[@id="seo-text"]/div/div[1]/div[2]/div[1]/div[3]/div/div[2]/div', '达人类型', data_dict)
        fetch_data(wait, '//*[@id="seo-text"]/div/div[1]/div[2]/div[1]/div[4]/div/div[2]', 'MCN机构', data_dict)
        fetch_data(wait, '//*[@id="seo-text"]/div/div[1]/div[2]/div[1]/div[5]/div/div[2]', '认证信息', data_dict)
        fetch_data(wait, '//*[@id="seo-text"]/div/div[1]/div[2]/div[2]/div[2]/div', '达人简介', data_dict)
        fetch_data(wait, '//*[@id="seo-text"]/div/div[1]/div[3]/div[1]/div[1]/div[2]/div[1]', '粉丝总数', data_dict)
        fetch_data(wait, '//*[@id="seo-text"]/div/div[1]/div[3]/div[1]/div[2]/div[2]/div/div', '粉丝团数', data_dict)
        fetch_data(wait, '//*[@id="seo-text"]/div/div[1]/div[3]/div[1]/div[3]/div[2]/div', '带货口碑', data_dict)
        fetch_data(wait, '//*[@id="seo-text"]/div/div[1]/div[3]/div[1]/div[4]/div[2]', '星图指数', data_dict)
        fetch_data(wait, '//*[@id="seo-text"]/div/div[1]/div[3]/div[1]/div[5]/div/div/div', '直播带货力', data_dict)
        fetch_data(wait, '//*[@id="seo-text"]/div/div[1]/div[3]/div[1]/div[6]/div/div/div', '视频带货力', data_dict)
        fetch_data(wait, '//*[@id="seo-text"]/div/div[1]/div[3]/div[2]/div[1]/div[2]/div', '粉丝量级', data_dict)
        fetch_data(wait, '//*[@id="seo-text"]/div/div[1]/div[3]/div[2]/div[2]/div[2]', '主营类型', data_dict)
        fetch_data(wait, '//*[@id="seo-text"]/div/div[1]/div[3]/div[1]/div[5]/div[2]/div', '带货水平', data_dict)
        fetch_data(wait, '//*[@id="seo-text"]/div/div[1]/div[3]/div[2]/div[4]/div[2]/div', '带货信息', data_dict)
        fetch_data(wait, '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[1]/div/div[1]/div[4]/div[1]/div['
                         '1]/div[2]/div','直播场次', data_dict)
        fetch_data(wait,'//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[1]/div/div[1]/div[4]/div[1]/div['
                        '1]/div[3]/div[2]/span','历史总场次', data_dict)
        fetch_data(wait, '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[1]/div/div[1]/div[4]/div[1]/div['
                         '2]/div[2]/div','平均开播时长', data_dict)
        fetch_data(wait,'//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[1]/div/div[1]/div[4]/div[1]/div['
                        '3]/div[2]/div','直播累计销量', data_dict)
        fetch_data(wait,'//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[1]/div/div[1]/div[4]/div[1]/div['
                        '3]/div[3]/div[2]/span','场均销量', data_dict)
        fetch_data(wait,'//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[1]/div/div[1]/div[4]/div[1]/div['
                        '3]/div[4]/div[2]/span','日均销量', data_dict)
        fetch_data(wait, '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[1]/div/div[1]/div[4]/div[1]/div['
                         '4]/div[2]/div/span','直播累计销售额', data_dict)
        fetch_data(wait,'//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[1]/div/div[1]/div[4]/div[1]/div['
                        '4]/div[3]/div[2]/span', '场均销售额', data_dict)
        fetch_data(wait,'//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[1]/div/div[1]/div[4]/div[1]/div['
                        '4]/div[4]/div[2]/span','日均销售额', data_dict)
        fetch_data(wait,'//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[1]/div/div[1]/div[4]/div[2]/div[1]/div[2]/div','视频数量', data_dict)
        fetch_data(wait,'//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[1]/div/div[1]/div[4]/div[2]/div[1]/div[3]/div[2]','历史总视频数', data_dict)

        # 在此处，您可以继续添加更多的数据字段和异常处理，每个部分都应该有相应的中文注释来标明它代表的数据点。

        # 平均视频时长
        try:
            average_video_duration_min = wait.until(EC.presence_of_element_located((By.XPATH,
                                                                                    '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[1]/div/div[1]/div[4]/div[2]/div[2]/div[2]/span[1]'))).text
            average_video_duration_sec = wait.until(EC.presence_of_element_located((By.XPATH,
                                                                                    '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[1]/div/div[1]/div[4]/div[2]/div[2]/div[2]/span[3]'))).text
            average_video_duration = average_video_duration_min + ' 分 ' + average_video_duration_sec + '秒'
            data_dict['平均视频时长'] = average_video_duration
        except TimeoutException:
            data_dict['平均视频时长'] = "0"

        # 平均点赞数
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[1]/div/div[1]/div[4]/div[2]/div[2]/div[3]/div[2]',
                   '平均点赞数', data_dict)

        # 平均赞粉比
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[1]/div/div[1]/div[4]/div[2]/div[2]/div[4]/div[2]',
                   '平均赞粉比', data_dict)

        # 视频累计销量
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[1]/div/div[1]/div[4]/div[2]/div[3]/div[2]/div',
                   '视频累计销量', data_dict)

        # 平均销量
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[1]/div/div[1]/div[4]/div[2]/div[3]/div[3]/div[2]',
                   '平均销量', data_dict)

        # 视频累计销售额
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[1]/div/div[1]/div[4]/div[2]/div[4]/div[2]/div',
                   '视频累计销售额', data_dict)

        # 平均销售额
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[1]/div/div[1]/div[4]/div[2]/div[4]/div['
                   '3]/div[2]',
                   '平均销售额', data_dict)


    except Exception as e:

        print(f"An error occurred: {e}")

        # 关闭当前标签页并返回之前的标签页

def click_radio_button_by_value(driver,xpath):
    try:
        # 等待直到预期的元素可见，这里我们直接寻找 <input> 元素
        element = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        # 尝试点击元素
        element.click()
        print('成功点击')
    except TimeoutException:
        print("加载时间过长，元素未能出现。")
    except ElementNotInteractableException:
        print("元素不可交互。")
    except Exception as e:
        print(f"尝试点击时出现错误: {e}")

        # 如果常规点击失败，尝试使用JavaScript执行点击
        try:
            driver.execute_script("arguments[0].click();", element)
        except Exception as e_script:
            print(f"JavaScript点击时出现错误: {e_script}")

""" 带货分析页 """

# 直播带货
def live_sales(po_nums):
    canvas_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.flex.mt10.live-aweme-chart > div:nth-child(1) > div.chart-wrapper.relative > div > div.full.chart-box > div:nth-child(1) > canvas'
    time_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.flex.mt10.live-aweme-chart > div:nth-child(1) > div.chart-wrapper.relative > div > div.full.chart-box > div:nth-child(2) > div.cfff.font-weight-500.fs12'
    data_selectors = [
        '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.flex.mt10.live-aweme-chart > div:nth-child(1) > div.chart-wrapper.relative > div > div.full.chart-box > div:nth-child(2) > div:nth-child(2) > span:nth-child(3)',
        '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.flex.mt10.live-aweme-chart > div:nth-child(1) > div.chart-wrapper.relative > div > div.full.chart-box > div:nth-child(2) > div:nth-child(3) > span:nth-child(3)']
    data_names = ['销量', '销售额']
    data = asyncio.run(gr(po_nums, canvas_selector, time_selector, data_selectors, data_names))
    if data == None:
        print('直播带货图没有完成')
    else:
        print('直播带货图完成')
    return data
# print(live_sales(10))

# 视频带货
def video_sales_trends(po_nums):
    canvas_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.flex.mt10.live-aweme-chart > div:nth-child(2) > div.chart-wrapper.relative > div > div.full.chart-box > div:nth-child(1) > canvas'
    time_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.flex.mt10.live-aweme-chart > div:nth-child(2) > div.chart-wrapper.relative > div > div.full.chart-box > div:nth-child(2) > div.cfff.font-weight-500.fs12'
    data_selectors = [
        '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.flex.mt10.live-aweme-chart > div:nth-child(2) > div.chart-wrapper.relative > div > div.full.chart-box > div:nth-child(2) > div:nth-child(2) > span:nth-child(3)',
        '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.flex.mt10.live-aweme-chart > div:nth-child(2) > div.chart-wrapper.relative > div > div.full.chart-box > div:nth-child(2) > div:nth-child(3) > span:nth-child(3)']
    data_names = ['销量', '销售额']
    data = asyncio.run(gr(po_nums, canvas_selector, time_selector, data_selectors, data_names))
    print('视频带货图完成')
    return data
# print(video_sales_trends(50))

# 近30天直播爆品-销量-销售额
def live_top30_sales(po_nums):
    canvas_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.product-info-wrapper.flex.pt20 > div.flex-1.pl20.flex.flex-direction-column > div.flex-1.relative > div > div.full.chart-box > div:nth-child(1) > canvas'
    time_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.product-info-wrapper.flex.pt20 > div.flex-1.pl20.flex.flex-direction-column > div.flex-1.relative > div > div.full.chart-box > div:nth-child(2) > div.cfff.font-weight-500.fs12'
    data_selectors = ['#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.product-info-wrapper.flex.pt20 > div.flex-1.pl20.flex.flex-direction-column > div.flex-1.relative > div > div.full.chart-box > div:nth-child(2) > div.mt5.cfff.font-weight-400.fs12 > span:nth-child(3)']
    data_names = ['销量']
    data = asyncio.run(gr(po_nums, canvas_selector, time_selector, data_selectors, data_names))
    print('完成')
    return data
# print(live_top30_sales(50))

""" 粉丝分析页 """

# 粉丝趋势
def fans_trends(po_nums):
    canvas_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.flex > div:nth-child(1) > div.fans-chart.relative > div > div.full.chart-box > div:nth-child(1) > canvas'
    time_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.flex > div:nth-child(1) > div.fans-chart.relative > div > div.full.chart-box > div:nth-child(2) > div.cfff.font-weight-500.fs12'
    data_selectors = [
        '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.flex > div:nth-child(1) > div.fans-chart.relative > div > div.full.chart-box > div:nth-child(2) > div:nth-child(2) > span:nth-child(3)',
        '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.flex > div:nth-child(1) > div.fans-chart.relative > div > div.full.chart-box > div:nth-child(2) > div:nth-child(3) > span:nth-child(3)'
    ]
    data_names = ['总量', '销量']

    data = asyncio.run(gr(po_nums, canvas_selector, time_selector, data_selectors, data_names))
    if data == None:
        print('粉丝趋势没有完成')
    else:
        print('粉丝趋势图完成')
    return data
# print(fan_trends(50))

# 粉丝团趋势
def fans_group_trend(po_nums):
    canvas_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.flex > div:nth-child(2) > div.fans-chart.relative > div > div.full.chart-box > div:nth-child(1) > canvas'
    time_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.flex > div:nth-child(2) > div.fans-chart.relative > div > div.full.chart-box > div:nth-child(2) > div.cfff.font-weight-500.fs12'
    data_selectors = [
        '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.flex > div:nth-child(2) > div.fans-chart.relative > div > div.full.chart-box > div:nth-child(2) > div:nth-child(2) > span:nth-child(3)',
        '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.flex > div:nth-child(2) > div.fans-chart.relative > div > div.full.chart-box > div:nth-child(2) > div:nth-child(3) > span:nth-child(3)'
    ]
    data_names = ['总量', '增量']

    data = asyncio.run(gr(po_nums, canvas_selector, time_selector, data_selectors, data_names))
    if data == None:
        print('粉丝趋势团没有完成')
    else:
        print('粉丝趋势团完成')
    return data
# print(fans_group_trend(50))

# 粉丝年龄分布
def fans_age_distribution(po_nums):
    canvas_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.fans-pic-wrapper.pb20 > div.flex.mt35.mb20 > div.flex-1.mr20 > div.box-height.relative > div > div > div.full.chart-box > div:nth-child(1) > canvas'
    time_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.fans-pic-wrapper.pb20 > div.flex.mt35.mb20 > div.flex-1.mr20 > div.box-height.relative > div > div > div.full.chart-box > div:nth-child(2) > div > div > div > div:nth-child(1)'
    data_selectors = [
        '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.fans-pic-wrapper.pb20 > div.flex.mt35.mb20 > div.flex-1.mr20 > div.box-height.relative > div > div > div.full.chart-box > div:nth-child(2) > div > div > div > div.flex.align-items-center > span:nth-child(2)']
    data_names = ['占比']
    data = asyncio.run(gr(po_nums, canvas_selector, time_selector, data_selectors, data_names))
    if data == None:
        print('粉丝年龄分布没有完成')
    else:
        print('粉丝年龄分布图完成')
    return data
# print(age_distribution(50))

# 直播年龄分布
def fans_live_age_distribution(po_nums):
    canvas_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.fans-pic-wrapper.pb20 > div.flex.mt35.mb20 > div.flex-1.mr20 > div.box-height.relative > div > div > div.full.chart-box > div:nth-child(1) > canvas'
    time_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.fans-pic-wrapper.pb20 > div.flex.mt35.mb20 > div.flex-1.mr20 > div.box-height.relative > div > div > div.full.chart-box > div:nth-child(2) > div > div > div > div:nth-child(1)'
    data_selectors = [
        '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.fans-pic-wrapper.pb20 > div.flex.mt35.mb20 > div.flex-1.mr20 > div.box-height.relative > div > div > div.full.chart-box > div:nth-child(2) > div > div > div > div.flex.align-items-center > span:nth-child(2)']
    data_names = ['占比']
    data = asyncio.run(gr(po_nums, canvas_selector, time_selector, data_selectors, data_names))
    if data == None:
        print('直播年龄分布没有完成')
    else:
        print('直播年龄分布图完成')
    return data
# print(live__distribution(50))

"""直播分析"""

# 直播趋势分析
def live_trends(po_nums):
    result = {}
    labels =['观看人次','销量','销售额']
    for label in labels:
        asyncio.run(mouse(label))
        if label =='观看人次':
            canvas_selector = '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[2]/div/div[2]/div/div[1]/div[1]/canvas'
            time_selector = '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[2]/div/div[2]/div/div[1]/div[2]/text()[1]'
            data_selectors = [
                '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[2]/div/div[2]/div/div[1]/div[2]/text()[2]',
                '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[2]/div/div[2]/div/div[1]/div[2]/div[1]',
                '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[2]/div/div[2]/div/div[1]/div[2]/text()[4]',
                '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[2]/div/div[2]/div/div[1]/div[2]/div[2]',
                '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[2]/div/div[2]/div/div[1]/div[2]/text()[5]']
            data_names = ['总人数', '总场次', '开播时间（1）', '观看人数（1）', '开播时间（2)', '观看人数（2）']
            data = asyncio.run(gr_xp(po_nums, canvas_selector, time_selector, data_selectors, data_names))

        else:
            canvas_selector ='#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div:nth-child(2) > div.pt20 > div > div:nth-child(2) > div > div.full.chart-box > div:nth-child(1) > canvas'
            time_selector ='#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div:nth-child(2) > div.pt20 > div > div:nth-child(2) > div > div.full.chart-box > div:nth-child(2) > div.cfff.font-weight-500.fs12'
            data_selectors =['#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div:nth-child(2) > div.pt20 > div > div:nth-child(2) > div > div.full.chart-box > div:nth-child(2) > div.mt5.cfff.font-weight-400.fs12 > span:nth-child(3)']
            data_names = [label]
            data = asyncio.run(gr(po_nums, canvas_selector, time_selector, data_selectors, data_names))
        result[label] = data
        print(f'完成了{label}的图')
    return result
# print(live_trends(20))

# 直播流量结构
def live_stream_traffic(po_nums):
    canvas_selector ='#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div:nth-child(2) > div:nth-child(3) > div > div.flow-structure-charts.flex-1 > div:nth-child(3) > div > div.full.chart-box > div:nth-child(1) > canvas'
    time_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div:nth-child(2) > div:nth-child(3) > div > div.flow-structure-charts.flex-1 > div:nth-child(3) > div > div.full.chart-box > div:nth-child(2) > div.cfff.fs12.mb4'
    data_selectors =['#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div:nth-child(2) > div:nth-child(3) > div > div.flow-structure-charts.flex-1 > div:nth-child(3) > div > div.full.chart-box > div:nth-child(2) > div:nth-child(2) > div > span:nth-child(3)',
                     '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div:nth-child(2) > div:nth-child(3) > div > div.flow-structure-charts.flex-1 > div:nth-child(3) > div > div.full.chart-box > div:nth-child(2) > div:nth-child(3) > div > span:nth-child(3)']
    data_names =['当前达人','同带货水平达人均值']
    data = asyncio.run(gr(po_nums, canvas_selector, time_selector, data_selectors, data_names))
    print('直播流量结构完成')
    return data

# print(live_stream_traffic(10))

# 流量结构趋势
def live_composition_trend(po_nums):
    canvas_selector ='#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div:nth-child(2) > div:nth-child(3) > div > div.structure-trend-charts.flex-1 > div:nth-child(2) > div > div.full.chart-box > div:nth-child(1) > canvas'
    time_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div:nth-child(2) > div:nth-child(3) > div > div.structure-trend-charts.flex-1 > div:nth-child(2) > div > div.full.chart-box > div:nth-child(2) > div.mb4.fs12.cfff'

    data_selectors=['#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div:nth-child(2) > div:nth-child(3) > div > div.structure-trend-charts.flex-1 > div:nth-child(2) > div > div.full.chart-box > div:nth-child(2) > div:nth-child(2) > span:nth-child(3)',
                    '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div:nth-child(2) > div:nth-child(3) > div > div.structure-trend-charts.flex-1 > div:nth-child(2) > div > div.full.chart-box > div:nth-child(2) > div:nth-child(3) > span:nth-child(3)',
                    '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div:nth-child(2) > div:nth-child(3) > div > div.structure-trend-charts.flex-1 > div:nth-child(2) > div > div.full.chart-box > div:nth-child(2) > div:nth-child(4) > span:nth-child(3)',
                    '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div:nth-child(2) > div:nth-child(3) > div > div.structure-trend-charts.flex-1 > div:nth-child(2) > div > div.full.chart-box > div:nth-child(2) > div:nth-child(5) > span:nth-child(3)',
                    '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div:nth-child(2) > div:nth-child(3) > div > div.structure-trend-charts.flex-1 > div:nth-child(2) > div > div.full.chart-box > div:nth-child(2) > div:nth-child(6) > span:nth-child(3)'
                    ]
    data_names = ['短视频引流','关注','推荐','付费（预估）','其他']
    data = asyncio.run(gr(po_nums, canvas_selector, time_selector, data_selectors, data_names))
    print('流量结构趋势完成')
    return data
# print(live_composition_trend(100))

# 直播穿透率
def live_broadcast_rate(po_nums):
    time.sleep(1)
    canvas_selector = '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[4]/div[1]/div[1]/div[2]/div/div[1]/div[1]/canvas'
    time_selector = '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[4]/div[1]/div[1]/div[2]/div/div[1]/div[2]/div/text()[1]'

    data_selectors = ['//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[4]/div[1]/div[1]/div[2]/div/div[1]/div[2]/div/span[2]',
                      '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[4]/div[1]/div[1]/div[2]/div/div[1]/div[2]/div/span[6]'
                      ]
    data_names =['直播曝光量','穿透率']
    data = asyncio.run(gr_xp(po_nums, canvas_selector, time_selector, data_selectors, data_names))
    print('直播穿透率完成')
    return data
#print(live_broadcast_rate(40))

# 成交转化率
def live_transaction_conversion_rate(po_nums):
    canvas_selector = '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[4]/div[1]/div[2]/div[2]/div/div[1]/div[1]/canvas'
    time_selector = '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[4]/div[1]/div[2]/div[2]/div/div[1]/div[2]/div/text()[1]'

    data_selectors = [
        '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[4]/div[1]/div[2]/div[2]/div/div[1]/div[2]/div/span[2]',
        '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[4]/div[1]/div[2]/div[2]/div/div[1]/div[2]/div/span[6]'
        ]
    data_names = ['直播曝光量', '转化率']
    data = asyncio.run(gr_xp(po_nums, canvas_selector, time_selector, data_selectors, data_names))
    print('成交转化率完成')
    return data
#print(live_transaction_conversion_rate(30))

# 直播时间分布
def live_time_distubution(po_nums):
    canvas_selector ='#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div:nth-child(2) > div.pt50.pb30.half-chart-box > div:nth-child(3) > div.take-goods-trends.flex-1 > div:nth-child(2) > div > div.full.chart-box > div:nth-child(1) > canvas'
    time_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div:nth-child(2) > div.pt50.pb30.half-chart-box > div:nth-child(3) > div.take-goods-trends.flex-1 > div:nth-child(2) > div > div.full.chart-box > div:nth-child(2) > div > span:nth-child(2)'

    data_selectors = [
        '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div:nth-child(2) > div.pt50.pb30.half-chart-box > div:nth-child(3) > div.take-goods-trends.flex-1 > div:nth-child(2) > div > div.full.chart-box > div:nth-child(2) > div > span:nth-child(3)'
    ]
    data_names = ['次数']
    data = asyncio.run(up_to_down(po_nums, canvas_selector, time_selector, data_selectors, data_names))
    print('直播时间分布完成')
    return data
#print(live_time_distubution(20))

# 平均停留时长趋势
def live_average_stay_trends(po_nums):
    canvas_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div:nth-child(2) > div.pt50.pb30.half-chart-box > div.flex.align-items-center.pt30 > div.take-goods-trends.flex-1 > div:nth-child(2) > div > div.full.chart-box > div:nth-child(1) > canvas'
    time_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div:nth-child(2) > div.pt50.pb30.half-chart-box > div.flex.align-items-center.pt30 > div.take-goods-trends.flex-1 > div:nth-child(2) > div > div.full.chart-box > div:nth-child(2) > span'

    data_selectors = [
        '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div:nth-child(2) > div.pt50.pb30.half-chart-box > div.flex.align-items-center.pt30 > div.take-goods-trends.flex-1 > div:nth-child(2) > div > div.full.chart-box > div:nth-child(2) > div > span:nth-child(3)']
    data_names = ['平均停留时长']
    data = asyncio.run(gr(po_nums, canvas_selector, time_selector, data_selectors, data_names))
    print('平均停留时长趋势完成')
    return data
# print(average_live_stay_trends(20))

# 产出趋势
def live_output_trends(po_nums):
    result ={}
    canvas_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div:nth-child(2) > div.pt50.pb30.half-chart-box > div.flex.align-items-center.pt30 > div.product-trend.flex-1 > div:nth-child(2) > div > div.full.chart-box > div:nth-child(1) > canvas'
    button_labels = ['UV价值','千次观看成交','分钟带货产出']
    data_names = button_labels
    data_selectors =['#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div:nth-child(2) > div.pt50.pb30.half-chart-box > div.flex.align-items-center.pt30 > div.product-trend.flex-1 > div:nth-child(2) > div > div.full.chart-box > div:nth-child(2) > div.mt5.cfff.font-weight-400.fs12 > span:nth-child(3)']
    for label in button_labels:
        if label == 'UV价值':
            time_selector ='#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div:nth-child(2) > div.pt50.pb30.half-chart-box > div.flex.align-items-center.pt30 > div.product-trend.flex-1 > div:nth-child(2) > div > div.full.chart-box > div:nth-child(2) > span'
        else:
            time_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div:nth-child(2) > div.pt50.pb30.half-chart-box > div.flex.align-items-center.pt30 > div.product-trend.flex-1 > div:nth-child(2) > div > div.full.chart-box > div:nth-child(2) > div.cfff.font-weight-500.fs12'
        asyncio.run(mouse(label))
        time.sleep(1)
        data = asyncio.run(gr(po_nums, canvas_selector, time_selector, data_selectors, data_names))

        print(f'完成了{label}的图')
        result[label+'图'] = data
    return result
# print(live_output_trends(10))

# 直播开播时间统计
def live_time_count(po_nums):
    result = {}
    canvas_selector = '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[4]/div[3]/div[2]/div[2]/div/div[1]/div[1]/canvas'
    time_selector = '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[4]/div[3]/div[2]/div[2]/div/div[1]/div[2]/div/text()[1]'
    button_labels = ['按小时', '按星期']
    data_names = ['直播次数','直播次数']
    data_selectors = [
        '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[4]/div[3]/div[2]/div[2]/div/div[1]/div[2]/div/text()[2]']
    for label in button_labels:
        asyncio.run(mouse(label))
        time.sleep(2)
        data = asyncio.run(gr_xp(po_nums, canvas_selector, time_selector, data_selectors, data_names))

        print(f'完成了{label}的图')
        result[label + '图'] = data
    return result
#print(live_time_count(30))

""" 视频分析 """

# 视频分析-指标趋势分析
def video_Metric_trends(po_nums):
    result = {}
    canvas_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.target-chart-wrapper.relative > div > div.full.chart-box > div:nth-child(1) > canvas'
    time_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.target-chart-wrapper.relative > div > div.full.chart-box > div:nth-child(2) > div.cfff.font-weight-500.fs12'
    data_selectors = [
        '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.target-chart-wrapper.relative > div > div.full.chart-box > div:nth-child(2) > div.mt5.cfff.font-weight-400.fs12 > span:nth-child(3)']
    left_label = ['点赞', '评论', '转发']
    right_label = ['增量', '总量']
    for l_label in left_label:
        asyncio.run(mouse(l_label))
        for r_label in right_label:
            asyncio.run(mouse(r_label))
            data_names = [l_label]
            data = asyncio.run(gr(po_nums, canvas_selector, time_selector, data_selectors, data_names))
            key_name = l_label + '_' + r_label
            result[key_name] = data
            print(f'完成了 {l_label} - {r_label} 的图')

    return result
# video_Metric_trends(10)

# 视频发布时间统计
def video_post_time(po_nums):
    result = {}
    canvas_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(8) > div:nth-child(2) > div.chart-wrapper.relative > div > div.full.chart-box > div:nth-child(1) > canvas'
    time_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(8) > div:nth-child(2) > div.chart-wrapper.relative > div > div.full.chart-box > div:nth-child(2) > div.cfff.font-weight-500.fs12'
    data_selectors = [
        '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(8) > div:nth-child(2) > div.chart-wrapper.relative > div > div.full.chart-box > div:nth-child(2) > div.cfff.font-weight-400.fs12 > span:nth-child(3)']
    labels = ['按小时', '按星期']
    for label in labels:
        asyncio.run(mouse(label))
        if label == '按小时':
            data_names = ['小时']
        else:
            data_names = ['天']
        data = asyncio.run(gr(po_nums, canvas_selector, time_selector, data_selectors, data_names))
        result[label] = data
        print(f'完成了{label}的图')

    return result
# print(video_post_time(20))

# 视频时长分布
def video_duration_distribution(po_nums):
    canvas_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(8) > div:nth-child(1) > div.chart-wrapper.relative > div > div.full.chart-box > div:nth-child(1) > canvas'
    time_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(8) > div:nth-child(1) > div.chart-wrapper.relative > div > div.full.chart-box > div:nth-child(2) > div > span:nth-child(2)'
    data_selectors = [
        '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(8) > div:nth-child(1) > div.chart-wrapper.relative > div > div.full.chart-box > div:nth-child(2) > div > span:nth-child(3)']
    data_names = ['次数']
    data = asyncio.run(up_to_down(po_nums, canvas_selector, time_selector, data_selectors, data_names))
    print('视频时长分布抓取完成')
    return data
# print(video_duration_distribution(10))



"""基础数据"""
def live(driver,url,data_dict):
    url = url+'/live'
    driver.get(url)
    time.sleep(2)
    wait = WebDriverWait(driver, 1)
    try:
        element = driver.find_element(By.CSS_SELECTOR, '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div.table-empty-box.pt20.pb20')  # 替换为您的CSS选择器
    except:
        element = driver.find_element(By.CSS_SELECTOR,
                                      ' #app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(2) > div:nth-child(2) > div.pb30.border-b-f5.pl20.pr20 > div')
    # 获取元素的类名
    element_classes = element.get_attribute('class')

    # 检查类名是否包含 'table-empty-box'
    if 'table-empty-box' in element_classes:
        print("元素包含 class='table-empty-box'，跳过获取其他值的操作")
        # 如果存在空的表格框，则将所有值设置为0
        data_dict['直播场次'] = 0
        data_dict['带货场次'] = 0
        data_dict['场均观看'] = 0
        data_dict['日均观看'] = 0
        data_dict['累计观看人次'] = 0
        data_dict['上架商品'] = 0
        data_dict['带货转化率'] = '0.00%'
        data_dict['场均销量'] = 0
        data_dict['日均销量'] = 0
        data_dict['总销量'] = 0
        data_dict['场均销售额'] = 0
        data_dict['日均销售额'] = 0
        data_dict['总销售额'] = 0
        data_dict['场均UV价值'] = 0
        data_dict['日均UV价值'] = 0
    else:
        # 如果不存在空的表格框，则继续执行获取值的代码
        # 获取直播场次
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div[1]/div[2]/div',
                   '直播场次', data_dict)
        # 如果直播场次不为0，则获取其他值
        # 带货场次
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div[1]/div[3]/div/span',
                   '带货场次', data_dict)

        # 场均观看
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div[2]/div[2]/div/span',
                   '场均观看', data_dict)

        # 带货场次
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div[1]/div[3]/div/span',
                   '带货场次', data_dict)

        # 场均观看
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div[2]/div[2]/div/span',
                   '场均观看', data_dict)

        # 日均观看
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div[2]/div[3]/span',
                   '日均观看', data_dict)

        # 累计观看人次
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div[2]/div[4]/span',
                   '累计观看人次', data_dict)

        # 上架商品
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div[3]/div[2]/div',
                   '上架商品', data_dict)

        # 带货转化率
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div[4]/div[2]/div',
                   '带货转化率', data_dict)

        # 场均销量
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div[5]/div[2]',
                   '场均销量', data_dict)

        # 日均销量
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div[5]/div[3]/span',
                   '日均销量', data_dict)

        # 总销量
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div[5]/div[4]/span',
                   '总销量', data_dict)

        # 场均销售额
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div[6]/div[3]/span',
                   '场均销售额', data_dict)

        # 日均销售额
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div[6]/div[3]/span',
                   '日均销售额', data_dict)

        # 总销售额
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div[6]/div[4]/span[2]',
                   '总销售额', data_dict)

        # 场均UV价值
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div[7]/div[2]/div',
                   '场均UV价值', data_dict)

        # 客单价
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div[7]/div[3]/div/span',
                   '客单价', data_dict)

        # 日均UV价值
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div[7]/div[3]/span[2]',
                   '日均UV价值', data_dict)

def live_page(po_nums):
    result = {}
    asyncio.run(custom_scroll(300))
    data = live_trends(po_nums)
    for key in data.keys():
        result['直播趋势分析_' + key] = data[key]
    # 调用live_trends函数
    result['直播趋势分析'] = live_trends(po_nums)
    asyncio.run(custom_scroll(300))
    time.sleep(1)
    result['直播流量结构'] = live_stream_traffic(po_nums)
    result['流量结构趋势'] = live_composition_trend(po_nums)
    asyncio.run(custom_scroll(500))
    result['直播穿透率'] = live_broadcast_rate(po_nums)
    result['成交转化率'] = live_transaction_conversion_rate(po_nums)

    asyncio.run(custom_scroll(200))
    result['平均停留时长趋势'] = live_average_stay_trends(po_nums)
    data_live_output = live_output_trends(po_nums)
    for key in data_live_output:
        result['产出趋势_' + key] = data_live_output[key]
    asyncio.run(custom_scroll(400))

    result['直播时长分布'] = live_time_distubution(po_nums)
    data_live_time_count = live_time_count(po_nums)
    for key in data_live_time_count:
        result['直播开播时间统计_' + key] = data_live_time_count[key]
    return result

def video(driver,url,data_dict):
    driver.get(url+'/aweme')
    # click_radio_button_by_value(driver,'//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[1]/div[2]/div[1]/div/label[6]/span')
    # time.sleep(1)
    wait = WebDriverWait(driver, 1)

    fetch_data(wait, '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[3]/div[1]/div/span', '所有视频数', data_dict)
    fetch_data(wait, '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[3]/div[2]/div/span', '带货视频', data_dict)
    fetch_data(wait, '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[3]/div[3]/div[1]/span', '平均点赞数', data_dict)
    fetch_data(wait, '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[3]/div[3]/div[2]', '点赞数中位值', data_dict)
    fetch_data(wait, '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[3]/div[4]/div[1]/span', '平均评论数', data_dict)
    fetch_data(wait, '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[3]/div[4]/div[2]', '评论数中位值', data_dict)
    fetch_data(wait, '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[3]/div[5]/div[1]/span', '平均转发数', data_dict)
    fetch_data(wait, '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[3]/div[5]/div[2]', '转发数中位值', data_dict)
    fetch_data(wait, '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[3]/div[6]/div[1]/span', '平均收藏数', data_dict)
    fetch_data(wait, '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[3]/div[6]/div[2]', '收藏数中位值', data_dict)
    fetch_data(wait, '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[3]/div[7]/div[1]/span', '平均销售额', data_dict)
    fetch_data(wait, '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[3]/div[7]/div[2]', '总销售额', data_dict)
    fetch_data(wait, '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[3]/div[8]/div[1]/span', '平均销量', data_dict)
    fetch_data(wait, '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[3]/div[8]/div[2]', '总销量', data_dict)
    fetch_data(wait, '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[3]/div[9]/div/span', 'IPM', data_dict)
    fetch_data(wait, '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[3]/div[10]/div/span', 'GPM', data_dict)

def video_page(po_nums):
    result = {}
    data = video_Metric_trends(po_nums)
    for key in data.keys():
        result['视频分析-指标趋势分析' + key] = data[key]
    asyncio.run(custom_scroll(400))
    data = video_post_time(po_nums)
    for key in data.keys():
        result['视频发布时间统计' + key] = data[key]
    result['视频时长分布'] = video_duration_distribution(po_nums)
    return result

def sale(driver,url,data_dict):
    url = url + '/promotion'
    driver.get(url)
    # click_radio_button_by_value(driver,
    #                             '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[1]/div[2]/div[1]/div/label[6]/span')
    # time.sleep(2)
    wait = WebDriverWait(driver, 1)
    try:
        element = driver.find_element(By.CSS_SELECTOR,
                                      '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.section-empty.text-align-center.pt40.pb40')  # 替换为您的CSS选择器
    except:
        element = driver.find_element(By.CSS_SELECTOR,
                                      '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div.overview-wrapper.flex.flex-flow-row-wrap.pt30.pl20.pr20')
    # 获取元素的类名
    element_classes = element.get_attribute('class')
    print(element_classes)
    if 'empty' in element_classes:
        data_dict['商品数量'] = 0
        data_dict['主要领域'] = 0
        data_dict['直播带货数量'] = 0
        data_dict['带货直播场次'] = 0
        data_dict['视频带货数量'] = 0
        data_dict['带货视频数'] = 0
        data_dict['带货品类'] = 0
        data_dict['美妆护肤占比'] = 0
        data_dict['带货品牌'] = 0
        data_dict['PMPM（每场直播带货商品数）'] = 0
    else:
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[3]/div[1]/div[1]/span',
                   '商品数量', data_dict)
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[3]/div[1]/div[2]',
                   '主要领域', data_dict)
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[3]/div[2]/div[1]/span',
                   '直播带货数量', data_dict)
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[3]/div[2]/div[2]',
                   '带货直播场次', data_dict)
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[3]/div[3]/div[1]/span',
                   '视频带货数量', data_dict)
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[3]/div[3]/div[2]',
                   '带货视频数', data_dict)
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[3]/div[4]/div[1]/span',
                   '带货品类', data_dict)
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[3]/div[4]/div[2]',
                   '最高占比', data_dict)
        fetch_data(wait,
                   '<span data-v-52dd07a9="" data-v-53d890c6="" class="fs22 c333 font-weight-400 cds-font lh100p"> 787 </span>',
                   '带货品牌', data_dict)
        fetch_data(wait,
                   '//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div/div/div[3]/div[5]/div[2]',
                   'PMPM（每场直播带货商品数）', data_dict)

        # 关闭WebDriver

def sales_page(po_nums):
    result = {}
    result['直播带货'] = live_sales(po_nums)
    result['视频带货'] = video_sales_trends(po_nums)
    asyncio.run(custom_scroll(800))
    result['近30天直播爆品-销量'] = live_top30_sales(po_nums)
    return result

def fans_page(po_nums):
    fans_total={}
    fans_total['粉丝趋势'] = fans_trends(po_nums)
    fans_total['粉丝团趋势'] = fans_group_trend(po_nums)
    asyncio.run(mouse('视频观众'))
    time.sleep(1)
    fans_total['粉丝年龄分布'] = fans_age_distribution(po_nums)
    asyncio.run(mouse('直播观众'))
    time.sleep(1)
    fans_total['直播年龄分布']= fans_live_age_distribution(po_nums)
    return fans_total



def main(url,po_nums):
    data_dict = {}
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(executable_path='C:\\Program Files\\Google\\Chrome\\Application\\chromedriver.exe',
                              options=chrome_options)
    base_data(driver, url, data_dict)
    # print(data_dict)

    # 创建excel+基础数据
    data_dict['url'] = url
    name = data_dict['账号名称']
    excel_file = create_excel_file(name,'output_婵妈妈达人页')
    write_data_to_excel(data_dict, '基础分析', excel_file)

    # 直播分析
    data_dict = {}
    live(driver, url, data_dict)
    asyncio.run(custom_scroll(150))
    write_data_to_excel(data_dict, '直播分析', excel_file)
    data = live_page(po_nums)
    write_graph_to_excel(excel_file, data)

    # 视频分析
    data_dict = {}
    video(driver, url, data_dict)
    time.sleep(3)
    asyncio.run(custom_scroll(300))
    write_data_to_excel(data_dict, '视频分析', excel_file)
    data = video_page(po_nums)
    write_graph_to_excel(excel_file, data)

    # 带货分析
    data_dict = {}
    live(driver, url, data_dict)
    asyncio.run(custom_scroll(300))
    write_data_to_excel(data_dict, '带货分析', excel_file)
    data = video_page(po_nums)
    write_graph_to_excel(excel_file, data)

    # 粉丝分析
    driver.get(url + '/fans')
    data = fans_page(po_nums)
    # print(data)
    write_graph_to_excel(excel_file, data)

    # print(excel_file)

if __name__ == '__main__':
    excel_file = '达人页.xlsx'
    df = pd.read_excel(excel_file)
    # 获取URL列的数据
    urls = df['url']
    choice = input('请输入你想要调整的参数，或者输入N:')
    if choice == 'N':
        for url in urls:
            print(f'正在运行爬取{url}')
            main(url,10)
            break
    else:
        choice = int(choice)
        for url in urls:
            print(f'正在运行爬取{url}')
            main(url, choice)




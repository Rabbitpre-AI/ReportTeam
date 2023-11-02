import asyncio
import time
import pandas as pd
import os
from pyppeteer import connect
from datetime import datetime
import random
async def custom_scroll(num):
    browser = await connect(browserURL='http://127.0.0.1:9222', defaultViewport={'width': 1280, 'height': 720})
    pages = await browser.pages()
    page = pages[0]
    await page.evaluate(f'window.scrollBy(0, {num})')  # 向下滚动100像素
# 横向CSS版
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
                        print(f"Element with selector {selector} not found!")
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
                    print(f"Element with time selector {time_selector} not found!")
            except Exception as e:
                pass
                # print(f"Error for time selector {time_selector}: {e}")

        await browser.disconnect()
        return sorted(data_dict.items(), key=lambda x: x[0])
    except Exception as e:
        print(f"处理图为'{canvas_selector}'的元素时出错: {e}")
        return None

# 横向XPATH版
async def gr_xp(num_data_points, canvas_selector, time_selector, data_selectors, data_names):
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
        await page.waitForXPath(canvas_selector, {"visible": True, "timeout": 1000})

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

if __name__ == "__main__":


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
        return data
    # print(live__distribution(50))

    def fans_page(po_nums):
        fans_total={}
        fans_total['粉丝趋势'] = fans_trends(po_nums)
        fans_total['粉丝团趋势'] = fans_group_trend(po_nums)
        asyncio.run(mouse('视频观众'))
        time.sleep(1)
        fans_total['粉丝年龄分布'] = fans_age_distribution(po_nums)
        asyncio.run(mouse('直播观众'))
        time.sleep(1)
        fans_total['直播年龄分布']= fans_age_distribution(po_nums)
        return fans_total

    #data = fans_page(30)
    #print(data)

    def write_data_to_excel(data, task_name):
        # 获取当前日期并格式化为年月日
        current_date = datetime.now().strftime('%Y-%m-%d')
        # 生成一个随机数（范围可以根据需求调整）
        random_number = random.randint(1, 1000)
        excel_file = f'{current_date}_{task_name}_{random_number}.xlsx'

        if not os.path.isfile(excel_file):
            # 如果文件不存在，创建一个新的Excel文件
            with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
                writer.save()

        with pd.ExcelWriter(excel_file, engine='openpyxl', mode='a') as writer:
            for sheet_name, sheet_data in data.items():
                if sheet_data is None:
                    print(f"跳过图表 '{sheet_name}'，因为数据为 None")
                    continue

                df = pd.DataFrame.from_dict(sheet_data, orient='index')
                if sheet_name in writer.book.sheetnames:
                    # 获取现有工作表的引用
                    worksheet = writer.sheets[sheet_name]
                    # 将新数据追加到工作表的最后一行后面
                    df.to_excel(writer, sheet_name=sheet_name, startrow=worksheet.max_row + 1, header=False)
                else:
                    # 创建新工作表并写入数据
                    df.to_excel(writer, sheet_name=sheet_name, startrow=1, header=False)

                # 将时间作为第一列写入
                worksheet = writer.sheets[sheet_name]
                worksheet.cell(row=1, column=1, value='时间')
                # 将数据的键（表头）写入第一行
                for col_num, key in enumerate(df.columns, 2):
                    worksheet.cell(row=1, column=col_num, value=key)

        print(f'Data has been written to {excel_file}')

    #write_data_to_excel(data,'fans_page_test')
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

    def sales_page(po_nums):
        result = {}
        result['直播带货'] = live_sales(po_nums)
        result['视频带货'] = video_sales_trends(po_nums)
        asyncio.run(custom_scroll(800))
        result['近30天直播爆品-销量'] = live_top30_sales(po_nums)
        return result

asyncio.run(custom_scroll(300))
print(sales_page(10))

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
            data_names =[l_label]
            data = asyncio.run(gr(po_nums, canvas_selector, time_selector, data_selectors, data_names))
            key_name = l_label + '_' + r_label
            result[key_name] = data
            print(f'完成了 {l_label} - {r_label} 的图')


    return result
# video_Metric_trends(10)

# 视频发布时间统计
def video_post_time(po_nums):
    result = {}
    canvas_selector ='#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(8) > div:nth-child(2) > div.chart-wrapper.relative > div > div.full.chart-box > div:nth-child(1) > canvas'
    time_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(8) > div:nth-child(2) > div.chart-wrapper.relative > div > div.full.chart-box > div:nth-child(2) > div.cfff.font-weight-500.fs12'
    data_selectors =['#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(8) > div:nth-child(2) > div.chart-wrapper.relative > div > div.full.chart-box > div:nth-child(2) > div.cfff.font-weight-400.fs12 > span:nth-child(3)']
    labels = ['按小时','按星期']
    for label in labels:
        asyncio.run(mouse(label))
        if label =='按小时':
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
    canvas_selector ='#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(8) > div:nth-child(1) > div.chart-wrapper.relative > div > div.full.chart-box > div:nth-child(1) > canvas'
    time_selector = '#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(8) > div:nth-child(1) > div.chart-wrapper.relative > div > div.full.chart-box > div:nth-child(2) > div > span:nth-child(2)'
    data_selectors =['#app > div.author-detail-page > div.author-detail-content > div.author-details-wrapper.flex.justify-content-space-between > div.details-right > div > div > div:nth-child(8) > div:nth-child(1) > div.chart-wrapper.relative > div > div.full.chart-box > div:nth-child(2) > div > span:nth-child(3)']
    data_names = ['次数']
    data = asyncio.run(up_to_down(po_nums, canvas_selector, time_selector, data_selectors, data_names))
    print('视频时长分布抓取完成')
    return data
# print(video_duration_distribution(10))

def video_page(po_nums):
    result = {}
    data = video_Metric_trends(po_nums)
    for key in data.keys():
        result['视频分析-指标趋势分析'+key] = data[key]
    asyncio.run(custom_scroll(400))
    data = video_post_time(po_nums)
    for key in data.keys():
        result['视频发布时间统计' + key] = data[key]
    result['视频时长分布'] = video_duration_distribution(po_nums)
    return result


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
            time.sleep(4)
            data = asyncio.run(gr_xp(po_nums, canvas_selector, time_selector, data_selectors, data_names))

            print(f'完成了{label}的图')
            result[label + '图'] = data
        return result
    #print(live_time_count(30))

    def live_page(po_nums):
        result = {}
        data = live_trends(po_nums)
        for key in data.keys():
            result['直播趋势分析_'+key] = data[key]
        # 调用live_trends函数
        result['直播趋势分析'] = live_trends(po_nums)
        asyncio.run(custom_scroll(250))
        result['直播流量结构'] = live_stream_traffic(po_nums)
        result['流量结构趋势'] = live_composition_trend(po_nums)
        asyncio.run(custom_scroll(200))
        result['直播穿透率'] = live_broadcast_rate(po_nums)
        result['成交转化率'] = live_transaction_conversion_rate(po_nums)
        asyncio.run(custom_scroll(200))
        result['直播时间分布'] = live_time_distubution(po_nums)
        asyncio.run(custom_scroll(200))
        result['平均停留时长趋势'] = live_average_stay_trends(po_nums)
        asyncio.run(custom_scroll(200))
        data_live_output = live_output_trends(po_nums)
        for key in data_live_output:
            result['产出趋势_'+key] = data_live_output[key]
        asyncio.run(custom_scroll(200))
        data_live_time_count= live_time_count(po_nums)
        for key in data_live_time_count:
            result['直播开播时间统计_'+ key] =data_live_time_count[key]
        return result


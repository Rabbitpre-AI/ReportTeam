import asyncio
import time

from pyppeteer import connect
import os
import xinkuai_blogger
import pandas as pd
from datetime import datetime
import random
from xinkuai_blogger_detail import Blogger_detail


class ChoosePage:

    def __init__(self, page, base_url):
        self.page = page
        self.base_url = base_url
        self.current_page_name = ''
        # 设置您想要创建的目录的名称
        self.folder_name = '新快-output'
        self.random_num = random.randint(0, 1000)
        # 当前文件的绝对路径
        self.current_directory = os.getcwd()
        self.current_date = datetime.now().strftime('%Y%m%d')
        self.blogger_table_excel_path = None
        self.blogger_detail_plate = ['overview', 'worksAnalysis', 'fanPortrait', 'liveAnalysis', 'categoryPromotion']
        self.links_dict = {
            '首页': '/',
            '快手号搜索': '/account/search',
            'MCN机构搜索': '/account/mcnSearch',
            '地域找号': '/account/regionalSearch',
            '指数排行榜': '/account/rank',
            '单项指标排行': '/account/singleRank',
            '视频搜索': '/material/videoSearch',
            '爆款速递': '/material/videoExpress',
            '标签搜索': '/material/label',
            '音乐BGM': '/material/music',
            '快手热榜': '/material/hot',
            '红人看板': '/broadcast/live',
            '主播带货排行': '/broadcast/liveExpertRank',
            '热门直播间': '/broadcast/liveSearch',
            '直播商品': '/broadcast/liveGoods',
            '直播流量大盘': '/broadcast/dashboard',
            '小店搜索': '/kwaiStore/storeSearch',
            '小店排行榜': '/kwaiStore/storeRank',
            '品牌搜索': '/brand/search',
            '品牌排行榜': '/brand/rank',
            '品类搜索': '/category/search',
            '品类排行榜': '/category/rank',
            '品类营销大盘': '/category/market',
        }

    async def get_current_page(self):
        current_url = self.page.url
        for name, path in self.links_dict.items():
            full_path = self.base_url.rstrip('/') + '/' + path.lstrip('/')
            if current_url == full_path:
                self.current_page_name = name
                return name
        return "未知页面"

    # 单个sheet的数据保存
    async def save_data_one_sheet(self, folder_name, excel_name, df):
        folder_path = os.path.join(self.current_directory, folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        excel_path = os.path.join(folder_path, f'output_快手{excel_name}{self.current_date}-{self.random_num}.xlsx')
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer)
        print(f'数据保存在{excel_path}')

        self.blogger_table_excel_path = excel_path
        print(self.blogger_table_excel_path)
    # 多个sheet的数据保存
    async def save_data_multi_sheet(self, folder_name, excel_name, final_data):
        folder_path = os.path.join(self.current_directory, folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        excel_path = os.path.join(folder_path, f'output_快手{excel_name}{self.current_date}-{self.random_num}.xlsx')
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            for sheet_name, df in final_data.items():
                df.to_excel(writer, sheet_name=sheet_name)
        print(f'数据保存在{excel_path}')

    async def execute_home_logic(self):
        while True:
            print("已访问首页")
            break

    # 快手号搜索
    async def execute_kuaishou_search_logic(self):
        print("已访问当前网页")
        while True:
            folder_name = '快手号搜索'
            print('请确定所需要执行功能，请注意，如没有列表账号excel，无法获取相应的达人账号，或改为手动操控指定页面')
            choose = input('1.快手号列表数据爬取，2.相关的快手账号信息爬取，或0返回上一页，请输入选项：')
            if choose == '1':
                print("执行快手号列表数据爬取操作")
                table_df = await xinkuai_blogger.kuaishou_blogger(self.page)
                if table_df is not None:
                    excel_name = '列表数据'
                    await self.save_data_one_sheet(folder_name, excel_name, table_df)
                else:
                    print('并没有爬取数据')

            elif choose == '2':
                print("执行相关的快手账号信息爬取操作")
                print('''快手号细节总共有五项，你可以根据实际情况选择你所要的数据，
                    1.账号概览
                    2.作品分析
                    3.粉丝画像
                    4.直播分析
                    5.品类商品
                    ''')
                user_input = input('请选择你所需要的数据（输入逻辑例如：135，则默认为1，3，5项），或回车默认全部：')

                if user_input == '':
                    selected_plate = self.blogger_detail_plate  # 默认全部
                else:
                    selected_indices = [int(index) - 1 for index in user_input.split(',') if index.isdigit()]
                    selected_plate = [self.blogger_detail_plate[i] for i in selected_indices]

                print('你选择的数据项是：', selected_plate)

                if self.blogger_table_excel_path is None:
                    print('当前并没有列表数据，请确认是否是要单独执行单个达人页数据,使用只需点开你所要的达人页，无需关闭第一个，请此时只保留2个页面，任务结束会自动关闭页面')
                    print('如果想执行已有的excel，复制相应链接即可')
                    choose1 = input('如果是，选择单个请扣1，引用列表请扣2：')
                    if choose1 == '1':
                        browser = await connect(browserURL='http://127.0.0.1:9222', defaultViewport=None)
                        pages = await browser.pages()
                        if len(pages) < 2:
                            print('当前页面数量不足，请确保至少有两个页面打开')
                        else:
                            page = pages[1]  # 获取第二个页面
                            blogger = Blogger_detail(page)
                            final_data = await blogger.get_account_info(selected_plate=selected_plate)
                            excel_name = str(final_data['个人信息']['名字'].iloc[0])
                            await self.save_data_multi_sheet(folder_name, excel_name, final_data)
                            await page.close()

                    elif choose1 == '2':
                        excel_path = input('请输入Excel文件路径：')
                        excel_path = excel_path.replace("\\", "\\\\")  # 将单斜杠替换为双斜杠
                        self.blogger_table_excel_path = excel_path

                else:

                    df = pd.read_excel(self.blogger_table_excel_path)
                    start = 0
                    end = len(df)
                    names = df['快手名字']
                    row_keys = df['row_key']
                    # 获取数据框中的行数
                    total_rows = len(df)

                    # 提示用户选择操作
                    print("已读取列表内容,请选择操作：")
                    print("1. 默认全部跑完")
                    print("2. 修改开始和结束的点")
                    print('3.如想更换列表，请使用此功能清空原有程序的路径')

                    # 获取用户选择
                    choice = input("请选择操作（1/2/3）：")

                    if choice == '1':
                        start = 0
                        end = total_rows
                    elif choice == '2':
                        # 提示用户输入开始和结束的点
                        start = int(input("请输入开始点（0 到 {}）：".format(total_rows)))
                        end = int(input("请输入结束点（{} 到 {}）：".format(start, total_rows)))
                        # 确保输入的范围合法
                        start = max(0, start)
                        end = min(end, total_rows)
                    elif choice == '3':
                        self.blogger_table_excel_path = None
                        print("已清空列表文件路径，您可以在之后重新设置。")
                        continue
                    else:
                        print("无效的选择，请重新运行程序并选择有效操作。")
                        continue

                    for i in range(start, end):
                        url = 'https://xk.newrank.cn/d/account/overview/' + str(row_keys[i])
                        browser = await connect(browserURL='http://127.0.0.1:9222', defaultViewport=None)
                        pages = await browser.pages()
                        page = pages[0]
                        await page.goto(url)
                        blogger = Blogger_detail(page)
                        final_data = await blogger.get_account_info(selected_plate)
                        excel_name = names[i]
                        if final_data is not None:
                            await self.save_data_multi_sheet(folder_name, excel_name, final_data)

            elif choose == '0':
                print("返回上一页操作")
                break
            else:
                print("无效的选择，请重新输入。")

    async def run(self):

        page_functions = {
            '首页': self.execute_home_logic,
            '快手号搜索': self.execute_kuaishou_search_logic,
            # 添加其他页面的功能函数
        }

        while True:
            current_page = await self.get_current_page()
            print(f"当前页面: {current_page}")
            print("可选路径：")
            for index, key in enumerate(self.links_dict.keys(), start=1):
                print(f"{index}: {key}")
            print("99: 直接使用当前页面功能")

            choice_input = input("请输入您的选择 (0 退出)：")

            if choice_input == '0':
                print("您选择退出。")
                break
            elif choice_input == '99':
                current_page = await self.get_current_page()
                # 查询当前页面并调用相应功能
                if current_page in page_functions:
                    await page_functions[current_page]()
                else:
                    print("当前页面还未开发功能。\n")
            elif choice_input.isdigit():
                choice = int(choice_input)
                if 1 <= choice <= len(self.links_dict):
                    selected_key = list(self.links_dict.keys())[choice - 1]
                    selected_path = list(self.links_dict.values())[choice - 1]
                    print(f"对应板块是：{selected_key}")
                    response = await self.page.goto(self.base_url + selected_path)
                    if response.status == 200:
                        print(f"已成功访问到 {selected_key} 页面")
                    else:
                        print(f"无法访问 {selected_key} 页面，请确认网络连接是否正常。")
                        user_confirmation = input("网络是否正常？ (Y/N)：").strip().lower()
                        if user_confirmation == 'n':
                            print("程序终止。")
                            break
                        elif user_confirmation == 'y':
                            print("请重新选择路径。")
                        else:
                            print("无效的输入，程序终止。")
                            break
                else:
                    print("无效的选择，请重新输入。")
            else:
                print("无效的选择，请重新输入。")


async def main():
    browser = await connect(browserURL='http://127.0.0.1:9222', defaultViewport=None)
    pages = await browser.pages()
    page = pages[0]
    base_url = 'https://xk.newrank.cn'
    chooser = ChoosePage(page,base_url)
    await chooser.run()


if __name__ == '__main__':
    asyncio.run(main())

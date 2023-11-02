import asyncio
from pyppeteer import connect

class ChoosePage:
    def __init__(self, page, base_url):
        self.page = page
        self.base_url = base_url  # Store the base URL as an instance variable
        self.current_page_name = ''
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

    async def navigate_to(self, path):
        full_url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"  # 正确地拼接 URL
        print(f"正在导航到: {full_url}")
        await self.page.goto(full_url)


    async def get_current_page(self):
        current_url = self.page.url
        for name, path in self.links_dict.items():
            full_path = self.base_url.rstrip('/') + '/' + path.lstrip('/')
            if current_url == full_path:
                self.current_page_name = name
                return name
        return "未知页面"

    async def run(self):
        current_page = await self.get_current_page()  # 假设这个方法返回当前页面的名称
        print(f"当前页面: {current_page}")
        print('\n请选择一个链接 或 输入"24"来查询当前页面所在位置， "0" 来结束程序!')
        print('\n')
        while True:
            for index, (text, path) in enumerate(self.links_dict.items(), start=1):
                print(f"{index}: {text}")

            choice_input = input("请输入你的选择的编号或 '0'退出 或 '24'查询当前所在页面：").strip()

            if choice_input.lower() == '0':
                print("退出程序。")
                return current_page  # 返回当前页面的名称并退出
            elif choice_input == '24':
                current_page = await self.get_current_page()
                print(f"当前页面: {current_page}")
            elif choice_input.isdigit():
                choice = int(choice_input) - 1
                if 0 <= choice < len(self.links_dict):
                    link_path = list(self.links_dict.values())[choice]
                    await self.navigate_to(self.base_url + link_path)
                    current_page = await self.get_current_page()  # 更新当前页面的名称
                    print(f'访问至{current_page}')
                else:
                    print("输入的编号不正确，请重新输入。")
            else:
                print("请输入有效的数字或 '退出'。")


# # 使用类的方法
# async def main():
#     browser = await connect(browserURL='http://127.0.0.1:9222', defaultViewport=None)
#     pages = await browser.pages()
#     page = pages[0]
#     base_url = 'https://xk.newrank.cn'
#
#     chooser = ChoosePage(page, base_url)
#     name = await chooser.run()  # 直接调用类的 run 方法
#     print(name)
#
# asyncio.run(main())

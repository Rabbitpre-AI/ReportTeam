import asyncio
import sys
import pandas as pd
from pyppeteer import connect

class TableDataScraper:
    def __init__(self, page, table_xpath, row_xpath):
        self.page = page
        self.table_xpath = table_xpath
        self.row_xpath = row_xpath
        self.data_row_keys = []
        self.all_data = []
        self.table_header = None

    async def get_data_row_key(self, row_element):
        data_row_key = await self.page.evaluate('(element) => element.getAttribute("data-row-key")', row_element)
        return data_row_key

    async def pull_down_until_end(self):
        pre_lst_len = 0
        timeout_seconds = 5  # 设置超时时间为5秒

        while True:
            elements = await self.page.xpath(self.table_xpath)
            table = elements[0] if elements else None

            if not table:
                print("未找到表格")
                break

            scroll_distance = sys.maxsize
            await self.page.evaluate('''(table, distance) => {
                table.scrollTop += distance;
            }''', table, scroll_distance)

            elapsed_time = 0

            while elapsed_time < timeout_seconds:
                await asyncio.sleep(1)
                elapsed_time += 1

                row_elements = await self.page.xpath(self.row_xpath)
                cur_lst_len = len(row_elements)

                if cur_lst_len > pre_lst_len:
                    break

            if elapsed_time >= timeout_seconds:
                print("5秒内未发现新数据，停止滚动。")
                break

            for row_element in row_elements[pre_lst_len:]:
                cell_data = await self.page.evaluate('''(row) => {
                    return Array.from(row.querySelectorAll("td")).map(cell => cell.innerText);
                }''', row_element)

                data_row_key = await self.get_data_row_key(row_element)
                if data_row_key:
                    self.data_row_keys.append(data_row_key)

                self.all_data.append(cell_data)

            pre_lst_len = cur_lst_len

            if self.table_header is None:
                self.table_header = await self.page.evaluate('''() => {
                    const ths = Array.from(document.querySelectorAll('table thead tr th'));
                    return ths.map(th => th.innerText.trim());
                }''')

        if self.all_data:
            df = pd.DataFrame(self.all_data, columns=self.table_header)
            return self.data_row_keys, df
        else:
            print("未收集到数据")
            return None, None

# 使用示例:
# 假设 'page' 是一个有效的 pyppeteer 页面对象
# scraper = TableDataScraper(page, table_xpath, row_xpath)
# data_row_keys, df = await scraper.pull_down_until_end()

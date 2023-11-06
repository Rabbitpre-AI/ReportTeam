import time

from 新快已完成代码.login_class import Login
import asyncio
from pyppeteer import errors
from xinkuai_choose_page import ChoosePage
async def xinkuai_main():
    try:
        # Here you should set the username and password for the login
        username = "18800011002"
        password = "6673xx"
        # Instantiate the Login class with the page, username, and password
        login = Login(username,password)
        await login.run()
        await asyncio.sleep(1)
        page = login.page
        baseurl = page.url
        print(baseurl)
        if baseurl == 'http://121.40.92.153:50888/':
            choose_xinkuai = ChoosePage(page,baseurl)
            await choose_xinkuai.run()
        else:
            print('暂时未开发')
    except errors.PyppeteerError as e:
        print(f"发生了一个Pyppeteer错误: {e}")
    except Exception as e:
        print(f"发生了一个未预期的错误: {e}")

# Run the main coroutine
asyncio.run(xinkuai_main())

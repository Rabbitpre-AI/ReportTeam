from login_class import Login
import asyncio
from pyppeteer import connect, errors
from xinkuai_choose_page import ChoosePage
async def xinkuai_main():
    try:
        # Here you should set the username and password for the login
        username = "18812346677"
        password = "4455aa"
        # Instantiate the Login class with the page, username, and password
        login = Login(username,password)
        await login.run()
        page = login.page
        baseurl = page.url
        choose = ChoosePage(page,baseurl)
        await choose.run()
    except errors.PyppeteerError as e:
        print(f"发生了一个Pyppeteer错误: {e}")
    except Exception as e:
        print(f"发生了一个未预期的错误: {e}")

# Run the main coroutine
asyncio.run(xinkuai_main())

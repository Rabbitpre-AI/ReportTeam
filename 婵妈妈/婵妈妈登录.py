import asyncio
import subprocess
import sys
import socket

from pyppeteer import connect

class Login:
    def __init__(self, username, password):
        self.browser = None
        self.page = None
        self.username = username
        self.password = password

    async def is_chrome_running(self, host, port):
        s = socket.socket()
        try:
            s.connect((host, port))
            s.close()
            return True
        except ConnectionRefusedError:
            return False

    async def execute_command(self):
        remote_debugging_port = 9222
        if await self.is_chrome_running('localhost', remote_debugging_port):
            return

        command = '"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\\seleniumAutomationProfile"'
        try:
            subprocess.Popen(command, shell=True)
        except Exception as e:
            print(f"执行命令时出现错误: {e}")
            sys.exit()

    async def perform_login(self, login_url):
        try:
            # await self.page.goto(login_url, waitUntil='networkidle0')
            # 清空输入框并触发输入事件
            selectors = [
                '#e2e-login-username',
                '#e2e-login-password'
            ]
            for selector in selectors:
                await self.page.evaluate(f"(selector) => document.querySelector(selector).value = ''", selector)
                await self.page.evaluate(f"""
                    (selector) => {{
                        const event = new Event('input', {{
                            bubbles: true,
                            cancelable: true,
                        }});
                        const element = document.querySelector(selector);
                        element.dispatchEvent(event);
                    }}
                """, selector)

            # 输入用户名和密码
            await self.page.type('#e2e-login-username', self.username)
            await self.page.type('#e2e-login-password', self.password)

            # 准备监听登录请求的响应
            login_response_future = self.page.waitForResponse(
                lambda response: 'login' in response.url,
                {'timeout': 10000}  # 设置超时时间为10秒
            )

            # 点击登录按钮
            await self.page.click('#e2e-login-submit')  # 确保这是登录按钮的正确选择器

            # 等待响应
            login_response = await login_response_future

            # 获取响应状态
            response_status = login_response.status

            # 打印响应状态
            # print(f'Login response status: {response_status}')

            # 根据响应状态判断是否登录成功
            if response_status == 200:
                print("登录成功")
                return True
            else:
                print(f"登录失败，响应状态码为: {response_status}")
                return False

        except Exception as e:
            print(f"登录过程中出现错误: {e}")
            return False

    async def is_logged_in(self):
        # 检查页面上的注销按钮是否存在
        logout_button_selector = 'img.login-out'
        logout_button = await self.page.querySelector(logout_button_selector)
        if logout_button:
            # print("用户已登录。")
            return True
        else:
            # print("用户未登录。")
            return False

    async def run(self):
        await self.execute_command()

        try:
            self.browser = await connect(browserURL='http://127.0.0.1:9222', defaultViewport=None)
            pages = await self.browser.pages()

            # 检查打开的页面数量
            if len(pages) > 1:
                print(f"当前有 {len(pages)} 个页面打开。请关闭不需要的页面后继续,请只保留婵妈妈的一个网页。")
                input("关闭页面后按回车键继续...")

                # 重新检查页面数量
                pages = await self.browser.pages()
                if len(pages) > 1:
                    print("仍然有多个页面打开。请关闭所有不需要的页面，请只保留婵妈妈的一个网页。")
                    return False

            self.page = pages[0]
            # await self.page.goto('https://www.chanmama.com/login', waitUntil='networkidle0')
            # 检查是否已登录
            if await self.is_logged_in():
                print('用户已登录，无需重复登录。')
                return True
            # 如果未登录，则执行登录过程
            else:
                await self.page.goto('https://www.chanmama.com/login', waitUntil='networkidle0')
                if await self.is_logged_in():
                    print('用户已登录，无需重复登录。')
                    return True
                login_successful = await self.perform_login('https://www.chanmama.com/login')
                if login_successful:
                    print('登录成功，已打开婵妈妈网站。')
                else:
                    print("登录失败。")
                    return False

        except Exception as e:
            print(f"出现错误: {e}")
            return False

        finally:
            if self.browser:
                await self.browser.disconnect()


async def main():
    login = Login(username='18811311746', password='18811311746')
    await login.run()

asyncio.run(main())

import asyncio
import subprocess
import sys
import socket
from pyppeteer import connect

class Login:
    def __init__(self,username,password):
        self.browser = None
        self.page = None
        self.password = password
        self.username = username
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
            # print("Chrome 已经在远程调试模式下运行。")
            return

        command = '"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\\seleniumAutomationProfile"'
        try:
            subprocess.Popen(command, shell=True)
            # print("已启动 Chrome 并启用远程调试模式。")
        except Exception as e:
            print(f"执行命令时出现错误: {e}")
            sys.exit()

    # 修改此方法以接受额外的参数：iframe_page
    async def click_button_in_iframe(self, iframe_page, button_text):
        try:
            button_xpath = f'//button[contains(text(), "{button_text}")]'
            button_element = await iframe_page.waitForXPath(button_xpath, {'visible': True, 'timeout': 5000})
            if button_element:
                await button_element.click()
                # print(f"在iframe中点击了按钮: {button_text}")
            else:
                print(f"在iframe中未找到按钮: {button_text}")
        except Exception as e:
            print(f"在iframe中点击按钮时出现错误: {e}")

    async def click_element_by_xpath(self, xpath):
        try:
            target_element = await self.page.waitForXPath(xpath, {'visible': True, 'timeout': 5000})
            if target_element:
                await target_element.click()
                # print(f"点击了XPath为 {xpath} 的元素。")
            else:
                print(f"未找到XPath为 {xpath} 的元素。")
        except Exception as e:
            print(f"尝试点击XPath为 {xpath} 的元素时出现错误: {str(e)}")

    async def switch_to_iframe_within_popup(self, popup_xpath):
        try:
            popup_element = await self.page.waitForXPath(popup_xpath, {'visible': True})
            if popup_element:
                # print(f"找到弹窗，XPath为 {popup_xpath}")

                iframe_element_handle_list = await popup_element.xpath('.//iframe')
                if iframe_element_handle_list:
                    iframe_element = iframe_element_handle_list[0]
                    # print("在弹窗中找到iframe。")

                    iframe_page = await iframe_element.contentFrame()

                    if iframe_page:
                        await self.get_button_info_in_iframe(iframe_page)

                    return iframe_page
                else:
                    print("在弹窗中未找到iframe。")
                    return None
            else:
                print("未找到弹窗。")
                return None
        except Exception as e:
            print(f"出现错误: {e}")
            return None

    async def get_button_info_in_iframe(self, page):
        try:
            button_elements = await page.xpath('//button')
            # print(f"iframe中的按钮数量: {len(button_elements)}")

            button_info = []
            for button_element in button_elements:
                button_text = await page.evaluate('(element) => element.textContent', button_element)
                # print(f"按钮文本: {button_text}")
                button_info.append(button_text)

            return button_info
        except Exception as e:
            print(f"在iframe中获取按钮信息时出现错误: {e}")
            return []

    async def execute_function_in_iframe(self, page):
        try:
            # 在iframe中执行特定功能
            # 这里可以添加您要执行的功能代码
            print("打开指定网页")
            return True
        except Exception as e:
            print(f"在iframe中执行功能时出现错误: {e}")

    async def check_element_by_selector(self, selector, timeout=3000):
        try:
            await self.page.waitForSelector(selector, {'visible': True, 'timeout': timeout})
            print(f"找到选择器为 {selector} 的元素。")
            return True
        except Exception as e:
            print(f"未找到选择器为 {selector} 的元素。错误信息: {str(e)}")
            return False

    async def check_element_by_xpath(self, xpath, timeout=3000):
        try:
            await self.page.waitForXPath(xpath, {'visible': True, 'timeout': timeout})
            # print(f"找到XPath为 {xpath} 的元素。")
            return True
        except Exception as e:
            print(f"未找到XPath为 {xpath} 的元素。错误信息: {str(e)}")
            return False

    async def is_current_page(self, target_url):
        current_url = await self.page.evaluate('window.location.href')
        return target_url == current_url

    async def perform_login(self):
        try:
            response = await self.page.goto('http://121.40.180.3:6060/web/index', waitUntil='networkidle0')
            if response.status == 200 and self.page.url == "http://121.40.180.3:6060/web/index":
                print("您已经登录！")
                return True

            await self.page.goto('http://121.40.180.3:6060')

            username_xpath = '/html/body/div[1]/div/div[2]/form/div[1]/input[2]'
            password_xpath = '/html/body/div[1]/div/div[2]/form/div[2]/input'

            username_input = await self.page.waitForXPath(username_xpath, {'visible': True})
            password_input = await self.page.waitForXPath(password_xpath, {'visible': True})

            if username_input and password_input:
                await username_input.type(self.username)
                await password_input.type(self.password)

            captcha_code = input("请输入浏览器中的验证码: ")

            captcha_input_xpath = '//*[@id="vercode"]'
            captcha_input = await self.page.waitForXPath(captcha_input_xpath, {'visible': True})
            if captcha_input:
                await captcha_input.type(captcha_code)

            submit_button_selector = 'button[type="submit"]'
            await self.page.click(submit_button_selector)

            await self.page.waitForNavigation(waitUntil='networkidle0')

            if self.page.url == "http://121.40.180.3:6060/web/index":
                print("登录成功。")
                return True

            print("登录失败或需要进一步验证。")
            return False
        except Exception as e:
            print(f"出现错误: {e}")
            return False

    async def run(self):
        await self.execute_command()

        login_successful = False
        try:
            self.browser = await connect(browserURL='http://127.0.0.1:9222', defaultViewport=None)
            pages = await self.browser.pages()
            self.page = pages[0]
            username = '18812346688'
            password = '6677xx'

            page_xinkuai_open = False
            page_xindou_open = False

            try:
                # 首先检查是否已经打开这两个页面
                page_xinkuai_open = await self.is_current_page('http://121.40.92.153:50888/')
                page_xindou_open = await self.is_current_page('http://121.40.92.153:50999/home')

                # 只有当这两个页面都没有打开时，才执行登录过程
                if not page_xinkuai_open and not page_xindou_open:
                    login_successful = await self.perform_login()
                elif page_xinkuai_open:
                    print("新快页面已经打开。")
                elif page_xindou_open:
                    print('新抖页面已经打开。')
            except Exception as e:
                print(f"出现错误: {e}")
        finally:
            if page_xinkuai_open or page_xindou_open:
                return True

            if login_successful:
                # print("登录成功，可以继续后续操作...")

                await self.click_element_by_xpath('/html/body/div[3]/div/a/div[1]/button')

                popup_found = await self.check_element_by_xpath('//*[@id="layui-layer1"]')

                if popup_found:
                    iframe_page = await self.switch_to_iframe_within_popup('//*[@id="layui-layer1"]')

                    if iframe_page:
                        # 获取按钮信息
                        button_info = await self.get_button_info_in_iframe(iframe_page)

                        # 过滤掉纯数字的按钮文本
                        button_info = [text for text in button_info if not text.strip().isdigit()]

                        # 如果过滤后还有按钮，才显示给用户
                        if button_info:
                            print('请选择以下你想访问的页面')
                            for idx, button_text in enumerate(button_info):
                                print(f"{idx + 1}. {button_text.strip()}")  # 使用strip()确保文本前后没有空格

                        while True:
                            choice = input("请选择要点击的按钮 (1/2): ")
                            if choice in ['1', '2']:
                                break
                            else:
                                print("无效的选择，请输入 1 或 2")

                        # 根据用户选择点击相应的按钮
                        selected_button = button_info[int(choice) - 1]
                        await self.click_button_in_iframe(iframe_page, selected_button)

                        # 在 iframe 中执行特定功能
                        a = await self.execute_function_in_iframe(iframe_page)

                    # TODO: 在成功登录后，继续执行其他操作

                else:
                    print("未在弹窗中找到iframe。")
                    return False
            else:
                print("登录过程中出现问题.")
                return False
            pages = await self.browser.pages()
            page_count = len(pages)
            for i in range(page_count):
                page = pages[i]
                await page.close()
                return a

def main():
    login = Login(username = '18812346688',
            password = '6677xx')
    asyncio.run(login.run())

main()


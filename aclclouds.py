import time
import os
import json
import re
import random
import requests

from seleniumbase import SB
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# ================= 智能环境配置 =================
if "DISPLAY" not in os.environ:
    os.environ["DISPLAY"] = ":1"

if "XAUTHORITY" not in os.environ:
    if os.path.exists("/home/headless/.Xauthority"):
        os.environ["XAUTHORITY"] = "/home/headless/.Xauthority"

print(f"[DEBUG] DISPLAY: {os.environ.get('DISPLAY')}")
print(f"[DEBUG] XAUTHORITY: {os.environ.get('XAUTHORITY')}")

# ================= 配置 =================
PROXY_URL = os.getenv("PROXY", "")
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

LOGIN_URL = "https://dash.aclclouds.com/auth/oauth/discord"
PROJECT_URL = "https://dash.aclclouds.com/projects"


class AclcloudsRenewal:

    def __init__(self):
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.screenshot_dir = os.path.join(self.BASE_DIR, "artifacts")
        os.makedirs(self.screenshot_dir, exist_ok=True)

    # ================= 工具 =================
    def log(self, msg):
        print(f"[{time.strftime('%H:%M:%S')}] [INFO] {msg}", flush=True)

    def send_telegram_notify(self, message, photo_path=None):
        if not TG_TOKEN or not TG_CHAT_ID:
            return

        try:
            if photo_path and os.path.exists(photo_path):
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
                with open(photo_path, "rb") as f:
                    requests.post(url, data={"chat_id": TG_CHAT_ID, "caption": message}, files={"photo": f})
            else:
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
                requests.post(url, data={"chat_id": TG_CHAT_ID, "text": message})
        except Exception as e:
            self.log(f"TG失败: {e}")

    # ================= Discord 登录 =================
    def discord_login(self, sb, EMAIL, PASSWORD):
        self.log("🚀 Discord 登录")

        try:
            sb.wait_for_element("input[name='email']", timeout=15)

            sb.fill("input[name='email']", EMAIL)
            sb.fill("input[name='password']", PASSWORD)

            sb.click("button[type='submit']")

            time.sleep(8)

        except Exception as e:
            self.log(f"❌ 登录失败: {e}")

    # ================= OAuth 核心修复版 =================
    def oauth_debug(self, sb):

        self.log("🔐 OAuth 稳定处理开始")

        def get_text(el):
            try:
                return " ".join([
                    el.text or "",
                    el.get_attribute("innerText") or "",
                    el.get_attribute("textContent") or "",
                    el.get_attribute("aria-label") or "",
                    el.get_attribute("value") or "",
                    el.get_attribute("innerHTML") or "",
                ]).lower()
            except:
                return ""

        def is_auth_button(el):
            t = get_text(el)
            return any(k in t for k in [
                "authorize",
                "allow",
                "continue",
                "accept",
                "yes"
            ])

        def get_elements(sb):
            sels = [
                "button",
                "a",
                "input",
                "[role='button']",
                "div[role='button']"
            ]
            out = []
            for s in sels:
                try:
                    out += sb.find_elements(s)
                except:
                    pass
            return out

        def scroll(sb):
            try:
                sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(0.5)
                sb.execute_script("window.scrollTo(0, 0);")

                sb.send_keys("body", Keys.PAGE_DOWN)
                sb.send_keys("body", Keys.END)

                try:
                    ActionChains(sb.driver).send_keys(Keys.PAGE_DOWN).perform()
                except:
                    pass
            except:
                pass

        for i in range(20):

            self.log(f"🔍 OAuth扫描 {i+1}/20")

            time.sleep(2)
            scroll(sb)
            time.sleep(1)

            if "client.hnhost.net" in sb.get_current_url():
                self.log("✅ OAuth完成")
                return True

            els = get_elements(sb)
            self.log(f"🧩 元素数量: {len(els)}")

            target = None

            for el in els:
                try:
                    if is_auth_button(el):
                        target = el
                        break
                except:
                    pass

            if target:
                try:
                    self.log("🟢 点击OAuth按钮")

                    sb.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});",
                        target
                    )

                    time.sleep(1)

                    try:
                        target.click()
                    except:
                        try:
                            ActionChains(sb.driver).move_to_element(target).click().perform()
                        except:
                            sb.execute_script("arguments[0].click();", target)

                    time.sleep(8)

                except Exception as e:
                    self.log(f"❌ 点击失败: {e}")

            else:
                self.log("⚠️ 未找到按钮")

        return False

    # ================= 主流程 =================
    def run(self):

        self.log("🚀 启动流程")

        with SB(
            uc=True,
            test=True,
            headed=True,
            headless=False,
            xvfb=False,
            proxy=PROXY_URL if PROXY_URL else None
        ) as sb:

            try:
                self.log("🌍 打开登录页")

                sb.uc_open_with_reconnect(LOGIN_URL, reconnect_time=25)
                time.sleep(5)

                self.discord_login(sb, EMAIL, PASSWORD)

                self.oauth_debug(sb)

                self.log("✅ 登录流程完成")

                sb.save_screenshot(f"{self.screenshot_dir}/done.png")

            except Exception as e:
                self.log(f"❌ 运行异常: {e}")
                sb.save_screenshot(f"{self.screenshot_dir}/error.png")


if __name__ == "__main__":
    AclcloudsRenewal().run()

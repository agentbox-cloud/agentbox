import time
from agentbox import Sandbox

# DOMAIN = "agentbox.net.cn"
# API_KEY = "ab_b089f13a7182672e026a2cf93c3b89123ba52d43"
# TEMPLATE = "wemmodr8mb2uk3kn7exw"

DOMAIN = "agentbox.lingyiwanwu.com"
API_KEY = "ab_06152e252767ec4ea707421546cacbb71c5acab4"
TEMPLATE = "wemmodr8mb2uk3kn7exw"

LOCAL_PATH = "/Users/haohaijiao/Desktop/agentbox/MobileAnJian4.2.0.apk"
APP_PATH = "/sdcard/Download/MobileAnJian4.2.0.apk"

def test_install_by_adb_shell():
    # sbx = Sandbox(
    #     api_key=API_KEY,
    #     template=TEMPLATE,
    #     domain=DOMAIN,
    #     timeout=3600)

    sbx = Sandbox.connect(
        sandbox_id="i77asngphzmuz1d9wljnv-BRD-2C188ECE494941B0",
        api_key=API_KEY,
        domain=DOMAIN,
        timeout=3600)

    print(sbx.get_info())

    try:
        sbx.adb_shell.connect()
        print(sbx.adb_shell.shell("ls -l /sdcard/Download"))
        if not sbx.adb_shell.exists(APP_PATH):
            start_time = time.time()
            sbx.adb_shell.push(LOCAL_PATH, APP_PATH)
            print("push cost:", time.time() - start_time)
        if sbx.adb_shell.exists(APP_PATH):
            result = sbx.adb_shell.install(APP_PATH, reinstall=True) # 安装应用
            # result = sbx.adb_shell.uninstall("com.cyjh.mobileanjian") # 卸载应用
            print("Install result:", result)

        # start_time = time.time()
        # print(start_time)
        # sbx.adb_shell.install(APP_PATH, reinstall=True)
        # print("push cost:", time.time() - start_time)

        # 查看已安装应用列表
        pmList = sbx.adb_shell.shell("pm list packages")
        print(len(pmList.split("\n")))
        for package in pmList.split("\n"):
            if "anjian" in package.lower() or "baidu" in package.lower():
                print(package)
    except Exception as e:
        print(e)
    finally:
        sbx.adb_shell.close()


if __name__ == "__main__":
    test_install_by_adb_shell()
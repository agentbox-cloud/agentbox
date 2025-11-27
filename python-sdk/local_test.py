import time
from agentbox import Sandbox



# DOMAIN = "agentbox.cloud"
# API_KEY = "ab_63f68fa6a599cf4ffb9305ae0c4f3e27f45ff69f"
# TEMPLATE = "90s8y31663z402tv2ive"

# DOMAIN = "agentbox.lingyiwanwu.com"
# API_KEY = "ab_06152e252767ec4ea707421546cacbb71c5acab4"
# TEMPLATE = "ldk37fby780vqlzy41jc"

DOMAIN = "agentbox.net.cn"
API_KEY = "ab_b089f13a7182672e026a2cf93c3b89123ba52d43"
TEMPLATE = "gu64l2b8yfv5xqpkxvn4"

def test_sandbox():
    sbx = Sandbox(api_key=API_KEY,
                template=TEMPLATE,
                domain=DOMAIN,
                timeout=300)

    _get_info_sandbox(sbx)
    _is_running_sandbox(sbx)

    sbx.set_timeout(60) # 超时后被kill，不会生成快照信息
    _is_running_sandbox(sbx)
    _get_info_sandbox(sbx)

    _pause_sandbox(sbx) # 手动暂停，生成快照
    _is_running_sandbox(sbx)

    _resume_sandbox(sbx) # 手动恢复，检查快照信息还存在
    _is_running_sandbox(sbx)

    _get_info_sandbox(sbx)
    sbx.set_timeout(60) # 超时后被自动kill，快照信息还存在

    _kill_sandbox(sbx) # 手动kill，清理快照信息，如果不执行此操作，快照信息会一直存在
    _is_running_sandbox(sbx)



def test_sandbox_connect(sandbox_id):
    print("\n<<<test sandbox connect>>>\n")
    print(sandbox_id)

    start_time = time.time()
    sbx = Sandbox.connect(
        api_key=API_KEY,
        domain=DOMAIN,
        sandbox_id=sandbox_id,
        timeout=150) # 连接已超时或已暂停的沙盒ID，并设置超时时间
    print("connect cost",time.time() - start_time)
    
    print(sbx.is_running())
    _get_info_sandbox(sbx)

    _pause_sandbox(sbx) # 手动暂停，不会重新生成快照信息，之前自动保存的快照信息还存在
    _is_running_sandbox(sbx)

    _connect_sandbox(sbx) # 连接已暂停的沙盒，默认超时时间5分钟
    _get_info_sandbox(sbx)

    print(sbx.is_running())
    _get_info_sandbox(sbx)

    _kill_sandbox(sbx) # 手动kill，清理快照信息，如果不执行此操作，快照信息会一直存在
    _is_running_sandbox(sbx)


def _connect_sandbox(sbx, timeout=300):
    start_time = time.time()
    sbx.connect(timeout=timeout)
    print("connect cost",time.time() - start_time)


def _get_info_sandbox(sbx):
    start_time = time.time()
    print(sbx.get_info())
    print("get info cost",time.time() - start_time)
    print()


def _pause_sandbox(sbx):
    start_time = time.time()
    sbx.pause()
    print("pause cost",time.time() - start_time)
    print()


def _resume_sandbox(sbx):
    start_time = time.time()
    # sbx.resume()
    Sandbox.resume(
        sandbox_id=sbx.sandbox_id,
        api_key=API_KEY,
        domain=DOMAIN,
        timeout=10)
    print("resume cost",time.time() - start_time)
    print()

def test_resume_sandbox_by_id(sandbox_id):
    start_time = time.time()
    sbx =Sandbox.resume(
        sandbox_id=sandbox_id,
        api_key=API_KEY,
        domain=DOMAIN,
        # auto_pause=True,
        timeout=10)
    print("resume cost",time.time() - start_time)
    print()

    _is_running_sandbox(sbx)
    _get_info_sandbox(sbx)

    time.sleep(10)
    _is_running_sandbox(sbx)


def _is_running_sandbox(sbx):
    start_time = time.time()
    print(sbx.is_running())
    print("is running cost",time.time() - start_time)
    print()


def _kill_sandbox(sbx):
    start_time = time.time()
    sbx.kill()
    print("kill cost",time.time() - start_time)


def test_sandbox_beta_create():
    sbx = Sandbox.beta_create(
        api_key=API_KEY,
        domain=DOMAIN,
        template=TEMPLATE,
        auto_pause=True,
        timeout=600)

    print(sbx.get_info())
    print(sbx.is_running())
    print(sbx.sandbox_id)

    _connect_sandbox(sbx) # 连接运行中的沙盒实例，超时时间默认5分钟，超时后自动暂停，并生成快照信息
    sbx.set_timeout(60)  # 超时后自动暂停，并生成快照信息
    _is_running_sandbox(sbx)
    _get_info_sandbox(sbx)


def test_pause_and_connect(sbxid):
    sbx = Sandbox.connect(
        domain=DOMAIN,
        api_key=API_KEY,
        sandbox_id=sbxid, 
        timeout=1200) # 连接已超时或已暂停的沙盒ID，并设置超时时间
    
    _is_running_sandbox(sbx)
    _get_info_sandbox(sbx)

    _pause_sandbox(sbx) # 手动暂停auto_pause=True的沙盒，不会重新生成快照信息，之前自动保存的快照信息还存在
    _is_running_sandbox(sbx)

    _resume_sandbox(sbx)
    # _connect_sandbox(sbx)
    sbx.set_timeout(60)  # 如果创建时设置auto_pause=True，超时后自动暂停，不会重新生成快照信息
    _is_running_sandbox(sbx)
    _get_info_sandbox(sbx)


# def test_brd_connect(sandbox_id):
#     # sbx = Sandbox(template="jttw5x7mzj4lv8cwmiui", api_key=API_KEY, timeout=3600)
#     sbx = Sandbox.connect(
#         domain=DOMAIN,
#         api_key=API_KEY,
#         sandbox_id=sandbox_id,
#         timeout=150)
#     print(sbx.get_info())
#     # print(sbx.is_running())
#     # print(sbx.get_metrics())

#     # sbx.set_timeout(300)
#     # print(sbx.get_info())
#     # print(sbx.is_running())

#     sbx.pause()
#     print(sbx.is_running())
#     time.sleep(10)
#     print(sbx.is_running())
#     sbx.resume()
#     print(sbx.is_running())


if __name__ == "__main__":
    test_sandbox()
    test_sandbox_beta_create()
    # test_pause_and_connect('i1h7vjgge8m2jho2fh9us-058d683d')
    # test_sandbox_beta_create()
    # test_pause_and_connect('imun790hek4rgsuyk3d44-058d683d')
    # test_sandbox_connect('i0zhz2xa5zwaokuaauaun-058d683d')

    # sandbox_id = 'ipvhoqgjm61r122krfxd3-09fbf109'
    # test_pause_and_connect(sandbox_id)

    # sandbox_id = 'ilv8k19fxx9lx13pxgf08-BRD-4EE26420235144E5'
    # test_brd_connect(sandbox_id)
    
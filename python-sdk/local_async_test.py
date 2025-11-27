import asyncio
import time
from agentbox import AsyncSandbox

DOMAIN = "agentbox.net.cn"
API_KEY = "ab_b089f13a7182672e026a2cf93c3b89123ba52d43"
TEMPLATE = "gu64l2b8yfv5xqpkxvn4"

async def test_sandbox():
    sbx = await AsyncSandbox.create(
        api_key=API_KEY,
        template=TEMPLATE,
        timeout=30,
        domain=DOMAIN,
    )

    await _get_info_sandbox(sbx)
    await _is_running_sandbox(sbx)

    await sbx.set_timeout(600)
    await _get_info_sandbox(sbx)

    await _pause_sandbox(sbx)
    await _is_running_sandbox(sbx)

    await _resume_sandbox(sbx)
    await _is_running_sandbox(sbx)

    await _kill_sandbox(sbx)
    await _is_running_sandbox(sbx)



async def test_sandbox_connect(sandbox_id):
    print("\n<<<test sandbox connect>>>\n")
    print(sandbox_id)

    start_time = time.time()
    sbx = await AsyncSandbox.connect(
        api_key=API_KEY,
        sandbox_id=sandbox_id,
        timeout=15,
        domain=DOMAIN,
    )
    print("connect cost",time.time() - start_time)
    
    # await asyncio.sleep(5)
    # print(await sbx.is_running())
    await _get_info_sandbox(sbx)

    # await _pause_sandbox(sbx)
    # await asyncio.sleep(3)

    # await _connect_sandbox(sbx)
    # await _get_info_sandbox(sbx)

    # await asyncio.sleep(5)
    # print(await sbx.is_running())
    # await _get_info_sandbox(sbx)

    # await asyncio.sleep(5)
    # print(await sbx.is_running())
    # await _get_info_sandbox(sbx)


async def _connect_sandbox(sbx):
    start_time = time.time()
    await sbx.connect(timeout=10)
    print("connect cost",time.time() - start_time)


async def _get_info_sandbox(sbx):
    start_time = time.time()
    print(await sbx.get_info())
    print("get info cost",time.time() - start_time)
    print()


async def _pause_sandbox(sbx):
    start_time = time.time()
    await sbx.pause()
    print("pause cost",time.time() - start_time)
    print()


async def _resume_sandbox(sbx):
    start_time = time.time()
    sandbox_id = sbx.sandbox_id
    await AsyncSandbox.resume(
        sandbox_id=sandbox_id,
        timeout=10,
        api_key=API_KEY,
        domain=DOMAIN,
    )
    # await AsyncSandbox.resume(sbx.sandbox_id, auto_pause=True, timeout=10)
    print("resume cost",time.time() - start_time)
    print()


async def _is_running_sandbox(sbx):
    start_time = time.time()
    print(await sbx.is_running())
    print("is running cost",time.time() - start_time)
    print()


async def _kill_sandbox(sbx):
    start_time = time.time()
    await sbx.kill()
    print("kill cost",time.time() - start_time)


async def test_sandbox_beta_create():
    sbx = await AsyncSandbox.beta_create(
        api_key=API_KEY,
        template=TEMPLATE,
        auto_pause=True,
        timeout=30,
        domain=DOMAIN,
    )

    print(await sbx.get_info())
    print(await sbx.is_running())
    print(sbx.sandbox_id)

    await _pause_sandbox(sbx)
    print(await sbx.is_running())

    await sbx.connect()
    print(await sbx.get_info())
    print(await sbx.is_running())
    print(sbx.sandbox_id)

async def test_pause_and_connect(sandbox_id):
    sbx = await AsyncSandbox.connect(
        api_key=API_KEY,
        sandbox_id=sandbox_id,
        timeout=150,
        domain=DOMAIN,
    )
    print(await sbx.get_info())
    print(await sbx.is_running())

    # metrics = await sbx.get_metrics()
    # print('Sandbox metrics', metrics) 

    await sbx.set_timeout(300)
    print(await sbx.get_info())
    print(await sbx.is_running())

    await _pause_sandbox(sbx)
    print(await sbx.is_running())

    await _connect_sandbox(sbx)
    print(await sbx.is_running())
    print(await sbx.get_info())
    


if __name__ == "__main__":
    # asyncio.run(test_sandbox())
    asyncio.run(test_sandbox_beta_create())
    # sandbox_id = 'ixnxrvqwzj0j2k1hcrtjh-058d683d'
    # asyncio.run(test_pause_and_connect(sandbox_id))
    # sandbox_id = 'in2xxay6mip2jp572mgby-BRD-B098F4EC958E4762'
    # asyncio.run(test_sandbox_connect(sandbox_id))
    

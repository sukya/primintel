import sys
import json
import time
import asyncio
import os
import random
import logging
from fake_useragent import UserAgent
# 强制底层使用 curl_cffi 以对抗高级 TLS 指纹追踪
from curl_cffi.requests import AsyncSession
from bingart import BingArt, Model, Aspect, AuthCookieError, PromptRejectedError
import argparse

# 全局消音：将 logging 和标准错误强制阻断，确保标准输出绝对是一串纯净的 JSON
logging.getLogger().setLevel(logging.CRITICAL)
sys.stderr = open(os.devnull, 'w')

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'config.json'))
OUTPUTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'outputs'))

def load_config():
    if not os.path.exists(CONFIG_PATH):
        # 兜底：由于 stdout 必须为 JSON，此处打印 JSON 并退出
        print(json.dumps({"error": f"Configuration file not found: {CONFIG_PATH}"}))
        sys.exit(1)
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config_data):
    """状态回写 (Critical): 持久化保存至磁盘"""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)

def get_valid_cookie(config_data):
    """智能轮询引擎"""
    current_time = time.time()
    
    # 遍历洗牌状态
    for account in config_data.get("auth_cookies", []):
        if account.get("status") == "depleted":
            # 24小时冷却期 (86400秒) 放行机制
            if current_time - account.get("last_used", 0) > 86400:
                account["status"] = "active"
                save_config(config_data)  # 状态流转立即持久化
                
    # 择取存活目标池
    active_accounts = [acc for acc in config_data.get("auth_cookies", []) if acc.get("status") == "active"]
    if not active_accounts:
        # 兜底容错：如果用户手动修改了配置文件里的 _U 字符串却忘了把 status 改回 active，导致全军覆没
        # 则在此处自动全部复活它们，给予一次重新尝试的机会
        for acc in config_data.get("auth_cookies", []):
            acc["status"] = "active"
        active_accounts = config_data.get("auth_cookies", [])
        save_config(config_data)
        
        if not active_accounts:
            return None
    
    # 动态负载均衡：选拔距离上次使役时间最为久远的 account
    active_accounts.sort(key=lambda x: x.get("last_used", 0))
    return active_accounts[0]

async def download_image(session, index, img_url):
    """带对抗特征的安全下载流"""
    # 随机化下载延时
    await asyncio.sleep(random.uniform(1.2, 3.5))
    file_name = f"generation_{int(time.time())}_{index}.jpg"
    save_path = os.path.join(OUTPUTS_DIR, file_name)
    
    try:
        response = await session.get(img_url)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            # 返回相对路径以供标准输出 JSON 给 Agent 调度
            return f"outputs/{file_name}"
    except Exception:
        pass
    return None

async def main(prompt, model_str="dalle3", aspect_str="square"):
    config_data = load_config()
    account = get_valid_cookie(config_data)
    
    if not account:
        print(json.dumps({"error": "No valid active accounts remaining. All accounts are depleted or expired."}))
        sys.exit(1)
        
    cookie_u = account.get("cookie_U", "").strip()
    
    # 清洗：如果用户直接把 " _U=xxxx " 粘贴进去了
    if cookie_u.startswith("_U="):
        cookie_u = cookie_u[3:]
    elif " _U=" in cookie_u:
        import re
        match = re.search(r"_U=([^;]+)", cookie_u)
        if match:
            cookie_u = match.group(1)
            
    # 【安全与反爬策略 1】：每次正式建立连接前的强休眠 (5-12秒)
    sleep_duration = random.uniform(5, 12)
    time.sleep(sleep_duration)  # 这里可以用 sync sleep，因为这是脚本最顶层单线入口，阻塞无妨
    
    # 【安全与反爬策略 2】：使用现代标准 Edge 浏览器 UA (Bing 会严厉拦截非 Edge 浏览器的生图请求)
    fake_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
    
    try:
        # 强制接管：BingArt 内部已集结 curl_cffi AsyncSession，可应对强力 TLS 校验
        async with BingArt(auth_cookie_U=cookie_u) as bing_art:
            # 修改底层请求头混入动态 UA 指纹
            bing_art.session.headers.update({"user-agent": fake_ua})
            
            # 记录最新征用时间以供洗牌排序
            account["last_used"] = time.time()
            save_config(config_data)
            
            # Map string to Enums
            model_map = {
                "dalle3": Model.DALLE,
                "gpt4o": Model.GPT4O,
                "mai1": Model.MAI1
            }
            aspect_map = {
                "square": Aspect.SQUARE,
                "landscape": Aspect.LANDSCAPE,
                "portrait": Aspect.PORTRAIT
            }
            
            target_model = model_map.get(model_str, Model.DALLE)
            target_aspect = aspect_map.get(aspect_str, Aspect.SQUARE)
            
            # 主并发发起生成
            results = await bing_art.generate(prompt, model=target_model, aspect=target_aspect)
            
            images_list = results.get("images", [])
            downloaded_paths = []
            
            if images_list:
                os.makedirs(OUTPUTS_DIR, exist_ok=True)
                download_session = bing_art.session
                
                # 并发收集下载队列（最多获取4张高分返回图）
                tasks = []
                for idx, img_obj in enumerate(images_list[:4]):
                    img_url = img_obj.get("url")
                    if img_url:
                        tasks.append(download_image(download_session, idx, img_url))
                
                out_paths = await asyncio.gather(*tasks)
                downloaded_paths = [p for p in out_paths if p]
                
                if downloaded_paths:
                    # ✅ [标准输出] 最高质量的完结回执
                    print(json.dumps({"status": "success", "images": downloaded_paths}))
                else:
                    raise Exception("Image extraction array empty or downloads failed.")
            else:
                raise Exception("Exhausted or No Image Return")
                
    except AuthCookieError as ace:
        # 401 / 403 惩罚态标记 - 死亡流放
        account["status"] = "expired"
        reason = str(ace) or "Unauthorized / Forbidden (401/403)"
        account["error_reason"] = reason
        account["last_error_at"] = time.time()
        save_config(config_data)
        print(json.dumps({"error": f"Auth cookie expired: {reason}. Marked as expired."}))
        
    except PromptRejectedError as pre:
        print(json.dumps({"error": f"Content blocked by safety policy: {str(pre)}"}))
        
    except Exception as e:
        # 400 配额耗尽 (Quota Exhausted) 或者是其他封禁异常，视为耗尽态标记 - 冷冻24h
        reason = str(e)
        if "400" in reason or "quota" in reason.lower():
            account["status"] = "depleted"
            msg = "Account quota likely exhausted (400)."
        else:
            account["status"] = "expired"
            msg = f"Unhandled error: {reason}"
            
        account["error_reason"] = reason
        account["last_error_at"] = time.time()
        account["last_used"] = time.time()
        save_config(config_data)
        print(json.dumps({"error": f"{msg} Marked accordingly. Details: {reason}"}))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bing Image Creator CLI")
    parser.add_argument("prompt", help="The prompt to generate image from")
    parser.add_argument("--model", type=str, default="dalle3", choices=["dalle3", "gpt4o", "mai1"], help="Model to use")
    parser.add_argument("--aspect", type=str, default="square", choices=["square", "landscape", "portrait"], help="Aspect ratio to use")
    
    args = parser.parse_args()
    
    # 强制劫持标准输出避免 curl_cffi 输出扰乱 JSON
    try:
        asyncio.run(main(args.prompt, args.model, args.aspect))
    except Exception as fatal_e:
        print(json.dumps({"error": f"Fatal unhandled exception: {str(fatal_e)}"}))
        sys.exit(1)

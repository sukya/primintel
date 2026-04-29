import sys
import json
import time
import asyncio
import os
import argparse
from curl_cffi.requests import AsyncSession

# 锁定路径
SKILL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_PATH = os.path.join(SKILL_DIR, 'resources', 'config.json')
OUTPUTS_DIR = os.path.join(SKILL_DIR, 'outputs')
ROOT_CONFIG_PATH = os.path.abspath(os.path.join(SKILL_DIR, '..', '..', 'config.json'))

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

async def download_image(session, index, img_url):
    file_name = f"zhipu_{int(time.time())}_{index}.jpg"
    save_path = os.path.join(OUTPUTS_DIR, file_name)
    try:
        response = await session.get(img_url)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            # 必须返回基于项目根目录的相对路径。
            # Web UI 需要依赖 /skills/... 路由提供静态服务
            # WeChat 端通过 chat_channel 解析该相对路径为绝对路径并发送
            return f"/skills/zhipu-cogview-image-creator/outputs/{file_name}"
    except Exception:
        pass
    return None

async def main(prompt):
    # 负载优先级逻辑：技能配置 > 全局配置
    skill_conf = load_json(CONFIG_PATH)
    root_conf = load_json(ROOT_CONFIG_PATH)
    
    api_key = skill_conf.get("api_key") or root_conf.get("zhipu_ai_api_key")
    model = skill_conf.get("model_name", "cogview-3-flash")
    size = skill_conf.get("size", "1024x1024")
    
    user_id = skill_conf.get("user_id")
    
    if not api_key:
        print(json.dumps({"error": "No Zhipu API Key found in skill config or root config."}))
        sys.exit(1)

    url = "https://open.bigmodel.cn/api/paas/v4/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "prompt": prompt,
        "size": size
    }
    
    if user_id:
        payload["user_id"] = user_id

    async with AsyncSession() as session:
        try:
            response = await session.post(url, headers=headers, json=payload, timeout=60)
            res_data = response.json()
            
            if response.status_code != 200:
                print(json.dumps({"error": f"API Error: {res_data.get('error', 'Unknown error')}"}))
                return

            images_data = res_data.get("data", [])
            if not images_data:
                print(json.dumps({"error": "No images returned from Zhipu API."}))
                return

            os.makedirs(OUTPUTS_DIR, exist_ok=True)
            tasks = []
            for idx, img_obj in enumerate(images_data):
                img_url = img_obj.get("url")
                if img_url:
                    tasks.append(download_image(session, idx, img_url))
            
            downloaded = await asyncio.gather(*tasks)
            final_paths = [p for p in downloaded if p]
            
            if final_paths:
                print(json.dumps({"status": "success", "images": final_paths}))
            else:
                print(json.dumps({"error": "Failed to download generated images."}))
                
        except Exception as e:
            print(json.dumps({"error": f"Exception during request: {str(e)}"}))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", help="Text prompt for image generation")
    args = parser.parse_args()
    
    asyncio.run(main(args.prompt))

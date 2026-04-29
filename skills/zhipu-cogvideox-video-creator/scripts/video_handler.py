import sys
import json
import time
import asyncio
import os
import argparse
from curl_cffi.requests import AsyncSession

# Paths
SKILL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_PATH = os.path.join(SKILL_DIR, 'resources', 'config.json')
OUTPUTS_DIR = os.path.join(SKILL_DIR, 'outputs')
ROOT_CONFIG_PATH = os.path.abspath(os.path.join(SKILL_DIR, '..', '..', 'config.json'))

def load_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

async def download_file(session, url, extension=".mp4"):
    file_name = f"zhipu_video_{int(time.time())}{extension}"
    save_path = os.path.join(OUTPUTS_DIR, file_name)
    try:
        response = await session.get(url, timeout=120)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return f"/skills/zhipu-cogvideox-video-creator/outputs/{file_name}"
    except Exception as e:
        sys.stderr.write(f"Download error: {e}\n")
    return None

async def main(prompt):
    # Load configs
    skill_conf = load_json(CONFIG_PATH)
    root_conf = load_json(ROOT_CONFIG_PATH)
    
    api_key = skill_conf.get("api_key") or root_conf.get("zhipu_ai_api_key")
    model = skill_conf.get("model_name", "cogvideox-flash")
    size = skill_conf.get("size", "1280x720")
    watermark_enabled = skill_conf.get("watermark_enabled", False)
    
    if not api_key:
        error_msg = f"No Zhipu API Key found. Skill config: {list(skill_conf.keys())}, Root config: {list(root_conf.keys())}"
        print(json.dumps({"error": error_msg, "debug_path": CONFIG_PATH}))
        sys.exit(1)

    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    base_url = "https://open.bigmodel.cn/api/paas/v4"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    async with AsyncSession() as session:
        try:
            # 1. Submit Generation Task
            gen_url = f"{base_url}/videos/generations"
            payload = {
                "model": model,
                "prompt": prompt,
                "size": size,
                "watermark_enabled": watermark_enabled
            }
            
            response = await session.post(gen_url, headers=headers, json=payload, timeout=30)
            res_data = response.json()
            
            if response.status_code != 200:
                print(json.dumps({"error": f"API Error (Submit): {res_data.get('error', 'Unknown error')}"}))
                return

            task_id = res_data.get("id")
            if not task_id:
                print(json.dumps({"error": "Failed to get task ID from Zhipu API."}))
                return

            # 2. Polling loop
            max_retries = 120 # ~600 seconds total (Video generation is slow)
            poll_interval = 5
            video_url = None
            
            for _ in range(max_retries):
                await asyncio.sleep(poll_interval)
                query_url = f"{base_url}/async-result/{task_id}"
                
                poll_res = await session.get(query_url, headers=headers, timeout=15)
                poll_data = poll_res.json()
                
                if poll_res.status_code != 200:
                    continue
                
                task_status = poll_data.get("task_status")
                if task_status == "SUCCESS":
                    video_list = poll_data.get("video_result", [])
                    if video_list:
                        video_url = video_list[0].get("url")
                    break
                elif task_status == "FAIL":
                    print(json.dumps({"error": f"Task failed on server: {poll_data.get('error')}"}))
                    return
            
            if not video_url:
                print(json.dumps({"error": "Task timed out or no video URL returned."}))
                return

            # 3. Download the video
            web_path = await download_file(session, video_url)
            if web_path:
                print(json.dumps({"status": "success", "videos": [web_path]}))
            else:
                print(json.dumps({"error": "Failed to download generated video."}))
                
        except Exception as e:
            print(json.dumps({"error": f"Exception during request: {str(e)}"}))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", help="Text prompt for video generation")
    args = parser.parse_args()
    
    if args.prompt:
        asyncio.run(main(args.prompt))
    else:
        print(json.dumps({"error": "No prompt provided."}))

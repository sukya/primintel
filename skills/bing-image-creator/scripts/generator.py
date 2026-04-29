import sys
import json
import asyncio
import os
from bingart import BingArt

# 定位 resources 文件夹下的 cookies.json
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'cookies.json'))

async def main(prompt):
    # 1. 验证配置文件状态
    if not os.path.exists(CONFIG_PATH):
        print(f"[严重错误] 未找到配置文件，期望位置: {CONFIG_PATH}")
        print("请新建该 resources/cookies.json 文件并在其中存入您的 'auth_cookie_U'。")
        sys.exit(1)
        
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError:
        print(f"[严重错误] JSON 格式解析失败，请检查文件: {CONFIG_PATH}")
        sys.exit(1)
        
    # 从 JSON 或者环境变量中读取 cookie，这里推荐配置时允许环境变量覆盖
    auth_cookie = os.environ.get("BING_AUTH_COOKIE_U") or config.get("auth_cookie_U")
    
    if not auth_cookie:
        print("[严重错误] 'auth_cookie_U' 在 cookies.json 中缺失，且环境变量 BING_AUTH_COOKIE_U 未设置。")
        sys.exit(1)
        
    # 2. 异步调用 Bing DALL-E 3 生成图片
    print(f"[*] 正在尝试连接至 Bing DALL-E 3 接口...")
    print(f"[*] 生成采用的热处理过提示词 (Prompt): '{prompt}'")
    
    try:
        # 实例化 BingArt 进行调用
        async with BingArt(auth_cookie_U=auth_cookie) as bing_art:
            results = await bing_art.generate(prompt)
            print("\n[成功] 图像已成功生成！")
            print("图像结果详情:")
            print(results)
    except Exception as e:
        error_msg = str(e)
        print(f"\n[生成异常] 图像生成过程崩溃，信息反馈: {error_msg}")
        print("\n=== 排障建议指引 ===")
        print("- 若属于 Authentication/Cookie 类别报错：请在浏览器重新捕捉 '_U' 参数覆盖更新 resources/cookies.json。")
        print("- 若属于 Content Policy (内容政策) 报错：你生成的提示词涉嫌违规，请重新斟酌修饰用词。")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法错误，正确用法: python generator.py '<提示词>'")
        sys.exit(1)
    
    input_prompt = sys.argv[1]
    asyncio.run(main(input_prompt))

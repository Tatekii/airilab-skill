#!/usr/bin/env python3
"""
AiriLab 任务状态检查

职责：查询单个任务的状态
"""

import requests
import json
import sys
from pathlib import Path

# 配置路径
CONFIG_DIR = Path.home() / '.openclaw' / 'skills' / 'airilab' / 'config'
TOKEN_FILE = CONFIG_DIR / '.env'

# API 端点
STATUS_URL = "https://cn.airilab.com/api/CrudRouters/getOneRecord"


def get_token():
    """从配置文件获取 Token"""
    if not TOKEN_FILE.exists():
        return None
    
    with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('AIRILAB_API_KEY='):
                return line.split('=', 1)[1].strip()
    return None


def check_status(job_id: str) -> str:
    """
    检查任务状态
    
    返回:
        str: pending, processing, completed, failed
    """
    token = get_token()
    
    if not token:
        print("❌ 未找到 Token")
        return "error"
    
    # 从 job_id 推断 project_id（这里需要改进）
    # 临时使用默认值
    project_id = 190177
    team_id = 0
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "projectId": project_id,
        "teamId": team_id,
        "language": "chs",
        "desiredGenerationId": job_id
    }
    
    try:
        response = requests.post(STATUS_URL, headers=headers, json=payload, timeout=30)
        result = response.json()
        
        if result.get("status") != 200:
            print(f"❌ API 错误：{result.get('message', 'Unknown')}")
            return "error"
        
        data = result.get("data", {})
        models = data.get("projectGenerationModel", [])
        
        if models and models[0].get("projectMedias"):
            # 任务完成
            medias = models[0]["projectMedias"]
            urls = [m["url"] for m in medias]
            print(f"状态：completed")
            print(f"图片数量：{len(medias)}")
            for i, url in enumerate(urls, 1):
                print(f"图片{i}: {url}")
            return "completed"
        else:
            # 任务还在处理中
            print("状态：pending")
            return "pending"
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络错误：{e}")
        return "error"
    except Exception as e:
        print(f"❌ 错误：{e}")
        return "error"


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="检查任务状态")
    parser.add_argument("--job-id", required=True, help="任务 ID")
    
    args = parser.parse_args()
    status = check_status(args.job_id)
    sys.exit(0 if status != "error" else 1)

#!/usr/bin/env python3
"""
AiriLab 任务结果获取

职责：获取已完成任务的输出结果（图片 URL）
"""

import requests
import json
import sys
from pathlib import Path

# 配置路径
CONFIG_DIR = Path.home() / '.openclaw' / 'skills' / 'airilab' / 'config'
TOKEN_FILE = CONFIG_DIR / '.env'
PROJECT_FILE = CONFIG_DIR / 'project_config.json'

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


def get_project_config():
    """获取项目配置"""
    if not PROJECT_FILE.exists():
        return None
    
    try:
        with open(PROJECT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def fetch_result(job_id: str) -> dict:
    """
    获取任务结果
    
    返回:
        dict: {
            'success': bool,
            'output_urls': list,  # 输出图片 URL 列表
            'thumbnail_url': str | None,
            'toolset': str,  # 工作流名称
            'message': str
        }
    """
    token = get_token()
    
    if not token:
        return {
            'success': False,
            'output_urls': [],
            'thumbnail_url': None,
            'toolset': None,
            'message': '未找到 Token，请先登录'
        }
    
    project = get_project_config()
    
    if not project:
        return {
            'success': False,
            'output_urls': [],
            'thumbnail_url': None,
            'toolset': None,
            'message': '未找到项目配置'
        }
    
    project_id = project.get('projectId', 190177)
    team_id = project.get('teamId', 0)
    
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
            return {
                'success': False,
                'output_urls': [],
                'thumbnail_url': None,
                'toolset': None,
                'message': f"API 错误：{result.get('message', 'Unknown')}"
            }
        
        data = result.get("data", {})
        models = data.get("projectGenerationModel", [])
        
        if not models:
            return {
                'success': False,
                'output_urls': [],
                'thumbnail_url': None,
                'toolset': None,
                'message': '未找到任务数据'
            }
        
        model = models[0]
        medias = model.get("projectMedias", [])
        
        if not medias:
            return {
                'success': False,
                'output_urls': [],
                'thumbnail_url': None,
                'toolset': None,
                'message': '任务尚未完成，没有输出图片'
            }
        
        # 提取所有图片 URL
        output_urls = [m["url"] for m in medias]
        
        # 第一张作为缩略图
        thumbnail_url = output_urls[0] if output_urls else None
        
        # 获取工作流名称
        workflow_name = model.get("workflowName", "unknown")
        toolset_map = {
            "MJ": "mj",
            "Upscale": "upscale",
            "Trans": "atmosphere"
        }
        toolset = toolset_map.get(workflow_name.split()[0] if workflow_name else "", "unknown")
        
        return {
            'success': True,
            'output_urls': output_urls,
            'thumbnail_url': thumbnail_url,
            'toolset': toolset,
            'message': f'获取成功，共 {len(output_urls)} 张图片'
        }
            
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'output_urls': [],
            'thumbnail_url': None,
            'toolset': None,
            'message': f'网络错误：{str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'output_urls': [],
            'thumbnail_url': None,
            'toolset': None,
            'message': f'错误：{str(e)}'
        }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="获取任务结果")
    parser.add_argument("--job-id", required=True, help="任务 ID")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                       help="输出格式")
    
    args = parser.parse_args()
    result = fetch_result(args.job_id)
    
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False))
    else:
        if result['success']:
            print(f"✅ {result['message']}")
            print(f"🎨 工具：{result['toolset']}")
            print(f"📷 图片数量：{len(result['output_urls'])}")
            for i, url in enumerate(result['output_urls'], 1):
                print(f"图片{i}: {url}")
            print(f"缩略图：{result['thumbnail_url']}")
        else:
            print(f"❌ {result['message']}")
    
    sys.exit(0 if result['success'] else 1)

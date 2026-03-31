#!/usr/bin/env python3
"""
AiriLab 统一配置管理

功能：
1. Token 管理（加载、保存、验证）
2. 项目配置管理（teamId, projectId, projectName）
3. 统一的配置存储路径
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# 配置目录
CONFIG_DIR = Path.home() / '.openclaw' / 'skills' / 'airilab' / 'config'
TOKEN_FILE = CONFIG_DIR / '.env'
PROJECT_FILE = CONFIG_DIR / 'project_config.json'


class AiriLabConfig:
    """AiriLab 统一配置管理器"""
    
    def __init__(self):
        """初始化配置管理器"""
        # 确保配置目录存在
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # ==================== Token 管理 ====================
    
    def get_token(self) -> Optional[str]:
        """
        获取 Token
        
        返回:
            str: Token，如果不存在则返回 None
        """
        if not TOKEN_FILE.exists():
            return None
        
        try:
            with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('AIRILAB_API_KEY='):
                        return line.split('=', 1)[1].strip()
            return None
        except Exception:
            return None
    
    def save_token(self, token: str, phone: str = "") -> bool:
        """
        保存 Token 到配置文件
        
        参数:
            token: JWT Token
            phone: 手机号（可选）
        
        返回:
            bool: 保存是否成功
        """
        try:
            with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
                f.write("# AiriLab API Token\n")
                f.write(f"AIRILAB_API_KEY={token}\n")
                if phone:
                    f.write(f"AIRILAB_PHONE={phone}\n")
                f.write(f"AIRILAB_UPDATED={datetime.now().isoformat()}\n")
            return True
        except Exception as e:
            print(f"❌ 保存 Token 失败：{e}")
            return False
    
    def clear_token(self) -> bool:
        """
        清除 Token
        
        返回:
            bool: 清除是否成功
        """
        try:
            if TOKEN_FILE.exists():
                TOKEN_FILE.unlink()
            return True
        except Exception as e:
            print(f"❌ 清除 Token 失败：{e}")
            return False
    
    def is_token_valid(self, token: str) -> bool:
        """
        验证 Token 格式和过期时间（解析 JWT payload）
        
        参数:
            token: JWT Token
        
        返回:
            bool: Token 是否有效且未过期
        """
        if not token:
            return False
        
        try:
            import base64
            import json
            
            # JWT Token 应该有 3 个部分
            parts = token.split('.')
            if len(parts) != 3:
                return False
            
            # 解析 payload (第二部分)
            payload = parts[1]
            # 补全 base64 padding
            payload += '=' * (-len(payload) % 4)
            decoded = json.loads(base64.urlsafe_b64decode(payload))
            
            # 检查过期时间
            exp = decoded.get('exp')
            if exp:
                # JWT exp 是秒级时间戳
                expiry = datetime.fromtimestamp(exp)
                if datetime.now() >= expiry:
                    return False  # 已过期
            
            # 长度检查（基本验证）
            if len(token) < 50:
                return False
            
            return True
            
        except Exception:
            # 解析失败，认为无效
            return False
    
    # ==================== 项目管理 ====================
    
    def get_project(self) -> Optional[Dict[str, Any]]:
        """
        获取项目配置
        
        返回:
            dict: 项目配置 {teamId, projectId, projectName}，如果不存在则返回 None
        """
        if not PROJECT_FILE.exists():
            return None
        
        try:
            with open(PROJECT_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 验证必要字段
            required_fields = ['teamId', 'projectId', 'projectName']
            if all(field in config for field in required_fields):
                return config
            else:
                print("⚠️ 配置文件缺少必要字段")
                return None
        except json.JSONDecodeError as e:
            print(f"❌ 配置文件解析错误：{e}")
            return None
        except Exception as e:
            print(f"❌ 加载配置失败：{e}")
            return None
    
    def save_project(self, team_id: int, project_id: int, project_name: str) -> bool:
        """
        保存项目配置
        
        参数:
            team_id: 团队 ID
            project_id: 项目 ID
            project_name: 项目名称
        
        返回:
            bool: 保存是否成功
        """
        config = {
            "teamId": team_id,
            "projectId": project_id,
            "projectName": project_name,
            "selected_at": datetime.now().isoformat()
        }
        
        try:
            with open(PROJECT_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ 保存项目配置失败：{e}")
            return False
    
    def clear_project(self) -> bool:
        """
        清除项目配置
        
        返回:
            bool: 清除是否成功
        """
        try:
            if PROJECT_FILE.exists():
                PROJECT_FILE.unlink()
            return True
        except Exception as e:
            print(f"❌ 清除项目配置失败：{e}")
            return False
    
    # ==================== 综合方法 ====================
    
    def is_fully_configured(self) -> bool:
        """
        检查是否完全配置（Token + 项目）
        
        返回:
            bool: 是否完全配置
        """
        token = self.get_token()
        project = self.get_project()
        
        return token is not None and project is not None
    
    def get_config_status(self) -> Dict[str, Any]:
        """
        获取配置状态
        
        返回:
            dict: 配置状态
        """
        token = self.get_token()
        project = self.get_project()
        
        return {
            "has_token": token is not None,
            "has_project": project is not None,
            "is_ready": self.is_fully_configured(),
            "token_preview": f"{token[:20]}..." if token else None,
            "project": project
        }


# ==================== 命令行入口 ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AiriLab 配置管理")
    parser.add_argument("action", choices=["status", "clear-token", "clear-project", "clear-all"],
                       help="操作类型")
    
    args = parser.parse_args()
    
    config = AiriLabConfig()
    
    if args.action == "status":
        status = config.get_config_status()
        print("📊 AiriLab 配置状态：")
        print(f"   Token: {'✅' if status['has_token'] else '❌'}")
        print(f"   项目：{'✅' if status['has_project'] else '❌'}")
        print(f"   就绪：{'✅' if status['is_ready'] else '❌'}")
        if status['project']:
            print(f"   项目：{status['project']['projectName']} (ID: {status['project']['projectId']})")
    
    elif args.action == "clear-token":
        config.clear_token()
        print("✅ Token 已清除")
    
    elif args.action == "clear-project":
        config.clear_project()
        print("✅ 项目配置已清除")
    
    elif args.action == "clear-all":
        config.clear_token()
        config.clear_project()
        print("✅ 所有配置已清除")

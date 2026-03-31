#!/usr/bin/env python3
"""
AiriLab 统一鉴权管理

整合原 airi-auth 技能的功能：
1. 手机号验证码登录
2. Token 验证和刷新
3. 自动登录流程
"""

import requests
import json
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .config import AiriLabConfig

# API 端点
SEND_OTP_URL = "https://cn.airilab.com/api/Accounts/Login"
VERIFY_CODE_URL = "https://cn.airilab.com/api/Accounts/Login"

# 请求头模板
DEFAULT_HEADERS = {
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,fr;q=0.8",
    "content-type": "application/json",
    "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


class AiriLabAuth:
    """AiriLab 统一鉴权管理器"""
    
    def __init__(self, config: AiriLabConfig = None):
        """
        初始化鉴权管理器
        
        参数:
            config: 配置管理器实例
        """
        self.config = config or AiriLabConfig()
    
    def ensure_authenticated(self) -> Dict[str, Any]:
        """
        确保已认证
        
        返回:
            dict: {
                'authenticated': bool,  # 是否已认证
                'needs_login': bool,     # 是否需要登录
                'token': str | None,     # Token
                'message': str           # 消息
            }
        """
        token = self.config.get_token()
        
        if not token:
            return {
                'authenticated': False,
                'needs_login': True,
                'token': None,
                'message': 'Token 不存在，需要登录'
            }
        
        # 验证 Token 格式
        if not self.config.is_token_valid(token):
            return {
                'authenticated': False,
                'needs_login': True,
                'token': None,
                'message': 'Token 格式无效，需要重新登录'
            }
        
        # 验证 Token 有效性（调用 API）
        if not self.validate_token(token):
            return {
                'authenticated': False,
                'needs_login': True,
                'token': None,
                'message': 'Token 已过期，需要重新登录'
            }
        
        return {
            'authenticated': True,
            'needs_login': False,
            'token': token,
            'message': '已认证'
        }
    
    def validate_token(self, token: str) -> bool:
        """
        验证 Token 有效性
        
        参数:
            token: JWT Token
        
        返回:
            bool: Token 是否有效
        """
        headers = DEFAULT_HEADERS.copy()
        headers["Authorization"] = f"Bearer {token}"
        
        try:
            # 调用一个需要认证的 API 来验证 Token
            response = requests.get(
                "https://cn.airilab.com/api/user/getUserInfo",
                headers=headers,
                timeout=10
            )
            
            # 200 表示有效，403 表示无效
            return response.status_code == 200
        except Exception:
            return False
    
    def send_verification_code(self, phone: str, country_code: str = "+86") -> Dict[str, Any]:
        """
        发送验证码
        
        参数:
            phone: 手机号
            country_code: 国家代码
        
        返回:
            dict: {
                'success': bool,
                'message': str,
                'user_id': int | None
            }
        """
        payload = {
            "phoneNumber": phone,
            "email": "",
            "isAgreedToTerms": True,
            "role": 2,
            "code": "",
            "countryCode": country_code,
            "countryName": "China",
            "openId": "",
            "language": "chs"
        }
        
        headers = DEFAULT_HEADERS.copy()
        headers["origin"] = "http://localhost:3000"
        headers["referer"] = "http://localhost:3000/"
        
        try:
            response = requests.post(
                SEND_OTP_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            result = response.json()
            
            if result.get("status") == 200 and result.get("message") == "Otp sent":
                user_id = result.get("data")
                
                # 保存临时状态
                temp_state = {
                    "pendingPhone": phone,
                    "pendingUserId": user_id,
                    "pendingCountryCode": country_code
                }
                
                return {
                    'success': True,
                    'message': f'验证码已发送至 {phone[:3]}****{phone[-4:]}',
                    'user_id': user_id,
                    'temp_state': temp_state
                }
            else:
                return {
                    'success': False,
                    'message': result.get('message', '发送验证码失败'),
                    'user_id': None
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'网络错误：{str(e)}',
                'user_id': None
            }
    
    def verify_code(self, phone: str, code: str, country_code: str = "+86") -> Dict[str, Any]:
        """
        验证验证码并获取 Token
        
        参数:
            phone: 手机号
            code: 验证码
            country_code: 国家代码
        
        返回:
            dict: {
                'success': bool,
                'token': str | None,
                'message': str,
                'expires_at': int | None
            }
        """
        payload = {
            "phoneNumber": phone,
            "email": "",
            "isAgreedToTerms": True,
            "role": 2,
            "code": code,
            "countryCode": country_code,
            "countryName": "China",
            "openId": "",
            "language": "chs"
        }
        
        headers = DEFAULT_HEADERS.copy()
        headers["origin"] = "https://cn.airilab.com"
        headers["referer"] = "https://cn.airilab.com/stdio/sign-in"
        
        try:
            response = requests.post(
                VERIFY_CODE_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            result = response.json()
            
            if result.get("status") == 200 and result.get("message") == "Success":
                data = result.get("data", {})
                access_token = data.get("accessToken")
                expires_in = data.get("expiresIn", 604800000)  # 7 天
                
                # 计算过期时间
                current_time = datetime.now()
                expires_at = int(current_time.timestamp() * 1000) + expires_in
                
                # 保存 Token
                self.config.save_token(access_token, phone)
                
                return {
                    'success': True,
                    'token': access_token,
                    'message': '登录成功',
                    'expires_at': expires_at,
                    'expires_days': expires_in // (1000 * 60 * 60 * 24)
                }
            else:
                return {
                    'success': False,
                    'message': result.get('message', '验证码错误'),
                    'token': None
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'网络错误：{str(e)}',
                'token': None
            }
    
    def logout(self) -> bool:
        """
        退出登录
        
        返回:
            bool: 是否成功
        """
        return self.config.clear_token()


# ==================== 命令行入口 ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AiriLab 鉴权管理")
    parser.add_argument("action", choices=["status", "login", "logout", "validate"],
                       help="操作类型")
    parser.add_argument("--phone", help="手机号（用于 login）")
    parser.add_argument("--code", help="验证码（用于 login）")
    
    args = parser.parse_args()
    
    auth = AiriLabAuth()
    
    if args.action == "status":
        result = auth.ensure_authenticated()
        print(f"认证状态：{result['message']}")
        if result['authenticated']:
            token_preview = f"{result['token'][:20]}..." if result['token'] else None
            print(f"Token: {token_preview}")
    
    elif args.action == "login":
        if not args.phone:
            print("❌ 错误：login 需要 --phone 参数")
        elif not args.code:
            # 发送验证码
            result = auth.send_verification_code(args.phone)
            print(result['message'])
            if result['success']:
                print("💡 请回复验证码：python3 auth.py login --phone <手机号> --code <验证码>")
        else:
            # 验证验证码
            result = auth.verify_code(args.phone, args.code)
            if result['success']:
                print(f"✅ {result['message']}")
                print(f"📅 有效期：{result['expires_days']} 天")
            else:
                print(f"❌ {result['message']}")
    
    elif args.action == "logout":
        auth.logout()
        print("✅ 已退出登录")
    
    elif args.action == "validate":
        token = auth.config.get_token()
        if token:
            is_valid = auth.validate_token(token)
            print(f"Token 有效性：{'✅ 有效' if is_valid else '❌ 无效'}")
        else:
            print("❌ Token 不存在")

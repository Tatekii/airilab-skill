#!/usr/bin/env python3
"""
AiriLab 配置检查脚本
检查 API Token、项目配置、Python 依赖等前置条件
"""

import json
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from core.config import AiriLabConfig
    from core.auth import AiriLabAuth
except ImportError:
    print("❌ 无法导入核心模块，请确保在正确的目录下运行")
    sys.exit(1)


def check_env_file():
    """检查.env 文件是否存在"""
    config_dir = Path(__file__).resolve().parent.parent / "config"
    env_file = config_dir / ".env"
    
    if not env_file.exists():
        print(f"❌ 配置文件不存在：{env_file}")
        print("   请创建文件并添加以下内容：")
        print("   AIRILAB_API_KEY=your_token_here")
        return False
    
    print(f"✅ 配置文件存在：{env_file}")
    
    # 读取并检查 API Key
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'AIRILAB_API_KEY=' not in content:
        print("❌ 配置文件中缺少 AIRILAB_API_KEY")
        return False
    
    api_key = [line for line in content.split('\n') if line.startswith('AIRILAB_API_KEY=')]
    if api_key:
        key_value = api_key[0].split('=', 1)[1].strip()
        if len(key_value) < 20:
            print("⚠️  API Key 看起来太短，可能无效")
        else:
            print(f"✅ API Key 已配置 (长度：{len(key_value)})")
    
    return True


def check_project_config():
    """检查项目配置文件"""
    config_dir = Path(__file__).resolve().parent.parent / "config"
    project_file = config_dir / "project_config.json"
    
    if not project_file.exists():
        print(f"❌ 项目配置文件不存在：{project_file}")
        print("   请先运行项目选择脚本或手动创建配置")
        return False
    
    print(f"✅ 项目配置文件存在：{project_file}")
    
    try:
        with open(project_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if 'teamId' not in config:
            print("❌ 项目配置中缺少 teamId")
            return False
        if 'projectId' not in config:
            print("❌ 项目配置中缺少 projectId")
            return False
        
        print(f"✅ 团队 ID: {config['teamId']}")
        print(f"✅ 项目 ID: {config['projectId']}")
        print(f"   项目名称：{config.get('projectName', '未知')}")
        return True
    
    except json.JSONDecodeError:
        print("❌ 项目配置文件格式错误")
        return False


def check_dependencies():
    """检查 Python 依赖"""
    print("\n检查 Python 依赖...")
    
    try:
        import requests
        print("✅ requests 已安装")
        return True
    except ImportError:
        print("❌ requests 未安装")
        print("   请运行：pip3 install requests")
        return False


def check_auth():
    """检查认证状态"""
    print("\n检查认证状态...")
    
    try:
        config = AiriLabConfig()
        auth = AiriLabAuth(config)
        result = auth.ensure_authenticated()
        
        if result.get("authenticated"):
            print("✅ 认证有效")
            print(f"   用户：{result.get('user', '未知')}")
            return True
        else:
            print(f"❌ 认证失败：{result.get('message', '未知错误')}")
            print("   请检查 config/.env 中的 API Token 是否有效")
            return False
    
    except Exception as e:
        print(f"❌ 认证检查出错：{e}")
        return False


def main():
    print("=" * 50)
    print("AiriLab Skill 配置检查")
    print("=" * 50)
    print()
    
    results = []
    
    # 检查各项配置
    results.append(("配置文件", check_env_file()))
    results.append(("项目配置", check_project_config()))
    results.append(("Python 依赖", check_dependencies()))
    results.append(("认证状态", check_auth()))
    
    print()
    print("=" * 50)
    print("检查结果汇总")
    print("=" * 50)
    
    all_passed = all(result[1] for result in results)
    
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {'通过' if passed else '失败'}")
    
    print()
    if all_passed:
        print("🎉 所有检查通过！AiriLab Skill 已就绪")
        print()
        print("使用示例:")
        print("  python3 core/api.py --tool mj --prompt \"现代建筑外观\"")
        print("  python3 core/api.py --tool upscale --base-image \"https://...\"")
        print("  python3 core/api.py --tool atmosphere --base-image \"...\" --prompt \"夜晚\"")
        sys.exit(0)
    else:
        print("⚠️  部分检查未通过，请先修复配置问题")
        print()
        print("修复指南:")
        print("  1. 确保 config/.env 包含有效的 AIRILAB_API_KEY")
        print("  2. 确保 config/project_config.json 包含 teamId 和 projectId")
        print("  3. 运行 pip3 install requests 安装依赖")
        sys.exit(1)


if __name__ == "__main__":
    main()

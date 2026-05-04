"""环境检查脚本：确保验证原型可以运行"""
import sys
from pathlib import Path

def check_python_version():
    """检查 Python 版本"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print(f"✅ Python 版本: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python 版本过低: {version.major}.{version.minor}.{version.micro}")
        print("   需要 Python 3.9+")
        return False

def check_dependencies():
    """检查依赖包"""
    required = {
        "anthropic": "anthropic",
        "pydantic": "pydantic",
        "python-dotenv": "dotenv"
    }

    missing = []
    for package_name, import_name in required.items():
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} 未安装")
            missing.append(package_name)

    if missing:
        print(f"\n请运行: pip install {' '.join(missing)}")
        return False
    return True

def check_env_file():
    """检查 .env 文件"""
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        print(f"✅ .env 文件存在")

        # 检查是否有 API key
        with open(env_file, 'r') as f:
            content = f.read()
            if "ANTHROPIC_API_KEY" in content:
                print("✅ ANTHROPIC_API_KEY 已配置")
                return True
            else:
                print("⚠️  ANTHROPIC_API_KEY 未配置（模拟版不需要）")
                return True
    else:
        print(f"⚠️  .env 文件不存在（模拟版不需要）")
        return True

def check_output_dir():
    """检查输出目录"""
    output_dir = Path(__file__).parent.parent / "data" / "prototype_results"
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建输出目录: {output_dir}")
    else:
        print(f"✅ 输出目录存在: {output_dir}")
    return True

def main():
    """同步执行 `main` 对应的业务步骤。

    职责: 位于脚本工具层，负责上述行为，并把相关输入、输出和副作用集中在 `main` 这一入口。
    关键输入: 不接收外部业务参数，依赖当前实例状态、模块配置或调用上下文。
    关键输出: 无返回值；执行结果体现在状态变更、持久化写入、事件推送或上游调用结果中。
    副作用: 不主动修改外部状态；如传入可变对象，可能返回基于其内容计算出的结果。
    异常/边界: 通常不主动抛出业务异常；空值、缺失字段或非法输入按类型约定和上游校验处理。
    """
    print("=" * 60)
    print("环境检查")
    print("=" * 60)
    print()

    checks = [
        ("Python 版本", check_python_version),
        ("依赖包", check_dependencies),
        (".env 文件", check_env_file),
        ("输出目录", check_output_dir),
    ]

    results = []
    for name, check_func in checks:
        print(f"\n检查 {name}:")
        results.append(check_func())

    print("\n" + "=" * 60)
    if all(results):
        print("✅ 所有检查通过！可以运行验证原型。")
        print("\n推荐操作：")
        print("1. 先运行模拟版: python scripts/prototype_mock.py")
        print("2. 模拟版通过后，再运行真实版: python scripts/prototype_continuous_planning.py")
    else:
        print("❌ 部分检查失败，请先解决上述问题。")
    print("=" * 60)

if __name__ == "__main__":
    main()

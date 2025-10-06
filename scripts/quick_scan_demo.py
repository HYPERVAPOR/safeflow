#!/usr/bin/env python
"""
快速扫描演示脚本

演示如何使用 SafeFlow 的适配器进行安全扫描
"""
import sys
import os
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from safeflow.adapters.semgrep_adapter import SemgrepAdapter
from safeflow.adapters.syft_adapter import SyftAdapter


def print_banner():
    """打印横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                    SafeFlow 快速扫描演示                     ║
║              软件代码安全测评智能编排平台 v0.1.0              ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def scan_with_semgrep(target_path: str):
    """使用 Semgrep 进行 SAST 扫描"""
    print("\n" + "="*60)
    print("📊 正在执行 Semgrep 静态代码分析...")
    print("="*60)
    
    try:
        adapter = SemgrepAdapter()
        
        scan_request = {
            "scan_id": "demo_scan_semgrep",
            "target": {
                "type": "LOCAL_PATH",
                "path": target_path
            },
            "options": {
                "rules": "auto"  # 使用自动规则集
            }
        }
        
        vulnerabilities = adapter.run(scan_request)
        
        print(f"\n✅ Semgrep 扫描完成！")
        print(f"📈 发现 {len(vulnerabilities)} 个潜在问题\n")
        
        if vulnerabilities:
            # 按严重度分组统计
            severity_count = {}
            for vuln in vulnerabilities:
                level = vuln.severity.level.value
                severity_count[level] = severity_count.get(level, 0) + 1
            
            print("严重度分布:")
            for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
                count = severity_count.get(level, 0)
                if count > 0:
                    emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", 
                            "LOW": "🟢", "INFO": "ℹ️"}
                    print(f"  {emoji.get(level, '•')} {level}: {count}")
            
            # 显示前 5 个高危漏洞
            high_severity = [v for v in vulnerabilities 
                           if v.severity.level.value in ["CRITICAL", "HIGH"]]
            if high_severity:
                print("\n🔍 高危漏洞示例（前5个）:")
                for i, vuln in enumerate(high_severity[:5], 1):
                    print(f"\n  {i}. {vuln.vulnerability_type.name}")
                    print(f"     位置: {vuln.location.file_path}:{vuln.location.line_start}")
                    print(f"     严重度: {vuln.severity.level.value}")
                    print(f"     描述: {vuln.description.summary[:80]}...")
        
        return vulnerabilities
        
    except Exception as e:
        print(f"❌ Semgrep 扫描失败: {str(e)}")
        return []


def scan_with_syft(target_path: str):
    """使用 Syft 进行 SCA 扫描"""
    print("\n" + "="*60)
    print("📦 正在执行 Syft 软件成分分析...")
    print("="*60)
    
    try:
        adapter = SyftAdapter()
        
        scan_request = {
            "scan_id": "demo_scan_syft",
            "target": {
                "type": "LOCAL_PATH",
                "path": target_path
            }
        }
        
        packages = adapter.run(scan_request)
        
        print(f"\n✅ Syft 扫描完成！")
        print(f"📦 发现 {len(packages)} 个软件包\n")
        
        if packages:
            # 统计包类型
            type_count = {}
            for pkg in packages:
                pkg_type = pkg.source_tool.rule_id
                type_count[pkg_type] = type_count.get(pkg_type, 0) + 1
            
            print("包类型分布:")
            for pkg_type, count in sorted(type_count.items()):
                print(f"  • {pkg_type}: {count}")
            
            print("\n💡 提示: Syft 仅生成 SBOM（软件物料清单）")
            print("   要检测漏洞，请结合 Grype 或其他漏洞数据库使用")
        
        return packages
        
    except Exception as e:
        print(f"❌ Syft 扫描失败: {str(e)}")
        print("💡 提示: 请确保已安装 Syft")
        print("   下载地址: https://github.com/anchore/syft/releases")
        return []


def save_results(semgrep_results, syft_results, output_dir="./demo_results"):
    """保存扫描结果"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存 Semgrep 结果
    if semgrep_results:
        semgrep_file = os.path.join(output_dir, "semgrep_results.json")
        with open(semgrep_file, 'w', encoding='utf-8') as f:
            json.dump(
                [v.model_dump() for v in semgrep_results],
                f,
                indent=2,
                ensure_ascii=False,
                default=str
            )
        print(f"\n💾 Semgrep 结果已保存到: {semgrep_file}")
    
    # 保存 Syft 结果
    if syft_results:
        syft_file = os.path.join(output_dir, "syft_results.json")
        with open(syft_file, 'w', encoding='utf-8') as f:
            json.dump(
                [p.model_dump() for p in syft_results],
                f,
                indent=2,
                ensure_ascii=False,
                default=str
            )
        print(f"💾 Syft 结果已保存到: {syft_file}")


def main():
    """主函数"""
    print_banner()
    
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("❌ 错误: 请提供要扫描的目标路径")
        print("\n用法:")
        print(f"  python {sys.argv[0]} <目标路径>")
        print("\n示例:")
        print(f"  python {sys.argv[0]} /path/to/your/project")
        print(f"  python {sys.argv[0]} ./safeflow")
        sys.exit(1)
    
    target_path = sys.argv[1]
    
    # 验证目标路径
    if not os.path.exists(target_path):
        print(f"❌ 错误: 目标路径不存在: {target_path}")
        sys.exit(1)
    
    print(f"\n🎯 扫描目标: {os.path.abspath(target_path)}")
    print(f"📅 开始时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 执行扫描
    semgrep_results = scan_with_semgrep(target_path)
    syft_results = scan_with_syft(target_path)
    
    # 保存结果
    if semgrep_results or syft_results:
        save_results(semgrep_results, syft_results)
    
    # 总结
    print("\n" + "="*60)
    print("📊 扫描总结")
    print("="*60)
    print(f"✅ Semgrep (SAST): {len(semgrep_results)} 个发现")
    print(f"✅ Syft (SCA): {len(syft_results)} 个软件包")
    print("\n🎉 演示完成！")
    print("\n💡 下一步:")
    print("   1. 查看 ./demo_results/ 目录中的详细结果")
    print("   2. 探索 docs/ 目录了解更多功能")
    print("   3. 阅读 docs/phase1_implementation_guide.md 了解开发指南")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  扫描被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


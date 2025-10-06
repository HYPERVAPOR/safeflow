#!/usr/bin/env python
"""
MCP 客户端测试脚本

在命令行中测试 SafeFlow MCP Server 的所有功能
"""
import sys
import os
import asyncio
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def print_banner():
    """打印横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║              SafeFlow MCP 客户端测试工具                   ║
║              命令行环境下的 MCP 协议测试                   ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_menu():
    """打印菜单"""
    menu = """
请选择测试项目:

1. 🔍 列出所有可用工具
2. 📋 查询工具能力
3. 🔬 执行 Semgrep 扫描
4. 📦 执行 Syft 扫描
5. 🚀 执行全工具扫描
6. 📚 查看扫描历史
7. 📄 读取扫描结果
8. 🧪 运行完整测试套件
9. ❌ 退出

输入数字 (1-9): """
    return input(menu).strip()


async def test_list_tools(client):
    """测试 1: 列出所有工具"""
    print("\n🔍 正在列出所有可用工具...")
    
    try:
        tools = await client.list_tools()
        print(f"\n✅ 发现 {len(tools)} 个 MCP 工具:\n")
        
        for i, tool in enumerate(tools, 1):
            print(f"  {i}. 📦 {tool['name']}")
            print(f"     {tool['description']}")
            print()
        
        return tools
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return []


async def test_tool_capability(client):
    """测试 2: 查询工具能力"""
    print("\n📋 查询工具能力...")
    
    tool_name = input("请输入工具名称 (semgrep/syft): ").strip().lower()
    
    try:
        capability = await client.get_tool_capability(tool_name)
        
        if capability.get("error"):
            print(f"❌ 错误: {capability['error']}")
            return
        
        print(f"\n✅ {tool_name} 工具能力:")
        print(f"   名称: {capability.get('tool_name', 'N/A')}")
        print(f"   版本: {capability.get('tool_version', 'N/A')}")
        print(f"   类型: {capability.get('tool_type', 'N/A')}")
        print(f"   厂商: {capability.get('vendor', 'N/A')}")
        print(f"   描述: {capability.get('description', 'N/A')}")
        
        if 'capabilities' in capability:
            caps = capability['capabilities']
            print(f"   支持语言: {', '.join(caps.get('supported_languages', [])[:5])}...")
            print(f"   检测类型: {', '.join(caps.get('detection_types', [])[:3])}...")
    
    except Exception as e:
        print(f"❌ 错误: {str(e)}")


async def test_semgrep_scan(client):
    """测试 3: Semgrep 扫描"""
    print("\n🔬 执行 Semgrep 扫描...")
    
    target_path = input("请输入目标路径 (默认: ./safeflow): ").strip()
    if not target_path:
        target_path = "./safeflow"
    
    rules = input("请输入规则集 (默认: auto): ").strip()
    if not rules:
        rules = "auto"
    
    print(f"\n⏳ 正在扫描 {target_path}...")
    
    try:
        result = await client.scan_with_semgrep(target_path, rules)
        
        if result.get("success"):
            print(f"\n✅ 扫描完成!")
            print(f"   扫描 ID: {result['scan_id']}")
            print(f"   发现漏洞: {result['vulnerability_count']} 个")
            
            if result['vulnerability_count'] > 0:
                print(f"\n📊 漏洞详情 (前5个):")
                for i, vuln in enumerate(result['vulnerabilities'][:5], 1):
                    print(f"   {i}. {vuln['vulnerability_type']['name']}")
                    print(f"      位置: {vuln['location']['file_path']}:{vuln['location']['line_start']}")
                    print(f"      严重度: {vuln['severity']['level']}")
        else:
            print(f"❌ 扫描失败: {result.get('error')}")
    
    except Exception as e:
        print(f"❌ 错误: {str(e)}")


async def test_syft_scan(client):
    """测试 4: Syft 扫描"""
    print("\n📦 执行 Syft 扫描...")
    
    target_path = input("请输入目标路径 (默认: ./safeflow): ").strip()
    if not target_path:
        target_path = "./safeflow"
    
    print(f"\n⏳ 正在扫描 {target_path}...")
    
    try:
        result = await client.scan_with_syft(target_path)
        
        if result.get("success"):
            print(f"\n✅ 扫描完成!")
            print(f"   扫描 ID: {result['scan_id']}")
            print(f"   发现软件包: {result['package_count']} 个")
            
            if result['package_count'] > 0:
                print(f"\n📊 软件包详情 (前5个):")
                for i, pkg in enumerate(result['packages'][:5], 1):
                    print(f"   {i}. {pkg['vulnerability_type']['name']}")
                    print(f"      类型: {pkg['source_tool']['rule_id']}")
        else:
            print(f"❌ 扫描失败: {result.get('error')}")
    
    except Exception as e:
        print(f"❌ 错误: {str(e)}")


async def test_full_scan(client):
    """测试 5: 全工具扫描"""
    print("\n🚀 执行全工具扫描...")
    
    target_path = input("请输入目标路径 (默认: ./safeflow): ").strip()
    if not target_path:
        target_path = "./safeflow"
    
    print(f"\n⏳ 正在使用所有工具扫描 {target_path}...")
    
    try:
        result = await client.scan_with_all_tools(target_path)
        
        if result.get("success"):
            print(f"\n✅ 全工具扫描完成!")
            print(f"   扫描 ID: {result['scan_id']}")
            
            summary = result.get("summary", {})
            print(f"   总漏洞数: {summary.get('total_vulnerabilities', 0)}")
            print(f"   总软件包: {summary.get('total_packages', 0)}")
            
            print(f"\n🔧 各工具结果:")
            for tool_name, tool_result in result.get("tools", {}).items():
                if tool_result.get("success"):
                    vuln_count = tool_result.get("vulnerability_count", 0)
                    pkg_count = tool_result.get("package_count", 0)
                    print(f"   ✓ {tool_name}: ", end="")
                    if vuln_count > 0:
                        print(f"{vuln_count} 个漏洞")
                    elif pkg_count > 0:
                        print(f"{pkg_count} 个软件包")
                else:
                    print(f"   ✗ {tool_name}: 失败 - {tool_result.get('error')}")
        else:
            print(f"❌ 扫描失败: {result.get('error')}")
    
    except Exception as e:
        print(f"❌ 错误: {str(e)}")


async def test_scan_history(client):
    """测试 6: 查看扫描历史"""
    print("\n📚 查看扫描历史...")
    
    try:
        history = await client.get_scan_history()
        
        if history and "history" in history:
            records = history["history"]
            print(f"\n✅ 发现 {len(records)} 条历史记录:\n")
            
            for i, record in enumerate(records[-10:], 1):  # 最近10条
                print(f"  {i}. 📄 {record['scan_id']}")
                print(f"     工具: {record['tool']}")
                print(f"     路径: {record['target_path']}")
                print(f"     时间: {record['scanned_at']}")
                print(f"     状态: {'✅' if record['success'] else '❌'}")
                print()
        else:
            print("📭 暂无扫描历史")
    
    except Exception as e:
        print(f"❌ 错误: {str(e)}")


async def test_read_results(client):
    """测试 7: 读取扫描结果"""
    print("\n📄 读取扫描结果...")
    
    scan_id = input("请输入扫描 ID: ").strip()
    if not scan_id:
        print("❌ 扫描 ID 不能为空")
        return
    
    try:
        result = await client.get_scan_results(scan_id)
        
        if result.get("error"):
            print(f"❌ 错误: {result['error']}")
            if "available_scans" in result:
                print("可用扫描:")
                for scan in result["available_scans"]:
                    print(f"  - {scan}")
        else:
            print(f"\n✅ 成功读取扫描结果:")
            print(f"   扫描 ID: {result.get('scan_id')}")
            print(f"   工具: {result.get('tool')}")
            print(f"   目标: {result.get('target_path')}")
            print(f"   时间: {result.get('scanned_at')}")
            
            # 保存到文件
            output_file = f"scan_result_{scan_id}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)
            print(f"   结果已保存到: {output_file}")
    
    except Exception as e:
        print(f"❌ 错误: {str(e)}")


async def test_full_suite(client):
    """测试 8: 完整测试套件"""
    print("\n🧪 运行完整测试套件...")
    print("="*60)
    
    tests = [
        ("列出工具", test_list_tools),
        ("查询 Semgrep 能力", lambda c: test_tool_capability_with_name(c, "semgrep")),
        ("查询 Syft 能力", lambda c: test_tool_capability_with_name(c, "syft")),
        ("Semgrep 扫描", lambda c: test_semgrep_scan_auto(c)),
        ("Syft 扫描", lambda c: test_syft_scan_auto(c)),
        ("查看历史", test_scan_history),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 测试: {test_name}")
        try:
            await test_func(client)
            results.append((test_name, "✅ 通过"))
        except Exception as e:
            results.append((test_name, f"❌ 失败: {str(e)}"))
    
    print("\n" + "="*60)
    print("📊 测试结果汇总:")
    for test_name, result in results:
        print(f"  {result} {test_name}")


async def test_tool_capability_with_name(client, tool_name):
    """辅助函数：查询指定工具能力"""
    capability = await client.get_tool_capability(tool_name)
    if not capability.get("error"):
        print(f"✅ {tool_name} 工具可用")


async def test_semgrep_scan_auto(client):
    """辅助函数：自动 Semgrep 扫描"""
    result = await client.scan_with_semgrep("./safeflow", "auto")
    if result.get("success"):
        print(f"✅ Semgrep 扫描成功，发现 {result['vulnerability_count']} 个问题")


async def test_syft_scan_auto(client):
    """辅助函数：自动 Syft 扫描"""
    result = await client.scan_with_syft("./safeflow")
    if result.get("success"):
        print(f"✅ Syft 扫描成功，发现 {result['package_count']} 个软件包")


async def main():
    """主函数"""
    print_banner()
    
    try:
        from safeflow.mcp.client import SafeFlowMCPClient
    except ImportError as e:
        print(f"\n❌ 错误: MCP 客户端导入失败")
        print(f"   {str(e)}")
        print(f"\n请确保已安装 MCP SDK: pip install mcp[cli]")
        sys.exit(1)
    
    print("🔌 正在连接 MCP Server...")
    
    try:
        async with SafeFlowMCPClient() as client:
            print("✅ MCP 连接成功!")
            
            while True:
                choice = print_menu()
                
                if choice == "1":
                    await test_list_tools(client)
                elif choice == "2":
                    await test_tool_capability(client)
                elif choice == "3":
                    await test_semgrep_scan(client)
                elif choice == "4":
                    await test_syft_scan(client)
                elif choice == "5":
                    await test_full_scan(client)
                elif choice == "6":
                    await test_scan_history(client)
                elif choice == "7":
                    await test_read_results(client)
                elif choice == "8":
                    await test_full_suite(client)
                elif choice == "9":
                    print("\n👋 再见!")
                    break
                else:
                    print("❌ 无效选择，请输入 1-9")
                
                input("\n按 Enter 继续...")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 连接失败: {str(e)}")
        print("请确保 MCP Server 可以正常启动")


if __name__ == "__main__":
    asyncio.run(main())

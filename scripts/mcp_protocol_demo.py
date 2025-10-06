#!/usr/bin/env python
"""
真正的 MCP 协议演示

演示如何通过标准的 MCP 协议（JSON-RPC over stdio）调用 SafeFlow 安全工具
"""
import sys
import os
import asyncio
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def print_banner():
    """打印横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║          SafeFlow 真正的 MCP 协议演示                       ║
║    基于官方 MCP Python SDK 实现标准 JSON-RPC 通信           ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


async def demo_mcp_protocol(target_path: str):
    """演示 MCP 协议通信"""
    
    try:
        from safeflow.mcp.client import SafeFlowMCPClient
    except ImportError as e:
        print(f"\n❌ 错误: MCP SDK 未安装")
        print(f"   {str(e)}")
        print(f"\n请运行: pip install mcp[cli]")
        sys.exit(1)
    
    print(f"\n🎯 扫描目标: {os.path.abspath(target_path)}")
    print(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ========================================
    # 步骤 1: 建立 MCP 连接
    # ========================================
    print("\n" + "="*60)
    print("🔌 步骤 1: 建立 MCP 协议连接")
    print("="*60)
    print("  → 启动 MCP Server (stdio 传输)")
    print("  → 建立 JSON-RPC 通信通道")
    print("  → 初始化 MCP 会话")
    
    async with SafeFlowMCPClient() as client:
        print("  ✓ MCP 连接建立成功！")
        
        # ========================================
        # 步骤 2: 发现可用工具（MCP Tools）
        # ========================================
        print("\n" + "="*60)
        print("🔍 步骤 2: 发现可用工具（MCP Tools）")
        print("="*60)
        print("  → 调用 MCP 协议的 tools/list 方法")
        
        tools = await client.list_tools()
        print(f"\n  ✓ 发现 {len(tools)} 个 MCP 工具:\n")
        
        for tool in tools:
            print(f"    📦 {tool['name']}")
            print(f"       {tool['description']}")
        
        # ========================================
        # 步骤 3: 查询工具能力
        # ========================================
        print("\n" + "="*60)
        print("📋 步骤 3: 查询工具能力（通过 MCP Tool 调用）")
        print("="*60)
        
        available_tools = await client.list_available_tools()
        
        if available_tools and "tools" in available_tools:
            for tool_info in available_tools["tools"]:
                print(f"\n  🛠️  {tool_info['name']}:")
                print(f"     类型: {tool_info['type']}")
                print(f"     ID: {tool_info['id']}")
                print(f"     描述: {tool_info['description']}")
                print(f"     支持语言: {', '.join(tool_info['supported_languages'][:5])}...")
        
        # ========================================
        # 步骤 4: 执行安全扫描（MCP Tool 调用）
        # ========================================
        print("\n" + "="*60)
        print("🔬 步骤 4: 执行安全扫描（通过 MCP Protocol）")
        print("="*60)
        print("  → 发送 tools/call JSON-RPC 请求")
        print("  → 工具: scan_with_all_tools")
        print("  → 传输: JSON-RPC 2.0 over stdio")
        
        scan_id = f"mcp_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"\n  ⏳ 正在扫描...")
        result = await client.scan_with_all_tools(target_path, scan_id=scan_id)
        
        if result.get("success"):
            print(f"\n  ✓ 扫描完成！扫描 ID: {result['scan_id']}")
            
            # 显示结果摘要
            summary = result.get("summary", {})
            print(f"\n  📊 扫描摘要:")
            print(f"     总漏洞数: {summary.get('total_vulnerabilities', 0)}")
            print(f"     总软件包: {summary.get('total_packages', 0)}")
            
            # 各工具结果
            print(f"\n  🔧 各工具结果:")
            for tool_name, tool_result in result.get("tools", {}).items():
                if tool_result.get("success"):
                    vuln_count = tool_result.get("vulnerability_count", 0)
                    pkg_count = tool_result.get("package_count", 0)
                    print(f"     • {tool_name}: ", end="")
                    if vuln_count > 0:
                        print(f"{vuln_count} 个发现")
                    elif pkg_count > 0:
                        print(f"{pkg_count} 个软件包")
                else:
                    print(f"     • {tool_name}: 失败 - {tool_result.get('error')}")
        else:
            print(f"\n  ✗ 扫描失败: {result.get('error')}")
        
        # ========================================
        # 步骤 5: 访问资源（MCP Resources）
        # ========================================
        print("\n" + "="*60)
        print("📚 步骤 5: 访问 MCP 资源（Resources）")
        print("="*60)
        print("  → 调用 MCP 协议的 resources/read 方法")
        
        resources = await client.list_resources()
        print(f"\n  ✓ 发现 {len(resources)} 个 MCP 资源:\n")
        
        for resource in resources:
            print(f"    📄 {resource['uri']}")
            if resource.get('description'):
                print(f"       {resource['description']}")
        
        # 读取扫描历史
        print(f"\n  → 读取资源: scan://history")
        history = await client.get_scan_history()
        
        if history and "history" in history:
            print(f"\n  📜 扫描历史记录:")
            for record in history["history"][-5:]:  # 最近5条
                print(f"     • {record['scan_id']}")
                print(f"       工具: {record['tool']}, 时间: {record['scanned_at']}")
        
        # 读取本次扫描结果
        print(f"\n  → 读取资源: scan://results/{scan_id}")
        scan_result = await client.get_scan_results(scan_id)
        
        if scan_result and not scan_result.get("error"):
            print(f"  ✓ 成功读取扫描结果")
            
            # 保存完整结果
            output_dir = "./mcp_protocol_results"
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f"{scan_id}.json")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(scan_result, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"  💾 完整结果已保存到: {output_file}")


def main():
    """主函数"""
    print_banner()
    
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("❌ 错误: 请提供要扫描的目标路径")
        print("\n用法:")
        print(f"  python {sys.argv[0]} <目标路径>")
        print("\n示例:")
        print(f"  python {sys.argv[0]} ./safeflow")
        sys.exit(1)
    
    target_path = sys.argv[1]
    
    # 验证目标路径
    if not os.path.exists(target_path):
        print(f"❌ 错误: 目标路径不存在: {target_path}")
        sys.exit(1)
    
    try:
        # 运行异步演示
        asyncio.run(demo_mcp_protocol(target_path))
        
        # 总结
        print("\n" + "="*60)
        print("✅ MCP 协议演示完成！")
        print("="*60)
        
        print("\n🎯 关键特性展示:")
        print("  ✓ 标准 MCP 协议通信（JSON-RPC 2.0）")
        print("  ✓ MCP Tools（工具调用）")
        print("  ✓ MCP Resources（资源访问）")
        print("  ✓ stdio 传输（可扩展到 HTTP/SSE）")
        print("  ✓ 会话管理和状态保持")
        
        print("\n📊 与之前实现的对比:")
        print("  传统: 服务层 → 适配器 → CLI 工具")
        print("  MCP:  客户端 → JSON-RPC → MCP Server → 工具")
        
        print("\n🔗 MCP 协议优势:")
        print("  • 标准化的通信协议")
        print("  • 可与任何支持 MCP 的客户端集成")
        print("  • 支持 LLM 直接调用（Claude Desktop 等）")
        print("  • 跨语言、跨平台互操作")
        
        print("\n💡 如何与 LLM 集成:")
        print("  1. 在 Claude Desktop 配置文件中注册此 MCP Server")
        print("  2. LLM 可以直接调用 SafeFlow 的安全扫描工具")
        print("  3. 实现智能化的安全分析和修复建议")
        
        print("\n📚 相关文档:")
        print("  • docs/MCP_COMPLETE_GUIDE.md")
        print("  • https://modelcontextprotocol.io")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  演示被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


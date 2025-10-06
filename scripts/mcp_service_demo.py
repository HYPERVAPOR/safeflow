#!/usr/bin/env python
"""
MCP 风格的服务化调用演示

演示如何使用 SafeFlow 的 MCP 风格服务层进行工具调用
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from safeflow.adapters.semgrep_adapter import SemgrepAdapter
from safeflow.adapters.syft_adapter import SyftAdapter
from safeflow.services.tool_registry import ToolRegistry
from safeflow.services.tool_service import ToolService, ScanRequest


def print_banner():
    """打印横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║            SafeFlow MCP 服务化调用演示                      ║
║        展示工具注册中心和统一调用接口的使用                  ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def demo_tool_registration():
    """演示 1: 工具注册和服务发现"""
    print("\n" + "="*60)
    print("📝 演示 1: 工具注册和服务发现（MCP 风格）")
    print("="*60)
    
    # 创建注册中心
    registry = ToolRegistry()
    print("\n✅ 步骤 1: 创建工具注册中心")
    
    # 注册工具
    print("\n✅ 步骤 2: 注册工具...")
    try:
        semgrep = SemgrepAdapter()
        registry.register(semgrep)
        print(f"  ✓ 已注册: {semgrep.tool_name} ({semgrep.tool_id})")
    except Exception as e:
        print(f"  ✗ Semgrep 注册失败: {str(e)}")
    
    try:
        syft = SyftAdapter()
        registry.register(syft)
        print(f"  ✓ 已注册: {syft.tool_name} ({syft.tool_id})")
    except Exception as e:
        print(f"  ✗ Syft 注册失败: {str(e)}")
    
    # 服务发现
    print("\n✅ 步骤 3: 服务发现（MCP 能力查询）")
    
    # 按类型发现
    from safeflow.schemas.tool_capability import ToolType
    sast_tools = registry.discover_by_type(ToolType.SAST)
    print(f"\n  🔍 SAST 工具: {len(sast_tools)} 个")
    for tool in sast_tools:
        print(f"    - {tool.tool_name} (支持 {len(tool.capabilities.supported_languages)} 种语言)")
    
    sca_tools = registry.discover_by_type(ToolType.SCA)
    print(f"\n  🔍 SCA 工具: {len(sca_tools)} 个")
    for tool in sca_tools:
        print(f"    - {tool.tool_name}")
    
    # 按语言发现
    python_tools = registry.discover_by_language("python")
    print(f"\n  🔍 支持 Python 的工具: {len(python_tools)} 个")
    for tool in python_tools:
        print(f"    - {tool.tool_name} ({tool.tool_type.value})")
    
    # 注册中心摘要
    summary = registry.get_summary()
    print(f"\n📊 注册中心摘要:")
    print(f"  总工具数: {summary['total_tools']}")
    print(f"  类型分布: {summary['type_distribution']}")
    
    return registry


def demo_unified_calling(registry: ToolRegistry, target_path: str):
    """演示 2: MCP 风格的统一调用"""
    print("\n" + "="*60)
    print("🎯 演示 2: MCP 风格的统一工具调用")
    print("="*60)
    
    # 创建工具服务
    service = ToolService(registry)
    print("\n✅ 步骤 1: 创建工具服务")
    
    # 列出可用工具
    print("\n✅ 步骤 2: 列出所有可用工具")
    available_tools = service.list_available_tools()
    for tool in available_tools:
        print(f"  - {tool.tool_name} ({tool.tool_id})")
    
    # 创建扫描请求
    scan_id = f"mcp_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    scan_request = ScanRequest(
        scan_id=scan_id,
        target_path=target_path,
        tool_ids=[],  # 空列表表示使用所有工具
        options={"rules": "auto"}
    )
    
    print(f"\n✅ 步骤 3: 创建扫描请求")
    print(f"  扫描 ID: {scan_id}")
    print(f"  目标路径: {target_path}")
    
    # 执行多工具扫描
    print(f"\n✅ 步骤 4: 执行多工具扫描（MCP 统一调用）")
    responses = service.scan_with_multiple_tools(scan_request)
    
    # 显示结果
    print(f"\n📊 扫描结果:")
    for response in responses:
        status = "✓" if response.success else "✗"
        print(f"\n  {status} {response.tool_id}:")
        if response.success:
            print(f"    发现 {len(response.vulnerabilities)} 个问题")
            print(f"    工具类型: {response.metadata.get('tool_type')}")
        else:
            print(f"    错误: {response.error}")
    
    return responses


def demo_result_aggregation(service: ToolService, responses):
    """演示 3: 结果聚合"""
    print("\n" + "="*60)
    print("📊 演示 3: 多工具结果聚合")
    print("="*60)
    
    # 聚合结果
    aggregated = service.aggregate_results(responses)
    
    print(f"\n总体统计:")
    print(f"  总漏洞数: {aggregated['total_vulnerabilities']}")
    print(f"  成功扫描: {aggregated['successful_scans']}")
    print(f"  失败扫描: {aggregated['failed_scans']}")
    
    print(f"\n严重度分布:")
    for level, count in aggregated['severity_distribution'].items():
        emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", 
                "LOW": "🟢", "INFO": "ℹ️"}
        print(f"  {emoji.get(level, '•')} {level}: {count}")
    
    print(f"\n工具贡献度:")
    for tool_id, count in aggregated['tool_distribution'].items():
        print(f"  • {tool_id}: {count} 个发现")
    
    return aggregated


def demo_capability_query(registry: ToolRegistry):
    """演示 4: 能力查询（MCP 协议核心功能）"""
    print("\n" + "="*60)
    print("🔍 演示 4: 工具能力查询（MCP 核心功能）")
    print("="*60)
    
    tool_ids = registry.get_tool_ids()
    
    for tool_id in tool_ids:
        capability = registry.get_capability(tool_id)
        if capability:
            print(f"\n📋 {capability.tool_name} 能力详情:")
            print(f"  ID: {capability.tool_id}")
            print(f"  类型: {capability.tool_type.value}")
            print(f"  版本: {capability.tool_version}")
            print(f"  厂商: {capability.vendor}")
            print(f"  支持语言: {', '.join(capability.capabilities.supported_languages[:5])}...")
            print(f"  检测类型: {', '.join(capability.capabilities.detection_types[:3])}...")
            print(f"  超时设置: {capability.execution.timeout_seconds}秒")
            print(f"  许可证: {capability.metadata.license}")


def save_mcp_results(responses, output_dir="./mcp_demo_results"):
    """保存MCP风格的扫描结果"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存完整响应
    responses_data = []
    for response in responses:
        response_dict = response.to_dict()
        response_dict['vulnerabilities'] = [
            v.model_dump() for v in response.vulnerabilities
        ]
        responses_data.append(response_dict)
    
    output_file = os.path.join(output_dir, "mcp_scan_results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(responses_data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 MCP 扫描结果已保存到: {output_file}")


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
    
    print(f"\n🎯 扫描目标: {os.path.abspath(target_path)}")
    print(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 演示 1: 工具注册和服务发现
        registry = demo_tool_registration()
        
        # 演示 2: MCP 风格的统一调用
        responses = demo_unified_calling(registry, target_path)
        
        # 演示 3: 结果聚合
        service = ToolService(registry)
        demo_result_aggregation(service, responses)
        
        # 演示 4: 能力查询
        demo_capability_query(registry)
        
        # 保存结果
        save_mcp_results(responses)
        
        # 总结
        print("\n" + "="*60)
        print("✅ MCP 服务化调用演示完成！")
        print("="*60)
        
        print("\n🎯 关键特性演示:")
        print("  ✓ 工具注册中心（统一管理）")
        print("  ✓ 服务发现机制（按类型/语言查询）")
        print("  ✓ 统一调用接口（标准化请求/响应）")
        print("  ✓ 能力动态查询（MCP 核心功能）")
        print("  ✓ 多工具协同调用")
        print("  ✓ 结果自动聚合")
        
        print("\n💡 对比传统方式:")
        print("  传统: 直接调用 CLI → 手动解析 → 分散管理")
        print("  MCP:  注册中心 → 统一接口 → 标准化响应 → 自动聚合")
        
        print("\n📚 下一步:")
        print("  1. 查看 docs/MCP_INTEGRATION_GUIDE.md 了解MCP集成指南")
        print("  2. 探索 safeflow/services/ 目录的服务层实现")
        print("  3. 阅读代码注释了解设计思路")
        
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


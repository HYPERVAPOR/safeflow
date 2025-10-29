"""
SafeFlow MCP Server 实现

基于官方 MCP Python SDK 将 SafeFlow 安全工具包装为 MCP 服务器
"""
import json
from typing import Any, Optional, List, Dict
from datetime import datetime

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("警告: MCP SDK 未安装，请运行: pip install mcp[cli]")
    FastMCP = None

from safeflow.adapters.semgrep_adapter import SemgrepAdapter
from safeflow.adapters.syft_adapter import SyftAdapter
from safeflow.adapters.base import BaseAdapter, AdapterError


# 全局存储扫描结果（实际应用中应使用数据库）
_scan_results: Dict[str, Any] = {}


def create_safeflow_mcp_server() -> "FastMCP":
    """
    创建 SafeFlow MCP Server
    
    将 Semgrep 和 Syft 工具包装为符合 MCP 协议的服务器
    
    Returns:
        FastMCP 服务器实例
    """
    if FastMCP is None:
        raise ImportError("MCP SDK 未安装，请运行: pip install mcp[cli]")
    
    # 创建 MCP 服务器
    mcp = FastMCP("SafeFlow Security Scanner")
    
    # 初始化适配器
    semgrep_adapter = None
    syft_adapter = None
    
    try:
        semgrep_adapter = SemgrepAdapter()
    except Exception as e:
        print(f"警告: Semgrep 初始化失败: {e}")
    
    try:
        syft_adapter = SyftAdapter()
    except Exception as e:
        print(f"警告: Syft 初始化失败: {e}")
    
    # ========================================
    # Tools: 工具定义（MCP 核心功能）
    # ========================================
    
    @mcp.tool()
    def scan_with_semgrep(
        target_path: str,
        rules: str = "auto",
        scan_id: Optional[str] = None,
        fast_mode: bool = False
    ) -> str:
        """
        使用 Semgrep 进行静态代码分析（SAST）
        
        Args:
            target_path: 要扫描的目标路径
            rules: Semgrep 规则集（如 'auto', 'p/security-audit'），支持逗号分隔多个规则
            scan_id: 可选的扫描 ID，用于追踪
            fast_mode: 快速模式，跳过大文件和常见目录（推荐用于大型项目）
            
        Returns:
            扫描结果的 JSON 字符串
        """
        if semgrep_adapter is None:
            return json.dumps({
                "error": "Semgrep 不可用",
                "success": False
            })
        
        if scan_id is None:
            scan_id = f"semgrep_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # 构建扫描选项
            options = {
                "rules": rules
            }
            
            # 快速模式：优化大型项目扫描
            if fast_mode:
                options["max_target_bytes"] = 1000000  # 限制单文件最大 1MB
                options["jobs"] = 4  # 并发扫描
            
            scan_request = {
                "scan_id": scan_id,
                "target": {
                    "type": "LOCAL_PATH",
                    "path": target_path
                },
                "options": options
            }
            
            vulnerabilities = semgrep_adapter.run(scan_request)
            
            # 存储结果
            result = {
                "success": True,
                "scan_id": scan_id,
                "tool": "semgrep",
                "target_path": target_path,
                "vulnerability_count": len(vulnerabilities),
                "vulnerabilities": [v.model_dump() for v in vulnerabilities],
                "scanned_at": datetime.now().isoformat()
            }
            
            _scan_results[scan_id] = result
            
            return json.dumps(result, default=str, ensure_ascii=False)
            
        except AdapterError as e:
            return json.dumps({
                "error": str(e),
                "success": False,
                "scan_id": scan_id
            })
    
    @mcp.tool()
    def scan_with_syft(
        target_path: str,
        scan_id: Optional[str] = None
    ) -> str:
        """
        使用 Syft 进行软件成分分析（SCA）
        
        Args:
            target_path: 要扫描的目标路径
            scan_id: 可选的扫描 ID，用于追踪
            
        Returns:
            扫描结果的 JSON 字符串
        """
        if syft_adapter is None:
            return json.dumps({
                "error": "Syft 不可用",
                "success": False
            })
        
        if scan_id is None:
            scan_id = f"syft_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            scan_request = {
                "scan_id": scan_id,
                "target": {
                    "type": "LOCAL_PATH",
                    "path": target_path
                }
            }
            
            packages = syft_adapter.run(scan_request)
            
            # 存储结果
            result = {
                "success": True,
                "scan_id": scan_id,
                "tool": "syft",
                "target_path": target_path,
                "package_count": len(packages),
                "packages": [p.model_dump() for p in packages],
                "scanned_at": datetime.now().isoformat()
            }
            
            _scan_results[scan_id] = result
            
            return json.dumps(result, default=str, ensure_ascii=False)
            
        except AdapterError as e:
            return json.dumps({
                "error": str(e),
                "success": False,
                "scan_id": scan_id
            })
    
    @mcp.tool()
    def scan_with_all_tools(
        target_path: str,
        scan_id: Optional[str] = None
    ) -> str:
        """
        使用所有可用工具进行全面扫描
        
        Args:
            target_path: 要扫描的目标路径
            scan_id: 可选的扫描 ID，用于追踪
            
        Returns:
            所有工具的扫描结果汇总
        """
        if scan_id is None:
            scan_id = f"full_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        results = {
            "success": True,
            "scan_id": scan_id,
            "target_path": target_path,
            "tools": {},
            "scanned_at": datetime.now().isoformat()
        }
        
        # 运行 Semgrep
        if semgrep_adapter:
            try:
                semgrep_result = json.loads(
                    scan_with_semgrep(target_path, scan_id=f"{scan_id}_semgrep")
                )
                results["tools"]["semgrep"] = semgrep_result
            except Exception as e:
                results["tools"]["semgrep"] = {"error": str(e)}
        
        # 运行 Syft
        if syft_adapter:
            try:
                syft_result = json.loads(
                    scan_with_syft(target_path, scan_id=f"{scan_id}_syft")
                )
                results["tools"]["syft"] = syft_result
            except Exception as e:
                results["tools"]["syft"] = {"error": str(e)}
        
        # 汇总统计
        total_vulns = 0
        total_packages = 0
        
        if "semgrep" in results["tools"] and results["tools"]["semgrep"].get("success"):
            total_vulns += results["tools"]["semgrep"].get("vulnerability_count", 0)
        
        if "syft" in results["tools"] and results["tools"]["syft"].get("success"):
            total_packages += results["tools"]["syft"].get("package_count", 0)
        
        results["summary"] = {
            "total_vulnerabilities": total_vulns,
            "total_packages": total_packages
        }
        
        _scan_results[scan_id] = results
        
        return json.dumps(results, default=str, ensure_ascii=False)
    
    @mcp.tool()
    def get_tool_capability(tool_name: str) -> str:
        """
        获取指定工具的能力声明
        
        Args:
            tool_name: 工具名称（'semgrep' 或 'syft'）
            
        Returns:
            工具能力声明的 JSON 字符串
        """
        tool_name = tool_name.lower()
        
        if tool_name == "semgrep" and semgrep_adapter:
            capability = semgrep_adapter.get_capability()
            return json.dumps(capability.model_dump(), default=str, ensure_ascii=False)
        
        elif tool_name == "syft" and syft_adapter:
            capability = syft_adapter.get_capability()
            return json.dumps(capability.model_dump(), default=str, ensure_ascii=False)
        
        else:
            return json.dumps({
                "error": f"工具 '{tool_name}' 不存在或不可用",
                "available_tools": []
            })
    
    @mcp.tool()
    def list_available_tools() -> str:
        """
        列出所有可用的安全扫描工具
        
        Returns:
            可用工具列表的 JSON 字符串
        """
        tools = []
        
        if semgrep_adapter:
            cap = semgrep_adapter.get_capability()
            tools.append({
                "name": cap.tool_name,
                "id": cap.tool_id,
                "type": cap.tool_type.value,
                "description": cap.description,
                "supported_languages": cap.capabilities.supported_languages
            })
        
        if syft_adapter:
            cap = syft_adapter.get_capability()
            tools.append({
                "name": cap.tool_name,
                "id": cap.tool_id,
                "type": cap.tool_type.value,
                "description": cap.description,
                "supported_languages": cap.capabilities.supported_languages
            })
        
        return json.dumps({"tools": tools}, ensure_ascii=False)
    
    # ========================================
    # Resources: 资源定义（MCP 核心功能）
    # ========================================
    
    @mcp.resource("scan://results/{scan_id}")
    def get_scan_results(scan_id: str) -> str:
        """
        获取指定扫描的结果
        
        Args:
            scan_id: 扫描 ID
            
        Returns:
            扫描结果的 JSON 字符串
        """
        if scan_id in _scan_results:
            return json.dumps(_scan_results[scan_id], default=str, ensure_ascii=False)
        else:
            return json.dumps({
                "error": f"扫描结果不存在: {scan_id}",
                "available_scans": list(_scan_results.keys())
            })
    
    @mcp.resource("scan://history")
    def get_scan_history() -> str:
        """
        获取所有扫描历史记录
        
        Returns:
            扫描历史的 JSON 字符串
        """
        history = []
        for scan_id, result in _scan_results.items():
            history.append({
                "scan_id": scan_id,
                "tool": result.get("tool", "multiple"),
                "target_path": result.get("target_path"),
                "scanned_at": result.get("scanned_at"),
                "success": result.get("success", False)
            })
        
        return json.dumps({"history": history}, default=str, ensure_ascii=False)
    
    return mcp


# ========================================
# 独立运行模式
# ========================================

def run_server():
    """运行 MCP Server（stdio 模式）"""
    mcp = create_safeflow_mcp_server()
    mcp.run()


if __name__ == "__main__":
    run_server()


"""
SafeFlow MCP Client 实现

用于连接和调用 SafeFlow MCP Server
"""
import json
from typing import Any, Dict, Optional, List
import subprocess
import sys

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("警告: MCP SDK 未安装，请运行: pip install mcp[cli]")
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None


class SafeFlowMCPClient:
    """
    SafeFlow MCP 客户端
    
    用于通过 MCP 协议调用 SafeFlow 安全扫描工具
    """
    
    def __init__(self, server_script_path: Optional[str] = None):
        """
        初始化 MCP 客户端
        
        Args:
            server_script_path: MCP 服务器脚本路径，默认使用内置服务器
        """
        if ClientSession is None:
            raise ImportError("MCP SDK 未安装，请运行: pip install mcp[cli]")
        
        self.server_script_path = server_script_path
        self.session: Optional[ClientSession] = None
        self._read = None
        self._write = None
        self._stdio_context = None
        self._session_context = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
    
    async def connect(self):
        """连接到 MCP 服务器"""
        if self.server_script_path is None:
            # 使用内置服务器
            import safeflow.mcp.server as server_module
            server_path = server_module.__file__
        else:
            server_path = self.server_script_path
        
        # 创建服务器参数
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "safeflow.mcp.server"],
            env=None
        )
        
        # 建立连接 - stdio_client 是异步上下文管理器
        self._stdio_context = stdio_client(server_params)
        self._read, self._write = await self._stdio_context.__aenter__()
        
        # 创建会话
        self._session_context = ClientSession(self._read, self._write)
        self.session = await self._session_context.__aenter__()
        
        # 初始化会话
        await self.session.initialize()
        
        return self
    
    async def close(self):
        """关闭连接"""
        # 关闭会话
        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
            self._session_context = None
            self.session = None
        
        # 关闭 stdio 连接
        if self._stdio_context:
            await self._stdio_context.__aexit__(None, None, None)
            self._stdio_context = None
            self._read = None
            self._write = None
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        列出所有可用工具
        
        Returns:
            工具列表
        """
        if not self.session:
            raise RuntimeError("客户端未连接，请先调用 connect()")
        
        tools = await self.session.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            }
            for tool in tools.tools
        ]
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """
        列出所有可用资源
        
        Returns:
            资源列表
        """
        if not self.session:
            raise RuntimeError("客户端未连接，请先调用 connect()")
        
        resources = await self.session.list_resources()
        return [
            {
                "uri": resource.uri,
                "name": resource.name,
                "description": resource.description
            }
            for resource in resources.resources
        ]
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        调用工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        if not self.session:
            raise RuntimeError("客户端未连接，请先调用 connect()")
        
        result = await self.session.call_tool(tool_name, arguments)
        
        # 解析结果
        if result.content:
            content = result.content[0]
            if hasattr(content, 'text'):
                try:
                    return json.loads(content.text)
                except json.JSONDecodeError:
                    return content.text
        
        return None
    
    async def read_resource(self, uri: str) -> Any:
        """
        读取资源
        
        Args:
            uri: 资源 URI
            
        Returns:
            资源内容
        """
        if not self.session:
            raise RuntimeError("客户端未连接，请先调用 connect()")
        
        result = await self.session.read_resource(uri)
        
        # 解析结果
        if result.contents:
            content = result.contents[0]
            if hasattr(content, 'text'):
                try:
                    return json.loads(content.text)
                except json.JSONDecodeError:
                    return content.text
        
        return None
    
    # ========================================
    # 便捷方法（封装常用操作）
    # ========================================
    
    async def scan_with_semgrep(
        self,
        target_path: str,
        rules: str = "auto",
        scan_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        使用 Semgrep 扫描
        
        Args:
            target_path: 目标路径
            rules: 规则集
            scan_id: 扫描 ID
            
        Returns:
            扫描结果
        """
        arguments = {
            "target_path": target_path,
            "rules": rules
        }
        if scan_id:
            arguments["scan_id"] = scan_id
        
        return await self.call_tool("scan_with_semgrep", arguments)
    
    async def scan_with_syft(
        self,
        target_path: str,
        scan_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        使用 Syft 扫描
        
        Args:
            target_path: 目标路径
            scan_id: 扫描 ID
            
        Returns:
            扫描结果
        """
        arguments = {"target_path": target_path}
        if scan_id:
            arguments["scan_id"] = scan_id
        
        return await self.call_tool("scan_with_syft", arguments)
    
    async def scan_with_all_tools(
        self,
        target_path: str,
        scan_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        使用所有工具扫描
        
        Args:
            target_path: 目标路径
            scan_id: 扫描 ID
            
        Returns:
            扫描结果
        """
        arguments = {"target_path": target_path}
        if scan_id:
            arguments["scan_id"] = scan_id
        
        return await self.call_tool("scan_with_all_tools", arguments)
    
    async def get_tool_capability(self, tool_name: str) -> Dict[str, Any]:
        """
        获取工具能力
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具能力声明
        """
        return await self.call_tool("get_tool_capability", {"tool_name": tool_name})
    
    async def list_available_tools(self) -> Dict[str, Any]:
        """
        列出可用工具
        
        Returns:
            工具列表
        """
        return await self.call_tool("list_available_tools", {})
    
    async def get_scan_results(self, scan_id: str) -> Dict[str, Any]:
        """
        获取扫描结果
        
        Args:
            scan_id: 扫描 ID
            
        Returns:
            扫描结果
        """
        uri = f"scan://results/{scan_id}"
        return await self.read_resource(uri)
    
    async def get_scan_history(self) -> Dict[str, Any]:
        """
        获取扫描历史
        
        Returns:
            扫描历史
        """
        return await self.read_resource("scan://history")


# ========================================
# 便捷函数
# ========================================

async def create_client(server_script_path: Optional[str] = None) -> SafeFlowMCPClient:
    """
    创建并连接 MCP 客户端
    
    Args:
        server_script_path: 服务器脚本路径
        
    Returns:
        已连接的客户端实例
    """
    client = SafeFlowMCPClient(server_script_path)
    await client.connect()
    return client


"""
工具注册中心

提供 MCP 风格的工具服务发现和管理
"""
from typing import Dict, List, Optional
from loguru import logger

from safeflow.adapters.base import BaseAdapter
from safeflow.schemas.tool_capability import ToolCapability, ToolType


class ToolRegistry:
    """
    工具注册中心 - MCP 风格的服务发现
    
    功能：
    1. 工具注册和注销
    2. 能力查询和发现
    3. 工具实例管理
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseAdapter] = {}
        self._capabilities: Dict[str, ToolCapability] = {}
        logger.info("ToolRegistry 初始化完成")
    
    def register(self, adapter: BaseAdapter) -> None:
        """
        注册工具（基于 MCP 能力声明）
        
        Args:
            adapter: 工具适配器实例
            
        Raises:
            ValueError: 如果工具 ID 已存在
        """
        capability = adapter.get_capability()
        tool_id = capability.tool_id
        
        if tool_id in self._tools:
            logger.warning(f"工具 {tool_id} 已注册，将被覆盖")
        
        self._tools[tool_id] = adapter
        self._capabilities[tool_id] = capability
        
        logger.info(
            f"工具注册成功: {capability.tool_name} "
            f"(ID: {tool_id}, Type: {capability.tool_type.value})"
        )
    
    def unregister(self, tool_id: str) -> bool:
        """
        注销工具
        
        Args:
            tool_id: 工具唯一标识
            
        Returns:
            是否成功注销
        """
        if tool_id in self._tools:
            del self._tools[tool_id]
            del self._capabilities[tool_id]
            logger.info(f"工具已注销: {tool_id}")
            return True
        else:
            logger.warning(f"工具不存在: {tool_id}")
            return False
    
    def get_adapter(self, tool_id: str) -> Optional[BaseAdapter]:
        """
        获取工具适配器实例
        
        Args:
            tool_id: 工具唯一标识
            
        Returns:
            适配器实例，如果不存在则返回 None
        """
        return self._tools.get(tool_id)
    
    def get_capability(self, tool_id: str) -> Optional[ToolCapability]:
        """
        获取工具能力声明（MCP 能力查询）
        
        Args:
            tool_id: 工具唯一标识
            
        Returns:
            工具能力声明，如果不存在则返回 None
        """
        return self._capabilities.get(tool_id)
    
    def discover_by_type(self, tool_type: ToolType) -> List[ToolCapability]:
        """
        按类型发现可用工具（MCP 服务发现）
        
        Args:
            tool_type: 工具类型（SAST, DAST, SCA 等）
            
        Returns:
            匹配的工具能力声明列表
        """
        capabilities = [
            cap for cap in self._capabilities.values()
            if cap.tool_type == tool_type
        ]
        
        logger.info(f"发现 {len(capabilities)} 个 {tool_type.value} 类型的工具")
        return capabilities
    
    def discover_by_language(self, language: str) -> List[ToolCapability]:
        """
        按支持的语言发现工具
        
        Args:
            language: 编程语言（如 python, java）
            
        Returns:
            支持该语言的工具能力声明列表
        """
        capabilities = [
            cap for cap in self._capabilities.values()
            if language.lower() in [lang.lower() for lang in cap.capabilities.supported_languages]
        ]
        
        logger.info(f"发现 {len(capabilities)} 个支持 {language} 的工具")
        return capabilities
    
    def discover_by_detection_type(self, detection_type: str) -> List[ToolCapability]:
        """
        按检测类型发现工具
        
        Args:
            detection_type: 检测类型（如 sql_injection, xss）
            
        Returns:
            支持该检测类型的工具能力声明列表
        """
        capabilities = [
            cap for cap in self._capabilities.values()
            if detection_type.lower() in [dt.lower() for dt in cap.capabilities.detection_types]
        ]
        
        logger.info(f"发现 {len(capabilities)} 个支持 {detection_type} 检测的工具")
        return capabilities
    
    def list_all(self) -> List[ToolCapability]:
        """
        列出所有已注册的工具
        
        Returns:
            所有工具的能力声明列表
        """
        return list(self._capabilities.values())
    
    def get_tool_count(self) -> int:
        """获取已注册工具数量"""
        return len(self._tools)
    
    def get_tool_ids(self) -> List[str]:
        """获取所有工具 ID 列表"""
        return list(self._tools.keys())
    
    def is_registered(self, tool_id: str) -> bool:
        """检查工具是否已注册"""
        return tool_id in self._tools
    
    def clear(self) -> None:
        """清空所有已注册的工具"""
        count = len(self._tools)
        self._tools.clear()
        self._capabilities.clear()
        logger.info(f"已清空 {count} 个工具")
    
    def get_summary(self) -> Dict[str, any]:
        """
        获取注册中心摘要信息
        
        Returns:
            包含统计信息的字典
        """
        type_count = {}
        for cap in self._capabilities.values():
            tool_type = cap.tool_type.value
            type_count[tool_type] = type_count.get(tool_type, 0) + 1
        
        return {
            "total_tools": len(self._tools),
            "type_distribution": type_count,
            "tool_ids": list(self._tools.keys())
        }


# 全局单例注册中心
_global_registry: Optional[ToolRegistry] = None


def get_global_registry() -> ToolRegistry:
    """
    获取全局工具注册中心单例
    
    Returns:
        全局工具注册中心实例
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def register_tool(adapter: BaseAdapter) -> None:
    """
    注册工具到全局注册中心（便捷函数）
    
    Args:
        adapter: 工具适配器实例
    """
    registry = get_global_registry()
    registry.register(adapter)


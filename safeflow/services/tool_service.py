"""
工具服务层

提供 MCP 风格的统一工具调用接口
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger

from safeflow.adapters.base import BaseAdapter, AdapterError
from safeflow.schemas.vulnerability import UnifiedVulnerability
from safeflow.schemas.tool_capability import ToolCapability
from safeflow.services.tool_registry import ToolRegistry


class ToolServiceError(Exception):
    """工具服务异常"""
    pass


class ScanRequest:
    """扫描请求（MCP 风格）"""
    
    def __init__(
        self,
        scan_id: str,
        target_path: str,
        tool_ids: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None
    ):
        self.scan_id = scan_id
        self.target_path = target_path
        self.tool_ids = tool_ids or []
        self.options = options or {}
        self.created_at = datetime.now()


class ScanResponse:
    """扫描响应（MCP 风格）"""
    
    def __init__(
        self,
        scan_id: str,
        tool_id: str,
        success: bool,
        vulnerabilities: List[UnifiedVulnerability] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.scan_id = scan_id
        self.tool_id = tool_id
        self.success = success
        self.vulnerabilities = vulnerabilities or []
        self.error = error
        self.metadata = metadata or {}
        self.completed_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "scan_id": self.scan_id,
            "tool_id": self.tool_id,
            "success": self.success,
            "vulnerability_count": len(self.vulnerabilities),
            "error": self.error,
            "metadata": self.metadata,
            "completed_at": self.completed_at.isoformat()
        }


class ToolService:
    """
    工具服务 - MCP 风格的统一调用接口
    
    功能：
    1. 统一的工具调用接口
    2. 请求/响应标准化
    3. 错误处理和日志记录
    4. 多工具协同调用
    """
    
    def __init__(self, registry: ToolRegistry):
        """
        初始化工具服务
        
        Args:
            registry: 工具注册中心
        """
        self.registry = registry
        logger.info("ToolService 初始化完成")
    
    def scan_with_tool(
        self,
        tool_id: str,
        scan_request: ScanRequest
    ) -> ScanResponse:
        """
        使用指定工具执行扫描（MCP 标准化调用）
        
        Args:
            tool_id: 工具唯一标识
            scan_request: 扫描请求
            
        Returns:
            扫描响应
            
        Raises:
            ToolServiceError: 工具不存在或执行失败
        """
        logger.info(f"开始扫描: {scan_request.scan_id} - 工具: {tool_id}")
        
        # 获取适配器
        adapter = self.registry.get_adapter(tool_id)
        if adapter is None:
            error_msg = f"工具不存在: {tool_id}"
            logger.error(error_msg)
            return ScanResponse(
                scan_id=scan_request.scan_id,
                tool_id=tool_id,
                success=False,
                error=error_msg
            )
        
        try:
            # 构建适配器扫描请求
            adapter_request = {
                "scan_id": scan_request.scan_id,
                "target": {
                    "type": "LOCAL_PATH",
                    "path": scan_request.target_path
                },
                "options": scan_request.options
            }
            
            # 执行扫描
            vulnerabilities = adapter.run(adapter_request)
            
            # 构建响应
            response = ScanResponse(
                scan_id=scan_request.scan_id,
                tool_id=tool_id,
                success=True,
                vulnerabilities=vulnerabilities,
                metadata={
                    "tool_name": adapter.tool_name,
                    "tool_type": adapter.tool_type,
                    "vulnerability_count": len(vulnerabilities)
                }
            )
            
            logger.info(
                f"扫描完成: {scan_request.scan_id} - "
                f"发现 {len(vulnerabilities)} 个问题"
            )
            
            return response
            
        except AdapterError as e:
            error_msg = f"适配器错误: {str(e)}"
            logger.error(error_msg)
            return ScanResponse(
                scan_id=scan_request.scan_id,
                tool_id=tool_id,
                success=False,
                error=error_msg
            )
        except Exception as e:
            error_msg = f"未预期的错误: {str(e)}"
            logger.error(error_msg)
            return ScanResponse(
                scan_id=scan_request.scan_id,
                tool_id=tool_id,
                success=False,
                error=error_msg
            )
    
    def scan_with_multiple_tools(
        self,
        scan_request: ScanRequest
    ) -> List[ScanResponse]:
        """
        使用多个工具执行扫描
        
        Args:
            scan_request: 扫描请求（包含工具 ID 列表）
            
        Returns:
            扫描响应列表
        """
        if not scan_request.tool_ids:
            logger.warning("未指定工具，将使用所有已注册的工具")
            scan_request.tool_ids = self.registry.get_tool_ids()
        
        logger.info(
            f"开始多工具扫描: {scan_request.scan_id} - "
            f"工具数量: {len(scan_request.tool_ids)}"
        )
        
        responses = []
        for tool_id in scan_request.tool_ids:
            response = self.scan_with_tool(tool_id, scan_request)
            responses.append(response)
        
        # 统计
        success_count = sum(1 for r in responses if r.success)
        total_vulns = sum(len(r.vulnerabilities) for r in responses)
        
        logger.info(
            f"多工具扫描完成: {scan_request.scan_id} - "
            f"成功 {success_count}/{len(responses)} - "
            f"发现 {total_vulns} 个问题"
        )
        
        return responses
    
    def get_tool_capability(self, tool_id: str) -> Optional[ToolCapability]:
        """
        获取工具能力（MCP 能力查询）
        
        Args:
            tool_id: 工具唯一标识
            
        Returns:
            工具能力声明，如果不存在则返回 None
        """
        return self.registry.get_capability(tool_id)
    
    def list_available_tools(self) -> List[ToolCapability]:
        """
        列出所有可用工具（MCP 服务发现）
        
        Returns:
            工具能力声明列表
        """
        return self.registry.list_all()
    
    def recommend_tools_for_target(
        self,
        target_path: str,
        language: Optional[str] = None
    ) -> List[str]:
        """
        为目标推荐合适的工具
        
        Args:
            target_path: 目标路径
            language: 编程语言（可选）
            
        Returns:
            推荐的工具 ID 列表
        """
        recommended = []
        
        if language:
            # 按语言推荐
            tools = self.registry.discover_by_language(language)
            recommended = [tool.tool_id for tool in tools]
        else:
            # 推荐所有工具
            recommended = self.registry.get_tool_ids()
        
        logger.info(f"为目标 {target_path} 推荐了 {len(recommended)} 个工具")
        return recommended
    
    def aggregate_results(
        self,
        responses: List[ScanResponse]
    ) -> Dict[str, Any]:
        """
        聚合多个扫描结果
        
        Args:
            responses: 扫描响应列表
            
        Returns:
            聚合后的统计信息
        """
        total_vulns = []
        for response in responses:
            if response.success:
                total_vulns.extend(response.vulnerabilities)
        
        # 按严重度统计
        severity_count = {}
        for vuln in total_vulns:
            level = vuln.severity.level.value
            severity_count[level] = severity_count.get(level, 0) + 1
        
        # 按工具统计
        tool_count = {}
        for response in responses:
            tool_count[response.tool_id] = len(response.vulnerabilities)
        
        return {
            "total_vulnerabilities": len(total_vulns),
            "severity_distribution": severity_count,
            "tool_distribution": tool_count,
            "successful_scans": sum(1 for r in responses if r.success),
            "failed_scans": sum(1 for r in responses if not r.success)
        }


# 便捷函数
def create_tool_service() -> ToolService:
    """
    创建工具服务实例（使用全局注册中心）
    
    Returns:
        工具服务实例
    """
    from safeflow.services.tool_registry import get_global_registry
    registry = get_global_registry()
    return ToolService(registry)


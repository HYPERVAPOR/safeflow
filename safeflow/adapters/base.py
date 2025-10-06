"""
工具适配器基类
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from loguru import logger

from safeflow.schemas.tool_capability import ToolCapability
from safeflow.schemas.vulnerability import UnifiedVulnerability


class AdapterError(Exception):
    """适配器异常基类"""
    pass


class InputValidationError(AdapterError):
    """输入验证异常"""
    pass


class ExecutionError(AdapterError):
    """执行异常"""
    pass


class ParseError(AdapterError):
    """解析异常"""
    pass


class BaseAdapter(ABC):
    """
    工具适配器基类
    
    所有工具适配器必须继承此类并实现抽象方法
    """
    
    def __init__(self):
        self.logger = logger
        self._capability = None
    
    @abstractmethod
    def get_capability(self) -> ToolCapability:
        """
        返回工具能力声明
        
        Returns:
            工具能力声明对象
        """
        pass
    
    @abstractmethod
    def validate_input(self, scan_request: Dict[str, Any]) -> bool:
        """
        验证扫描请求是否满足工具输入要求
        
        Args:
            scan_request: 扫描请求字典
        
        Returns:
            验证是否通过
            
        Raises:
            InputValidationError: 输入验证失败
        """
        pass
    
    @abstractmethod
    def execute(self, scan_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行扫描任务
        
        Args:
            scan_request: 扫描请求字典
        
        Returns:
            工具原生输出（JSON 格式）
            
        Raises:
            ExecutionError: 执行失败
        """
        pass
    
    @abstractmethod
    def parse_output(self, raw_output: Dict[str, Any], scan_request: Dict[str, Any]) -> List[UnifiedVulnerability]:
        """
        将工具原生输出转换为统一漏洞模型
        
        Args:
            raw_output: 工具的原生 JSON 输出
            scan_request: 原始扫描请求（用于提取上下文信息）
        
        Returns:
            统一漏洞模型列表
            
        Raises:
            ParseError: 解析失败
        """
        pass
    
    def run(self, scan_request: Dict[str, Any]) -> List[UnifiedVulnerability]:
        """
        完整的扫描流程（框架提供，子类通常不需要重写）
        
        Args:
            scan_request: 扫描请求字典
        
        Returns:
            统一漏洞模型列表
            
        Raises:
            AdapterError: 扫描流程中的任何异常
        """
        tool_name = self.get_capability().tool_name
        self.logger.info(f"[{tool_name}] 开始扫描流程")
        
        try:
            # 步骤 1: 验证输入
            self.logger.info(f"[{tool_name}] 验证输入...")
            if not self.validate_input(scan_request):
                raise InputValidationError(f"[{tool_name}] 输入验证失败")
            
            # 步骤 2: 执行扫描
            self.logger.info(f"[{tool_name}] 执行扫描...")
            raw_output = self.execute(scan_request)
            
            # 步骤 3: 解析输出
            self.logger.info(f"[{tool_name}] 解析扫描结果...")
            vulnerabilities = self.parse_output(raw_output, scan_request)
            
            self.logger.info(f"[{tool_name}] 扫描完成，发现 {len(vulnerabilities)} 个漏洞")
            return vulnerabilities
            
        except InputValidationError as e:
            self.logger.error(f"[{tool_name}] 输入验证失败: {str(e)}")
            raise
        except ExecutionError as e:
            self.logger.error(f"[{tool_name}] 执行失败: {str(e)}")
            raise
        except ParseError as e:
            self.logger.error(f"[{tool_name}] 解析失败: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"[{tool_name}] 未预期的错误: {str(e)}")
            raise AdapterError(f"[{tool_name}] 扫描失败: {str(e)}") from e
    
    def _generate_vulnerability_id(self, scan_session_id: str, index: int) -> str:
        """
        生成漏洞唯一 ID
        
        Args:
            scan_session_id: 扫描会话 ID
            index: 漏洞索引
        
        Returns:
            漏洞唯一 ID
        """
        tool_id = self.get_capability().tool_id
        return f"vuln_{scan_session_id}_{tool_id}_{index}"
    
    def _extract_cwe_id(self, text: str) -> int:
        """
        从文本中提取 CWE ID
        
        Args:
            text: 包含 CWE 信息的文本
        
        Returns:
            CWE ID 或 None
        """
        import re
        match = re.search(r'CWE-(\d+)', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None
    
    @property
    def tool_id(self) -> str:
        """获取工具 ID"""
        return self.get_capability().tool_id
    
    @property
    def tool_name(self) -> str:
        """获取工具名称"""
        return self.get_capability().tool_name
    
    @property
    def tool_type(self) -> str:
        """获取工具类型"""
        return self.get_capability().tool_type.value


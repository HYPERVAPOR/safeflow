"""
业务场景工作流模板

定义4类典型业务场景的工作流模板：
1. 代码提交快速回归（Code Commit）
2. 依赖更新扫描验证（Dependency Update）
3. 紧急漏洞披露扫描（Emergency Vulnerability）
4. 版本发布全链路回归（Release Regression）
"""
from typing import Dict, Any, Callable, List, Optional
from abc import ABC, abstractmethod
from loguru import logger

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

from safeflow.orchestration.models import WorkflowState, WorkflowType
from safeflow.orchestration.config import (
    WorkflowConfig,
    QUICK_SCAN_CONFIG,
    DEPENDENCY_SCAN_CONFIG,
    EMERGENCY_SCAN_CONFIG,
    FULL_SCAN_CONFIG
)
from safeflow.orchestration import nodes


class WorkflowTemplateBase(ABC):
    """工作流模板基类"""
    
    def __init__(self, config: Optional[WorkflowConfig] = None):
        """
        初始化模板
        
        Args:
            config: 工作流配置
        """
        self.config = config or self.get_default_config()
    
    @abstractmethod
    def get_template_id(self) -> str:
        """获取模板ID"""
        pass
    
    @abstractmethod
    def get_template_name(self) -> str:
        """获取模板名称"""
        pass
    
    @abstractmethod
    def get_workflow_type(self) -> WorkflowType:
        """获取工作流类型"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """获取模板描述"""
        pass
    
    @abstractmethod
    def get_required_tools(self) -> List[str]:
        """获取必需的工具"""
        pass
    
    @abstractmethod
    def get_optional_tools(self) -> List[str]:
        """获取可选的工具"""
        pass
    
    @abstractmethod
    def get_default_config(self) -> WorkflowConfig:
        """获取默认配置"""
        pass
    
    @abstractmethod
    def build_graph(self) -> Callable:
        """构建工作流图"""
        pass
    
    @abstractmethod
    def get_node_sequence(self) -> List[Callable]:
        """获取节点执行序列（简化模式）"""
        pass
    
    def validate_input(self, state: WorkflowState) -> bool:
        """
        验证输入
        
        Args:
            state: 工作流状态
            
        Returns:
            是否有效
        """
        # 验证工具
        required_tools = self.get_required_tools()
        if required_tools:
            for tool in required_tools:
                if tool not in state.tool_ids:
                    logger.warning(f"缺少必需的工具: {tool}")
                    return False
        
        # 验证目标
        if not state.target.path:
            logger.error("扫描目标路径不能为空")
            return False
        
        return True
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取模板元数据"""
        return {
            "template_id": self.get_template_id(),
            "template_name": self.get_template_name(),
            "workflow_type": self.get_workflow_type().value,
            "description": self.get_description(),
            "required_tools": self.get_required_tools(),
            "optional_tools": self.get_optional_tools(),
            "config": self.config.to_dict()
        }


class CodeCommitWorkflow(WorkflowTemplateBase):
    """
    代码提交快速回归工作流
    
    场景：
    - 开发人员提交代码后触发
    - 快速安全回归测试
    - 聚焦变更代码
    
    特点：
    - 执行时间短（<30分钟）
    - 使用轻量级工具
    - 快速反馈
    """
    
    def get_template_id(self) -> str:
        return "code_commit_v1"
    
    def get_template_name(self) -> str:
        return "代码提交快速回归"
    
    def get_workflow_type(self) -> WorkflowType:
        return WorkflowType.CODE_COMMIT
    
    def get_description(self) -> str:
        return "用于代码提交后的快速安全回归测试，聚焦变更代码，执行时间<30分钟"
    
    def get_required_tools(self) -> List[str]:
        return ["semgrep"]
    
    def get_optional_tools(self) -> List[str]:
        return []
    
    def get_default_config(self) -> WorkflowConfig:
        return QUICK_SCAN_CONFIG
    
    def get_node_sequence(self) -> List[Callable]:
        """节点序列：初始化 → 扫描 → 收集 → 完成"""
        return [
            nodes.initialize_node,
            nodes.single_scan_node,
            nodes.result_collection_node,
            nodes.finalize_node
        ]
    
    def build_graph(self) -> Callable:
        """构建LangGraph图"""
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph 未安装")
        
        def _build():
            workflow = StateGraph(WorkflowState)
            
            # 添加节点
            workflow.add_node("initialize", nodes.initialize_node)
            workflow.add_node("scan", nodes.single_scan_node)
            workflow.add_node("collect", nodes.result_collection_node)
            workflow.add_node("finalize", nodes.finalize_node)
            
            # 添加边
            workflow.set_entry_point("initialize")
            workflow.add_edge("initialize", "scan")
            workflow.add_edge("scan", "collect")
            workflow.add_edge("collect", "finalize")
            workflow.add_edge("finalize", END)
            
            return workflow.compile()
        
        return _build


class DependencyUpdateWorkflow(WorkflowTemplateBase):
    """
    依赖更新扫描验证工作流
    
    场景：
    - 依赖库升级后触发
    - 重点进行SCA扫描
    - 漏洞库匹配
    
    特点：
    - 聚焦依赖分析
    - 验证漏洞修复
    - 生成依赖清单
    """
    
    def get_template_id(self) -> str:
        return "dependency_update_v1"
    
    def get_template_name(self) -> str:
        return "依赖更新扫描验证"
    
    def get_workflow_type(self) -> WorkflowType:
        return WorkflowType.DEPENDENCY_UPDATE
    
    def get_description(self) -> str:
        return "重点进行SCA扫描与漏洞匹配，用于依赖库升级后的安全验证"
    
    def get_required_tools(self) -> List[str]:
        return ["syft"]
    
    def get_optional_tools(self) -> List[str]:
        return ["dependency-check"]
    
    def get_default_config(self) -> WorkflowConfig:
        return DEPENDENCY_SCAN_CONFIG
    
    def get_node_sequence(self) -> List[Callable]:
        """节点序列：初始化 → 扫描 → 验证 → 完成"""
        return [
            nodes.initialize_node,
            nodes.single_scan_node,
            nodes.validation_node,
            nodes.finalize_node
        ]
    
    def build_graph(self) -> Callable:
        """构建LangGraph图"""
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph 未安装")
        
        def _build():
            workflow = StateGraph(WorkflowState)
            
            # 添加节点
            workflow.add_node("initialize", nodes.initialize_node)
            workflow.add_node("scan", nodes.single_scan_node)
            workflow.add_node("validate", nodes.validation_node)
            workflow.add_node("finalize", nodes.finalize_node)
            
            # 添加边
            workflow.set_entry_point("initialize")
            workflow.add_edge("initialize", "scan")
            workflow.add_edge("scan", "validate")
            workflow.add_edge("validate", "finalize")
            workflow.add_edge("finalize", END)
            
            return workflow.compile()
        
        return _build


class EmergencyVulnWorkflow(WorkflowTemplateBase):
    """
    紧急漏洞披露扫描工作流
    
    场景：
    - 重大漏洞披露后触发
    - 快速全量扫描
    - 针对特定CVE/CWE
    
    特点：
    - 高并发执行
    - 优先级排序
    - 立即生成报告
    """
    
    def get_template_id(self) -> str:
        return "emergency_vuln_v1"
    
    def get_template_name(self) -> str:
        return "紧急漏洞披露扫描"
    
    def get_workflow_type(self) -> WorkflowType:
        return WorkflowType.EMERGENCY_VULN
    
    def get_description(self) -> str:
        return "快速全量扫描与验证，针对特定CVE/CWE，执行时间<1小时"
    
    def get_required_tools(self) -> List[str]:
        return ["semgrep", "syft"]
    
    def get_optional_tools(self) -> List[str]:
        return []
    
    def get_default_config(self) -> WorkflowConfig:
        return EMERGENCY_SCAN_CONFIG
    
    def get_node_sequence(self) -> List[Callable]:
        """节点序列：初始化 → 并行扫描 → 收集 → 验证 → 完成"""
        return [
            nodes.initialize_node,
            nodes.parallel_scan_node,
            nodes.result_collection_node,
            nodes.validation_node,
            nodes.finalize_node
        ]
    
    def build_graph(self) -> Callable:
        """构建LangGraph图"""
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph 未安装")
        
        def _build():
            workflow = StateGraph(WorkflowState)
            
            # 添加节点
            workflow.add_node("initialize", nodes.initialize_node)
            workflow.add_node("parallel_scan", nodes.parallel_scan_node)
            workflow.add_node("collect", nodes.result_collection_node)
            workflow.add_node("validate", nodes.validation_node)
            workflow.add_node("finalize", nodes.finalize_node)
            
            # 添加边
            workflow.set_entry_point("initialize")
            workflow.add_edge("initialize", "parallel_scan")
            workflow.add_edge("parallel_scan", "collect")
            workflow.add_edge("collect", "validate")
            workflow.add_edge("validate", "finalize")
            workflow.add_edge("finalize", END)
            
            return workflow.compile()
        
        return _build


class ReleaseRegressionWorkflow(WorkflowTemplateBase):
    """
    版本发布全链路回归工作流
    
    场景：
    - 版本发布前触发
    - 完整的多阶段测试
    - 人工审查环节
    
    特点：
    - 全面覆盖
    - 包含人工审查
    - 生成合规报告
    """
    
    def get_template_id(self) -> str:
        return "release_regression_v1"
    
    def get_template_name(self) -> str:
        return "版本发布全链路回归"
    
    def get_workflow_type(self) -> WorkflowType:
        return WorkflowType.RELEASE_REGRESSION
    
    def get_description(self) -> str:
        return "完整的多阶段测试，包含人工审查环节，用于版本发布前的全面安全检查"
    
    def get_required_tools(self) -> List[str]:
        return ["semgrep", "syft"]
    
    def get_optional_tools(self) -> List[str]:
        return []
    
    def get_default_config(self) -> WorkflowConfig:
        return FULL_SCAN_CONFIG
    
    def get_node_sequence(self) -> List[Callable]:
        """节点序列：初始化 → 并行扫描 → 收集 → 验证 → 人工审查 → 完成"""
        return [
            nodes.initialize_node,
            nodes.parallel_scan_node,
            nodes.result_collection_node,
            nodes.validation_node,
            nodes.human_review_node,
            nodes.finalize_node
        ]
    
    def build_graph(self) -> Callable:
        """构建LangGraph图"""
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph 未安装")
        
        def _build():
            workflow = StateGraph(WorkflowState)
            
            # 添加节点
            workflow.add_node("initialize", nodes.initialize_node)
            workflow.add_node("parallel_scan", nodes.parallel_scan_node)
            workflow.add_node("collect", nodes.result_collection_node)
            workflow.add_node("validate", nodes.validation_node)
            workflow.add_node("human_review", nodes.human_review_node)
            workflow.add_node("finalize", nodes.finalize_node)
            
            # 添加边
            workflow.set_entry_point("initialize")
            workflow.add_edge("initialize", "parallel_scan")
            workflow.add_edge("parallel_scan", "collect")
            workflow.add_edge("collect", "validate")
            workflow.add_edge("validate", "human_review")
            workflow.add_edge("human_review", "finalize")
            workflow.add_edge("finalize", END)
            
            return workflow.compile()
        
        return _build


# 模板注册表

WORKFLOW_TEMPLATES: Dict[WorkflowType, WorkflowTemplateBase] = {
    WorkflowType.CODE_COMMIT: CodeCommitWorkflow(),
    WorkflowType.DEPENDENCY_UPDATE: DependencyUpdateWorkflow(),
    WorkflowType.EMERGENCY_VULN: EmergencyVulnWorkflow(),
    WorkflowType.RELEASE_REGRESSION: ReleaseRegressionWorkflow(),
}


def get_template(workflow_type: WorkflowType) -> WorkflowTemplateBase:
    """
    获取工作流模板
    
    Args:
        workflow_type: 工作流类型
        
    Returns:
        工作流模板实例
    """
    if workflow_type not in WORKFLOW_TEMPLATES:
        raise ValueError(f"不支持的工作流类型: {workflow_type}")
    
    return WORKFLOW_TEMPLATES[workflow_type]


def list_templates() -> List[Dict[str, Any]]:
    """
    列出所有模板
    
    Returns:
        模板元数据列表
    """
    return [template.get_metadata() for template in WORKFLOW_TEMPLATES.values()]


def get_template_by_id(template_id: str) -> Optional[WorkflowTemplateBase]:
    """
    通过模板ID获取模板
    
    Args:
        template_id: 模板ID
        
    Returns:
        工作流模板实例
    """
    for template in WORKFLOW_TEMPLATES.values():
        if template.get_template_id() == template_id:
            return template
    
    return None


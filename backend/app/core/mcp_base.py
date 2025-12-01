"""
MCP 工具基础抽象类
提供统一的 MCP 工具接口和通用功能
"""

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ToolCategory(str, Enum):
    """工具分类"""

    STATIC_ANALYSIS = "static_analysis"  # 静态分析
    DYNAMIC_ANALYSIS = "dynamic_analysis"  # 动态分析
    DEPENDENCY_ANALYSIS = "dependency_analysis"  # 依赖分析
    FUZZING = "fuzzing"  # 模糊测试
    WEB_SECURITY = "web_security"  # Web安全


class ParameterType(str, Enum):
    """参数类型"""

    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    FILE = "file"
    DIRECTORY = "directory"


class ToolParameter(BaseModel):
    """工具参数定义"""

    name: str = Field(..., description="参数名称")
    type: ParameterType = Field(..., description="参数类型")
    description: str = Field(..., description="参数描述")
    required: bool = Field(True, description="是否必需")
    default: Optional[Any] = Field(None, description="默认值")
    enum: Optional[List[str]] = Field(None, description="枚举值")
    pattern: Optional[str] = Field(None, description="正则表达式模式")
    min_length: Optional[int] = Field(None, description="最小长度")
    max_length: Optional[int] = Field(None, description="最大长度")
    minimum: Optional[Union[int, float]] = Field(None, description="最小值")
    maximum: Optional[Union[int, float]] = Field(None, description="最大值")
    format: Optional[str] = Field(None, description="格式提示")


class ToolCapability(BaseModel):
    """工具能力描述"""

    category: ToolCategory = Field(..., description="工具分类")
    description: str = Field(..., description="工具描述")
    version: str = Field(..., description="工具版本")
    author: str = Field(..., description="作者")
    homepage: Optional[str] = Field(None, description="主页链接")
    documentation: Optional[str] = Field(None, description="文档链接")
    supported_languages: List[str] = Field(
        default_factory=list, description="支持的编程语言"
    )
    supported_formats: List[str] = Field(
        default_factory=list, description="支持的输入格式"
    )
    output_formats: List[str] = Field(
        default_factory=list, description="支持的输出格式"
    )
    tags: List[str] = Field(default_factory=list, description="标签")


class ExecutionContext(BaseModel):
    """执行上下文"""

    user_id: Optional[str] = Field(None, description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    request_id: Optional[str] = Field(None, description="请求ID")
    workspace_dir: Optional[str] = Field(None, description="工作目录")
    timeout: int = Field(300, description="超时时间(秒)")
    max_memory: str = Field("1GB", description="最大内存")
    enable_network: bool = Field(False, description="是否允许网络访问")
    sandbox: bool = Field(True, description="是否使用沙箱")


class ExecutionResult(BaseModel):
    """执行结果"""

    success: bool = Field(..., description="是否成功")
    tool_name: str = Field(..., description="工具名称")
    execution_time: float = Field(..., description="执行时间(秒)")
    output: Optional[str] = Field(None, description="输出内容")
    output_file: Optional[str] = Field(None, description="输出文件路径")
    error: Optional[str] = Field(None, description="错误信息")
    exit_code: int = Field(0, description="退出代码")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class MCPToolBase(ABC):
    """MCP 工具基础抽象类"""

    def __init__(self):
        self.name: str = (
            self.__class__.__name__.lower().replace("mcp", "").replace("tool", "")
        )
        self._tool_info: Optional[ToolCapability] = None

    @property
    @abstractmethod
    def parameters(self) -> List[ToolParameter]:
        """获取工具参数定义"""
        pass

    @property
    @abstractmethod
    def capability(self) -> ToolCapability:
        """获取工具能力描述"""
        pass

    @abstractmethod
    async def execute(
        self, args: Dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """执行工具"""
        pass

    @abstractmethod
    async def validate_args(self, args: Dict[str, Any]) -> bool:
        """验证参数"""
        pass

    @abstractmethod
    async def check_availability(self) -> bool:
        """检查工具可用性"""
        pass

    def get_tool_info(self) -> Dict[str, Any]:
        """获取工具信息（MCP 格式）"""
        if not self._tool_info:
            self._tool_info = self.capability

        params_schema = {"type": "object", "properties": {}, "required": []}

        for param in self.parameters:
            param_schema = {"type": param.type.value, "description": param.description}

            if param.default is not None:
                param_schema["default"] = param.default
            if param.enum:
                param_schema["enum"] = param.enum
            if param.pattern:
                param_schema["pattern"] = param.pattern
            if param.min_length is not None:
                param_schema["minLength"] = param.min_length
            if param.max_length is not None:
                param_schema["maxLength"] = param.max_length
            if param.minimum is not None:
                param_schema["minimum"] = param.minimum
            if param.maximum is not None:
                param_schema["maximum"] = param.maximum
            if param.format:
                param_schema["format"] = param.format

            params_schema["properties"][param.name] = param_schema

            if param.required:
                params_schema["required"].append(param.name)

        return {
            "name": self.name,
            "description": self._tool_info.description,
            "inputSchema": params_schema,
            "category": self._tool_info.category.value,
            "capability": {
                "version": self._tool_info.version,
                "author": self._tool_info.author,
                "homepage": self._tool_info.homepage,
                "documentation": self._tool_info.documentation,
                "supported_languages": self._tool_info.supported_languages,
                "supported_formats": self._tool_info.supported_formats,
                "output_formats": self._tool_info.output_formats,
                "tags": self._tool_info.tags,
            },
        }

    async def prepare_execution(
        self, args: Dict[str, Any], context: ExecutionContext
    ) -> bool:
        """准备执行环境"""
        # 验证参数
        if not await self.validate_args(args):
            return False

        # 检查工具可用性
        if not await self.check_availability():
            return False

        return True

    def create_error_result(
        self, tool_name: str, error: str, execution_time: float = 0.0
    ) -> ExecutionResult:
        """创建错误结果"""
        return ExecutionResult(
            success=False,
            tool_name=tool_name,
            execution_time=execution_time,
            error=error,
            exit_code=1,
        )

    def create_success_result(
        self,
        tool_name: str,
        execution_time: float,
        output: Optional[str] = None,
        output_file: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """创建成功结果"""
        return ExecutionResult(
            success=True,
            tool_name=tool_name,
            execution_time=execution_time,
            output=output,
            output_file=output_file,
            exit_code=0,
            metadata=metadata or {},
        )


class SandboxManager:
    """沙箱管理器"""

    @staticmethod
    async def create_sandbox(context: ExecutionContext) -> Optional[str]:
        """创建沙箱环境"""
        # 这里可以集成 Docker 或其他容器技术
        # 暂时返回工作目录
        if context.workspace_dir:
            return context.workspace_dir
        return "/tmp/safeflow-sandbox"

    @staticmethod
    async def cleanup_sandbox(sandbox_path: str):
        """清理沙箱环境"""
        # 清理临时文件
        pass


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self._tools: Dict[str, MCPToolBase] = {}
        self._categories: Dict[ToolCategory, List[str]] = {}

    def register(self, tool: MCPToolBase):
        """注册工具"""
        self._tools[tool.name] = tool
        category = tool.capability.category
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(tool.name)
        logger.info(f"Registered MCP tool: {tool.name}")

    def get_tool(self, name: str) -> Optional[MCPToolBase]:
        """获取工具"""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """列出所有工具"""
        return list(self._tools.keys())

    def list_tools_by_category(self, category: ToolCategory) -> List[str]:
        """按分类列出工具"""
        return self._categories.get(category, [])

    def get_all_tools_info(self) -> List[Dict[str, Any]]:
        """获取所有工具信息"""
        return [tool.get_tool_info() for tool in self._tools.values()]


# 全局工具注册表
tool_registry = ToolRegistry()

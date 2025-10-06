"""
MCP 协议 - 工具能力声明 Schema
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ToolType(str, Enum):
    """工具类型枚举"""
    SAST = "SAST"          # 静态应用安全测试
    DAST = "DAST"          # 动态应用安全测试
    IAST = "IAST"          # 交互式应用安全测试
    SCA = "SCA"            # 软件成分分析
    FUZZING = "FUZZING"    # 模糊测试
    SECRETS = "SECRETS"    # 密钥扫描
    CONTAINER = "CONTAINER" # 容器镜像扫描


class Capabilities(BaseModel):
    """工具能力描述"""
    supported_languages: List[str] = Field(
        description="支持的编程语言列表",
        example=["python", "java", "javascript"]
    )
    detection_types: List[str] = Field(
        description="支持检测的漏洞类型",
        example=["sql_injection", "xss", "buffer_overflow"]
    )
    cwe_coverage: List[int] = Field(
        default=[],
        description="覆盖的 CWE ID 列表"
    )


class InputRequirements(BaseModel):
    """输入要求"""
    requires_source_code: bool = Field(
        default=True,
        description="是否需要源代码"
    )
    requires_binary: bool = Field(
        default=False,
        description="是否需要二进制文件"
    )
    requires_running_app: bool = Field(
        default=False,
        description="是否需要运行中的应用"
    )
    requires_dependencies_manifest: bool = Field(
        default=False,
        description="是否需要依赖清单文件"
    )
    supported_vcs: List[str] = Field(
        default=["git"],
        description="支持的版本控制系统"
    )
    additional_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="工具特定的额外配置"
    )


class OutputFormat(BaseModel):
    """输出格式描述"""
    native_format: str = Field(
        description="原生输出格式",
        example="json"
    )
    supports_streaming: bool = Field(
        default=False,
        description="是否支持流式输出"
    )
    result_fields: List[str] = Field(
        description="原生输出包含的关键字段",
        example=["path", "line", "severity"]
    )


class ResourceRequirements(BaseModel):
    """资源要求"""
    min_memory_mb: int = Field(
        default=512,
        description="最小内存需求（MB）"
    )
    min_cpu_cores: int = Field(
        default=1,
        description="最小 CPU 核心数"
    )


class ExecutionConfig(BaseModel):
    """执行配置"""
    command_template: str = Field(
        description="命令行模板",
        example="semgrep scan --json --config=auto {target_path}"
    )
    timeout_seconds: int = Field(
        default=600,
        description="默认超时时间（秒）"
    )
    resource_requirements: ResourceRequirements


class Metadata(BaseModel):
    """元数据"""
    license: str = Field(
        description="许可证",
        example="MIT"
    )
    documentation_url: Optional[str] = Field(
        default=None,
        description="文档链接"
    )
    adapter_version: str = Field(
        description="适配器版本",
        example="1.0.0"
    )
    registered_at: datetime = Field(
        default_factory=datetime.now,
        description="注册时间"
    )


class ToolCapability(BaseModel):
    """工具能力声明完整模型"""
    tool_id: str = Field(
        description="工具唯一标识",
        example="semgrep-1.50.0"
    )
    tool_name: str = Field(
        description="工具名称",
        example="Semgrep"
    )
    tool_version: str = Field(
        description="工具版本号",
        example="1.50.0"
    )
    tool_type: ToolType = Field(
        description="工具类型"
    )
    vendor: str = Field(
        description="厂商/组织名称",
        example="Semgrep Inc."
    )
    description: str = Field(
        description="工具功能描述"
    )
    
    capabilities: Capabilities
    input_requirements: InputRequirements
    output_format: OutputFormat
    execution: ExecutionConfig
    metadata: Metadata

    class Config:
        json_schema_extra = {
            "example": {
                "tool_id": "semgrep-1.50.0",
                "tool_name": "Semgrep",
                "tool_version": "1.50.0",
                "tool_type": "SAST",
                "vendor": "Semgrep Inc.",
                "description": "轻量级静态代码分析工具",
                "capabilities": {
                    "supported_languages": ["python", "javascript", "java"],
                    "detection_types": ["sql_injection", "xss"],
                    "cwe_coverage": [79, 89]
                },
                "input_requirements": {
                    "requires_source_code": True,
                    "requires_binary": False,
                    "requires_running_app": False,
                    "requires_dependencies_manifest": False,
                    "supported_vcs": ["git"],
                    "additional_config": {}
                },
                "output_format": {
                    "native_format": "json",
                    "supports_streaming": False,
                    "result_fields": ["check_id", "path", "start", "end"]
                },
                "execution": {
                    "command_template": "semgrep scan --json --config=auto {target_path}",
                    "timeout_seconds": 600,
                    "resource_requirements": {
                        "min_memory_mb": 512,
                        "min_cpu_cores": 1
                    }
                },
                "metadata": {
                    "license": "LGPL-2.1",
                    "documentation_url": "https://semgrep.dev/docs/",
                    "adapter_version": "1.0.0",
                    "registered_at": "2025-01-15T10:00:00Z"
                }
            }
        }


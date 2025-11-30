from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class ToolStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class ToolCapability(BaseModel):
    """工具能力声明"""
    name: str = Field(..., description="能力名称")
    description: str = Field(..., description="能力描述")
    input_schema: Dict[str, Any] = Field(..., description="输入参数结构")
    output_schema: Dict[str, Any] = Field(..., description="输出结果结构")


class ToolRegistration(BaseModel):
    """工具注册信息"""
    tool_id: str = Field(..., description="工具唯一标识")
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    version: str = Field(..., description="工具版本")
    capabilities: List[ToolCapability] = Field(..., description="工具能力列表")
    deployment_config: Dict[str, Any] = Field(..., description="部署配置")
    supported_commands: List[str] = Field(..., description="支持的命令")
    tags: List[str] = Field(default=[], description="功能标签")


class ToolInfo(BaseModel):
    """工具信息"""
    tool_id: str
    name: str
    description: str
    version: str
    status: ToolStatus
    capabilities: List[ToolCapability]
    tags: List[str]
    created_at: str
    updated_at: str
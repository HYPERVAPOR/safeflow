"""
MCP 协议 Schema 定义模块
"""
from safeflow.schemas.tool_capability import (
    ToolCapability,
    ToolType,
    Capabilities,
    InputRequirements,
    OutputFormat,
    ExecutionConfig,
    ResourceRequirements,
    Metadata
)

from safeflow.schemas.vulnerability import (
    UnifiedVulnerability,
    VulnerabilityType,
    Location,
    Severity,
    SeverityLevel,
    Confidence,
    SourceTool,
    Description,
    VulnerabilityMetadata,
    Verification,
    VerificationStatus,
    Exploitability,
    map_severity_to_unified
)

__all__ = [
    # Tool Capability
    "ToolCapability",
    "ToolType",
    "Capabilities",
    "InputRequirements",
    "OutputFormat",
    "ExecutionConfig",
    "ResourceRequirements",
    "Metadata",
    
    # Vulnerability
    "UnifiedVulnerability",
    "VulnerabilityType",
    "Location",
    "Severity",
    "SeverityLevel",
    "Confidence",
    "SourceTool",
    "Description",
    "VulnerabilityMetadata",
    "Verification",
    "VerificationStatus",
    "Exploitability",
    "map_severity_to_unified"
]


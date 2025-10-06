# SafeFlow 模型上下文协议（MCP）规范 v1.0

## 1. 概述

模型上下文协议（Model Context Protocol, MCP）是 SafeFlow 平台用于统一异构安全工具接入的标准化协议。

### 1.1 设计目标

- **标准化**：为所有安全工具提供统一的描述语言
- **可扩展**：支持新工具类型和新字段的灵活扩展
- **互操作**：保证不同工具的结果可以直接比较和融合
- **语义化**：明确定义每个字段的含义和约束

---

## 2. 工具能力声明 Schema

### 2.1 ToolCapability 模型

```json
{
  "tool_id": "string (唯一标识)",
  "tool_name": "string (工具名称)",
  "tool_version": "string (版本号)",
  "tool_type": "enum [SAST, DAST, IAST, SCA, FUZZING, SECRETS, CONTAINER]",
  "vendor": "string (厂商/组织)",
  "description": "string (功能描述)",
  
  "capabilities": {
    "supported_languages": ["string (如 python, java, c++)"],
    "detection_types": ["string (如 sql_injection, xss, buffer_overflow)"],
    "cwe_coverage": ["integer (支持的 CWE ID 列表)"]
  },
  
  "input_requirements": {
    "requires_source_code": "boolean",
    "requires_binary": "boolean",
    "requires_running_app": "boolean",
    "requires_dependencies_manifest": "boolean",
    "supported_vcs": ["git", "svn"],
    "additional_config": "object (工具特定配置)"
  },
  
  "output_format": {
    "native_format": "string (如 json, xml, sarif)",
    "supports_streaming": "boolean",
    "result_fields": ["string (原生输出包含的关键字段)"]
  },
  
  "execution": {
    "command_template": "string (命令行模板)",
    "timeout_seconds": "integer (默认超时时间)",
    "resource_requirements": {
      "min_memory_mb": "integer",
      "min_cpu_cores": "integer"
    }
  },
  
  "metadata": {
    "license": "string",
    "documentation_url": "string",
    "adapter_version": "string (适配器版本)",
    "registered_at": "datetime (注册时间)"
  }
}
```

### 2.2 示例：Semgrep 能力声明

```json
{
  "tool_id": "semgrep-1.50.0",
  "tool_name": "Semgrep",
  "tool_version": "1.50.0",
  "tool_type": "SAST",
  "vendor": "Semgrep Inc.",
  "description": "轻量级静态代码分析工具，支持自定义规则",
  
  "capabilities": {
    "supported_languages": [
      "python", "javascript", "typescript", "java", "go", 
      "ruby", "c", "cpp", "php", "rust", "kotlin", "scala"
    ],
    "detection_types": [
      "sql_injection", "xss", "command_injection", "path_traversal",
      "hardcoded_secrets", "insecure_deserialization"
    ],
    "cwe_coverage": [89, 79, 78, 22, 502, 798]
  },
  
  "input_requirements": {
    "requires_source_code": true,
    "requires_binary": false,
    "requires_running_app": false,
    "requires_dependencies_manifest": false,
    "supported_vcs": ["git"],
    "additional_config": {
      "rules": "可选，自定义规则路径或规则集名称"
    }
  },
  
  "output_format": {
    "native_format": "json",
    "supports_streaming": false,
    "result_fields": ["check_id", "path", "start", "end", "extra"]
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
```

---

## 3. 统一漏洞模型 Schema

### 3.1 UnifiedVulnerability 模型

```json
{
  "vulnerability_id": "string (平台生成的唯一 ID)",
  "scan_session_id": "string (所属扫描会话 ID)",
  
  "vulnerability_type": {
    "name": "string (漏洞名称，如 SQL Injection)",
    "cwe_id": "integer | null (CWE 分类 ID)",
    "owasp_category": "string | null (如 A03:2021 - Injection)"
  },
  
  "location": {
    "file_path": "string (相对于项目根目录的路径)",
    "function_name": "string | null (函数/方法名)",
    "class_name": "string | null (类名)",
    "line_start": "integer (起始行号)",
    "line_end": "integer (结束行号)",
    "column_start": "integer | null",
    "column_end": "integer | null",
    "code_snippet": "string | null (相关代码片段)"
  },
  
  "severity": {
    "level": "enum [CRITICAL, HIGH, MEDIUM, LOW, INFO]",
    "score": "float | null (CVSS 分数, 0-10)",
    "exploitability": "enum [EASY, MODERATE, HARD, UNKNOWN]"
  },
  
  "confidence": {
    "score": "integer (0-100, 置信度百分比)",
    "reason": "string (置信度评估依据)"
  },
  
  "source_tool": {
    "tool_id": "string (来源工具标识)",
    "rule_id": "string (触发的规则 ID)",
    "original_severity": "string (工具原始严重度)",
    "raw_output": "object (工具原始输出，JSON 格式)"
  },
  
  "description": {
    "summary": "string (简短描述)",
    "detail": "string (详细说明)",
    "impact": "string (潜在影响)",
    "remediation": "string (修复建议)"
  },
  
  "metadata": {
    "detected_at": "datetime (检测时间)",
    "language": "string (代码语言)",
    "tags": ["string (标签列表)"],
    "references": ["string (外部参考链接)"]
  },
  
  "verification": {
    "status": "enum [PENDING, VERIFIED, FALSE_POSITIVE, WONT_FIX]",
    "verified_at": "datetime | null",
    "verified_by": "string | null (验证人或自动化系统)"
  }
}
```

### 3.2 严重度映射规则

| 工具原生等级 | 统一等级 | CVSS 分数范围 |
|------------|---------|-------------|
| Critical / 严重 | CRITICAL | 9.0 - 10.0 |
| High / 高 | HIGH | 7.0 - 8.9 |
| Medium / 中 / Warning | MEDIUM | 4.0 - 6.9 |
| Low / 低 / Info | LOW | 0.1 - 3.9 |
| Informational / 信息 | INFO | 0.0 |

---

## 4. 适配器接口规范

### 4.1 BaseAdapter 抽象类

每个工具适配器必须继承 `BaseAdapter` 并实现以下方法：

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from safeflow.schemas.tool_capability import ToolCapability
from safeflow.schemas.vulnerability import UnifiedVulnerability

class BaseAdapter(ABC):
    
    @abstractmethod
    def get_capability(self) -> ToolCapability:
        """返回工具能力声明"""
        pass
    
    @abstractmethod
    def validate_input(self, scan_request: Dict[str, Any]) -> bool:
        """验证扫描请求是否满足工具输入要求"""
        pass
    
    @abstractmethod
    def execute(self, scan_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行扫描任务
        
        Returns:
            工具原生输出（JSON 格式）
        """
        pass
    
    @abstractmethod
    def parse_output(self, raw_output: Dict[str, Any]) -> List[UnifiedVulnerability]:
        """
        将工具原生输出转换为统一漏洞模型
        
        Args:
            raw_output: 工具的原生 JSON 输出
            
        Returns:
            统一漏洞模型列表
        """
        pass
    
    def run(self, scan_request: Dict[str, Any]) -> List[UnifiedVulnerability]:
        """
        完整的扫描流程（框架提供）
        """
        if not self.validate_input(scan_request):
            raise ValueError("输入验证失败")
        
        raw_output = self.execute(scan_request)
        vulnerabilities = self.parse_output(raw_output)
        
        return vulnerabilities
```

### 4.2 ScanRequest 格式

```json
{
  "scan_id": "string (扫描任务唯一 ID)",
  "target": {
    "type": "enum [LOCAL_PATH, GIT_REPO, DOCKER_IMAGE]",
    "path": "string (目标路径或 URL)",
    "branch": "string | null (Git 分支，仅 GIT_REPO 类型)",
    "commit": "string | null (Git commit ID)"
  },
  "options": {
    "language": "string | null (指定语言，可选)",
    "rules": "string | null (自定义规则，可选)",
    "exclude_paths": ["string (排除路径列表)"]
  },
  "context": {
    "project_name": "string",
    "scan_type": "enum [FULL, INCREMENTAL]",
    "triggered_by": "string (触发来源，如 CI/CD, Manual)"
  }
}
```

---

## 5. 字段映射表

### 5.1 Semgrep → UnifiedVulnerability 映射

| Semgrep 字段 | MCP 字段 | 映射规则 |
|-------------|---------|---------|
| `check_id` | `source_tool.rule_id` | 直接映射 |
| `path` | `location.file_path` | 直接映射 |
| `start.line` | `location.line_start` | 直接映射 |
| `end.line` | `location.line_end` | 直接映射 |
| `extra.severity` | `severity.level` | 按映射表转换 |
| `extra.message` | `description.summary` | 直接映射 |
| `extra.metadata.cwe` | `vulnerability_type.cwe_id` | 提取 CWE ID |

### 5.2 Syft → UnifiedVulnerability 映射

| Syft 字段 | MCP 字段 | 映射规则 |
|----------|---------|---------|
| `vulnerability.id` (CVE-ID) | `vulnerability_type.name` | 直接映射 |
| `artifact.name` | `location.file_path` | 依赖包名作为"位置" |
| `vulnerability.severity` | `severity.level` | 按映射表转换 |
| `vulnerability.cvss.score` | `severity.score` | 直接映射 |
| `vulnerability.description` | `description.summary` | 直接映射 |

---

## 6. 扩展性设计

### 6.1 新增工具类型

在 `tool_type` 枚举中添加新类型：

```python
class ToolType(str, Enum):
    SAST = "SAST"          # 静态应用安全测试
    DAST = "DAST"          # 动态应用安全测试
    IAST = "IAST"          # 交互式应用安全测试
    SCA = "SCA"            # 软件成分分析
    FUZZING = "FUZZING"    # 模糊测试
    SECRETS = "SECRETS"    # 密钥扫描
    CONTAINER = "CONTAINER" # 容器镜像扫描
    # 未来可扩展：IaC, API Security 等
```

### 6.2 新增自定义字段

在 `UnifiedVulnerability.metadata` 中添加自定义字段，保持向后兼容。

---

## 7. 版本演进策略

- **v1.x**: 支持基础 SAST/SCA 工具
- **v2.x**: 增加 DAST/Fuzzing 支持，引入验证状态
- **v3.x**: 增加证据链字段，支持区块链存证

---

## 附录 A: CWE Top 25 映射表

| CWE ID | 名称 | 对应检测类型 |
|--------|------|------------|
| CWE-79 | XSS | xss |
| CWE-89 | SQL 注入 | sql_injection |
| CWE-22 | 路径遍历 | path_traversal |
| CWE-78 | OS 命令注入 | command_injection |
| CWE-787 | 越界写 | buffer_overflow |
| CWE-502 | 不安全反序列化 | insecure_deserialization |
| CWE-798 | 硬编码凭据 | hardcoded_secrets |
| ... | ... | ... |

完整列表参考：https://cwe.mitre.org/top25/

---

## 附录 B: SARIF 格式对比

MCP 协议参考了 SARIF（Static Analysis Results Interchange Format）标准，但进行了简化和定制：

- **简化点**：去除了冗余的嵌套结构，直接扁平化关键字段
- **扩展点**：增加了工具能力声明、置信度、验证状态等字段
- **兼容性**：可通过转换器支持 SARIF ↔ MCP 互转

---

## 变更记录

| 版本 | 日期 | 变更内容 |
|-----|------|---------|
| v1.0 | 2025-01-15 | 初始版本，支持 SAST/SCA 基础字段 |


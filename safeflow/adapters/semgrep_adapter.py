"""
Semgrep 工具适配器

将 Semgrep 静态分析工具集成到 SafeFlow 平台
"""
import json
import subprocess
import os
from typing import List, Dict, Any
from datetime import datetime

from safeflow.adapters.base import (
    BaseAdapter, 
    InputValidationError, 
    ExecutionError, 
    ParseError
)
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
    Exploitability,
    map_severity_to_unified
)


class SemgrepAdapter(BaseAdapter):
    """Semgrep 适配器实现"""
    
    def __init__(self):
        super().__init__()
        self._check_semgrep_installed()
    
    def _get_semgrep_path(self) -> str:
        """获取 Semgrep 可执行文件路径"""
        import sys
        from pathlib import Path
        
        # 尝试查找虚拟环境中的 semgrep
        venv_semgrep = Path(sys.executable).parent / "semgrep"
        if venv_semgrep.exists():
            return str(venv_semgrep)
        
        # 尝试使用系统 PATH 中的 semgrep
        import shutil
        system_semgrep = shutil.which("semgrep")
        if system_semgrep:
            return system_semgrep
        
        raise ExecutionError("未找到 Semgrep 命令，请先安装: pip install semgrep")
    
    def _check_semgrep_installed(self):
        """检查 Semgrep 是否已安装"""
        try:
            semgrep_path = self._get_semgrep_path()
            result = subprocess.run(
                [semgrep_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise ExecutionError("Semgrep 未正确安装")
            self.logger.info(f"Semgrep 版本: {result.stdout.strip()}")
            self.logger.info(f"Semgrep 路径: {semgrep_path}")
        except ExecutionError:
            raise
        except Exception as e:
            raise ExecutionError(f"检查 Semgrep 安装失败: {str(e)}")
    
    def get_capability(self) -> ToolCapability:
        """返回 Semgrep 工具能力声明"""
        return ToolCapability(
            tool_id="semgrep",
            tool_name="Semgrep",
            tool_version="1.50.0",
            tool_type=ToolType.SAST,
            vendor="Semgrep Inc.",
            description="轻量级静态代码分析工具，支持多种语言和自定义规则",
            
            capabilities=Capabilities(
                supported_languages=[
                    "python", "javascript", "typescript", "java", "go",
                    "ruby", "c", "cpp", "php", "rust", "kotlin", "scala"
                ],
                detection_types=[
                    "sql_injection", "xss", "command_injection", "path_traversal",
                    "hardcoded_secrets", "insecure_deserialization", "xxe",
                    "open_redirect", "csrf", "weak_crypto"
                ],
                cwe_coverage=[89, 79, 78, 22, 502, 798, 611, 601, 352, 327]
            ),
            
            input_requirements=InputRequirements(
                requires_source_code=True,
                requires_binary=False,
                requires_running_app=False,
                requires_dependencies_manifest=False,
                supported_vcs=["git"],
                additional_config={
                    "rules": "可选，自定义规则路径或规则集名称（如 'p/security-audit'）"
                }
            ),
            
            output_format=OutputFormat(
                native_format="json",
                supports_streaming=False,
                result_fields=["check_id", "path", "start", "end", "extra"]
            ),
            
            execution=ExecutionConfig(
                command_template="semgrep scan --json --no-git-ignore --config {rules} {target_path}",
                timeout_seconds=1800,  # 增加到 30 分钟，适应大型项目
                resource_requirements=ResourceRequirements(
                    min_memory_mb=512,
                    min_cpu_cores=1
                )
            ),
            
            metadata=Metadata(
                license="LGPL-2.1",
                documentation_url="https://semgrep.dev/docs/",
                adapter_version="1.0.0",
                registered_at=datetime.now()
            )
        )
    
    def validate_input(self, scan_request: Dict[str, Any]) -> bool:
        """验证输入"""
        target = scan_request.get("target", {})
        target_path = target.get("path")
        
        if not target_path:
            raise InputValidationError("缺少 target.path 字段")
        
        if not os.path.exists(target_path):
            raise InputValidationError(f"目标路径不存在: {target_path}")
        
        if not os.path.isdir(target_path):
            raise InputValidationError(f"目标路径必须是目录: {target_path}")
        
        return True
    
    def execute(self, scan_request: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Semgrep 扫描"""
        target = scan_request.get("target", {})
        target_path = target.get("path")
        options = scan_request.get("options", {})
        
        # 获取 Semgrep 可执行文件路径
        semgrep_path = self._get_semgrep_path()
        
        # 构建命令
        rules = options.get("rules", "auto")  # 默认使用 auto 规则集
        cmd = [
            semgrep_path,
            "scan",
            "--json",
            "--no-git-ignore"  # 扫描所有文件，不受 Git 限制
        ]
        
        # 处理规则参数：支持逗号分隔的多个规则集
        if isinstance(rules, str):
            # 如果包含逗号，分割成多个规则
            rule_list = [r.strip() for r in rules.split(",") if r.strip()]
        elif isinstance(rules, list):
            rule_list = rules
        else:
            rule_list = ["auto"]
        
        # 为每个规则添加 --config 参数
        for rule in rule_list:
            cmd.extend(["--config", rule])
        
        # 添加目标路径
        cmd.append(target_path)
        
        # 添加性能优化参数
        max_target_bytes = options.get("max_target_bytes", None)
        if max_target_bytes:
            cmd.extend(["--max-target-bytes", str(max_target_bytes)])
        
        # 添加并发任务数（加速扫描）
        jobs = options.get("jobs", None)
        if jobs:
            cmd.extend(["--jobs", str(jobs)])
        
        # 添加排除路径
        exclude_paths = options.get("exclude_paths", [])
        for exclude in exclude_paths:
            cmd.extend(["--exclude", exclude])
        
        # 默认排除常见的大文件目录
        default_excludes = [
            "node_modules",
            ".git",
            "dist",
            "build",
            "*.min.js",
            "*.bundle.js"
        ]
        for exclude in default_excludes:
            if exclude not in exclude_paths:
                cmd.extend(["--exclude", exclude])
        
        self.logger.info(f"执行命令: {' '.join(cmd)}")
        
        try:
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.get_capability().execution.timeout_seconds
            )
            
            # Semgrep 即使发现漏洞，返回码也可能不是 0
            # 因此我们不检查 returncode，而是检查输出是否有效
            if result.stdout:
                try:
                    output = json.loads(result.stdout)
                    return output
                except json.JSONDecodeError as e:
                    self.logger.error(f"解析 JSON 输出失败: {str(e)}")
                    self.logger.error(f"原始输出: {result.stdout[:500]}")
                    raise ParseError(f"Semgrep 输出不是有效的 JSON: {str(e)}")
            else:
                # 没有输出，可能是错误
                if result.stderr:
                    self.logger.error(f"Semgrep 错误输出: {result.stderr}")
                    raise ExecutionError(f"Semgrep 执行失败: {result.stderr}")
                else:
                    # 没有发现任何问题
                    return {"results": []}
        
        except subprocess.TimeoutExpired:
            raise ExecutionError(f"Semgrep 执行超时（{self.get_capability().execution.timeout_seconds}秒）")
        except Exception as e:
            raise ExecutionError(f"Semgrep 执行异常: {str(e)}")
    
    def parse_output(self, raw_output: Dict[str, Any], scan_request: Dict[str, Any]) -> List[UnifiedVulnerability]:
        """将 Semgrep 输出转换为统一漏洞模型"""
        vulnerabilities = []
        scan_session_id = scan_request.get("scan_id", "unknown")
        target_path = scan_request.get("target", {}).get("path", "")
        
        # Semgrep 的结果在 "results" 字段中
        results = raw_output.get("results", [])
        
        for index, finding in enumerate(results):
            try:
                vuln = self._parse_single_finding(finding, scan_session_id, index, target_path)
                vulnerabilities.append(vuln)
            except Exception as e:
                self.logger.warning(f"解析单个发现失败（索引 {index}）: {str(e)}")
                continue
        
        return vulnerabilities
    
    def _parse_single_finding(
        self, 
        finding: Dict[str, Any], 
        scan_session_id: str, 
        index: int,
        target_path: str
    ) -> UnifiedVulnerability:
        """解析单个 Semgrep 发现"""
        
        # 提取基本信息
        check_id = finding.get("check_id", "unknown")
        path = finding.get("path", "")
        start = finding.get("start", {})
        end = finding.get("end", {})
        extra = finding.get("extra", {})
        
        # 提取元数据
        metadata = extra.get("metadata", {})
        message = extra.get("message", "")
        severity = extra.get("severity", "WARNING")
        
        # 提取 CWE
        cwe_text = metadata.get("cwe", "")
        cwe_id = None
        if isinstance(cwe_text, str):
            cwe_id = self._extract_cwe_id(cwe_text)
        elif isinstance(cwe_text, list) and len(cwe_text) > 0:
            cwe_id = self._extract_cwe_id(cwe_text[0])
        
        # 提取 OWASP 类别（可能是列表或字符串）
        owasp_raw = metadata.get("owasp", None)
        owasp_category = None
        if owasp_raw:
            if isinstance(owasp_raw, list) and len(owasp_raw) > 0:
                owasp_category = owasp_raw[0]  # 取第一个
            elif isinstance(owasp_raw, str):
                owasp_category = owasp_raw
        
        # 构建统一漏洞模型
        return UnifiedVulnerability(
            vulnerability_id=self._generate_vulnerability_id(scan_session_id, index),
            scan_session_id=scan_session_id,
            
            vulnerability_type=VulnerabilityType(
                name=check_id.split(".")[-1].replace("-", " ").title(),
                cwe_id=cwe_id,
                owasp_category=owasp_category
            ),
            
            location=Location(
                file_path=path,
                function_name=None,  # Semgrep 不直接提供函数名
                class_name=None,
                line_start=start.get("line", 0),
                line_end=end.get("line", 0),
                column_start=start.get("col", None),
                column_end=end.get("col", None),
                code_snippet=finding.get("extra", {}).get("lines", None)
            ),
            
            severity=Severity(
                level=map_severity_to_unified(severity, "SAST"),
                score=self._severity_to_score(severity),
                exploitability=Exploitability.UNKNOWN
            ),
            
            confidence=Confidence(
                score=self._severity_to_confidence(severity),
                reason="基于 Semgrep 规则匹配"
            ),
            
            source_tool=SourceTool(
                tool_id=self.tool_id,
                rule_id=check_id,
                original_severity=severity,
                raw_output=finding
            ),
            
            description=Description(
                summary=message,
                detail=metadata.get("description", None),
                impact=metadata.get("impact", None),
                remediation=metadata.get("remediation", None)
            ),
            
            metadata=VulnerabilityMetadata(
                detected_at=datetime.now(),
                language=metadata.get("technology", [None])[0] if metadata.get("technology") else None,
                tags=self._normalize_to_list(metadata.get("category", [])),
                references=self._normalize_to_list(metadata.get("references", []))
            ),
            
            verification=Verification()
        )
    
    def _severity_to_score(self, severity: str) -> float:
        """将严重度转换为 CVSS 分数"""
        severity_map = {
            "ERROR": 8.5,
            "CRITICAL": 9.5,
            "WARNING": 6.0,
            "HIGH": 7.5,
            "INFO": 3.0,
            "MEDIUM": 5.0,
            "LOW": 2.0
        }
        return severity_map.get(severity.upper(), 5.0)
    
    def _severity_to_confidence(self, severity: str) -> int:
        """根据严重度推断置信度"""
        # Semgrep 的规则通常比较准确
        severity_confidence_map = {
            "ERROR": 90,
            "CRITICAL": 90,
            "WARNING": 80,
            "HIGH": 85,
            "INFO": 70,
            "MEDIUM": 75,
            "LOW": 70
        }
        return severity_confidence_map.get(severity.upper(), 75)
    
    def _normalize_to_list(self, value: Any) -> List[str]:
        """将值标准化为列表"""
        if value is None:
            return []
        elif isinstance(value, list):
            return value
        elif isinstance(value, str):
            return [value]
        else:
            return []


# 示例用法
if __name__ == "__main__":
    adapter = SemgrepAdapter()
    
    # 打印能力声明
    capability = adapter.get_capability()
    print("=== Semgrep 能力声明 ===")
    print(capability.model_dump_json(indent=2))
    
    # 测试扫描（需要提供真实路径）
    # scan_request = {
    #     "scan_id": "test_scan_001",
    #     "target": {
    #         "type": "LOCAL_PATH",
    #         "path": "/path/to/your/code"
    #     },
    #     "options": {
    #         "rules": "auto"
    #     }
    # }
    # 
    # vulnerabilities = adapter.run(scan_request)
    # print(f"\n发现 {len(vulnerabilities)} 个漏洞")


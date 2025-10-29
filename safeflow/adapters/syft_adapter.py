"""
Syft 工具适配器

将 Syft 软件成分分析工具集成到 SafeFlow 平台
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


class SyftAdapter(BaseAdapter):
    """Syft 适配器实现"""
    
    def __init__(self):
        super().__init__()
        self._check_syft_installed()
    
    def _check_syft_installed(self):
        """检查 Syft 是否已安装"""
        try:
            result = subprocess.run(
                ["syft", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise ExecutionError("Syft 未正确安装")
            self.logger.info(f"Syft 版本: {result.stdout.strip()}")
        except FileNotFoundError:
            raise ExecutionError(
                "未找到 Syft 命令，请从 https://github.com/anchore/syft/releases 下载安装"
            )
        except Exception as e:
            raise ExecutionError(f"检查 Syft 安装失败: {str(e)}")
    
    def get_capability(self) -> ToolCapability:
        """返回 Syft 工具能力声明"""
        return ToolCapability(
            tool_id="syft",
            tool_name="Syft",
            tool_version="0.99.0",
            tool_type=ToolType.SCA,
            vendor="Anchore Inc.",
            description="强大的软件包材料清单（SBOM）生成器和软件成分分析工具",
            
            capabilities=Capabilities(
                supported_languages=[
                    "python", "javascript", "java", "go", "ruby",
                    "rust", "php", "c", "cpp", "dotnet"
                ],
                detection_types=[
                    "vulnerable_dependency", "outdated_package",
                    "license_risk", "supply_chain_risk"
                ],
                cwe_coverage=[]  # SCA 主要关注已知 CVE，不直接映射 CWE
            ),
            
            input_requirements=InputRequirements(
                requires_source_code=True,
                requires_binary=False,
                requires_running_app=False,
                requires_dependencies_manifest=True,  # 需要如 package.json, requirements.txt 等
                supported_vcs=["git"],
                additional_config={
                    "scan_depth": "可选，扫描深度（shallow/deep）"
                }
            ),
            
            output_format=OutputFormat(
                native_format="json",
                supports_streaming=False,
                result_fields=["artifacts", "source", "distro"]
            ),
            
            execution=ExecutionConfig(
                command_template="syft scan {target_path} -o json",
                timeout_seconds=300,
                resource_requirements=ResourceRequirements(
                    min_memory_mb=256,
                    min_cpu_cores=1
                )
            ),
            
            metadata=Metadata(
                license="Apache-2.0",
                documentation_url="https://github.com/anchore/syft",
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
        
        return True
    
    def execute(self, scan_request: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Syft 扫描"""
        target = scan_request.get("target", {})
        target_path = target.get("path")
        
        # 构建命令
        cmd = [
            "syft",
            "scan",
            target_path,
            "-o", "json"
        ]
        
        self.logger.info(f"执行命令: {' '.join(cmd)}")
        
        try:
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.get_capability().execution.timeout_seconds
            )
            
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else "未知错误"
                self.logger.error(f"Syft 执行失败: {error_msg}")
                raise ExecutionError(f"Syft 执行失败: {error_msg}")
            
            if result.stdout:
                try:
                    output = json.loads(result.stdout)
                    return output
                except json.JSONDecodeError as e:
                    self.logger.error(f"解析 JSON 输出失败: {str(e)}")
                    raise ParseError(f"Syft 输出不是有效的 JSON: {str(e)}")
            else:
                return {"artifacts": []}
        
        except subprocess.TimeoutExpired:
            raise ExecutionError(
                f"Syft 执行超时（{self.get_capability().execution.timeout_seconds}秒）"
            )
        except Exception as e:
            raise ExecutionError(f"Syft 执行异常: {str(e)}")
    
    def parse_output(
        self, 
        raw_output: Dict[str, Any], 
        scan_request: Dict[str, Any]
    ) -> List[UnifiedVulnerability]:
        """
        将 Syft 输出转换为统一漏洞模型
        
        注意：Syft 本身只生成 SBOM，不直接报告漏洞。
        需要结合 Grype 或其他漏洞数据库来识别漏洞。
        这里我们提供一个基础实现，记录发现的软件包。
        """
        vulnerabilities = []
        scan_session_id = scan_request.get("scan_id", "unknown")
        
        # Syft 的软件包列表在 "artifacts" 字段中
        artifacts = raw_output.get("artifacts", [])
        
        # 由于 Syft 不直接报告漏洞，这里我们将每个包作为一个"潜在风险点"记录
        # 实际使用中，应该将 Syft 输出传递给 Grype 进行漏洞匹配
        for index, artifact in enumerate(artifacts):
            try:
                # 这里只是示例：记录包信息，不作为真实漏洞
                # 在完整实现中，应该调用漏洞数据库API
                vuln = self._create_package_record(artifact, scan_session_id, index)
                if vuln:
                    vulnerabilities.append(vuln)
            except Exception as e:
                self.logger.warning(f"解析软件包失败（索引 {index}）: {str(e)}")
                continue
        
        self.logger.info(
            f"Syft 扫描发现 {len(artifacts)} 个软件包"
            f"（注意：需要结合漏洞数据库进行漏洞匹配）"
        )
        
        return vulnerabilities
    
    def _create_package_record(
        self, 
        artifact: Dict[str, Any], 
        scan_session_id: str, 
        index: int
    ) -> UnifiedVulnerability:
        """
        创建软件包记录
        
        这是一个简化实现。完整版应该：
        1. 查询漏洞数据库（如 NVD、OSV）
        2. 匹配 CVE 信息
        3. 生成真实的漏洞记录
        """
        name = artifact.get("name", "unknown")
        version = artifact.get("version", "unknown")
        pkg_type = artifact.get("type", "unknown")
        
        # 这里只是示例：创建一个 INFO 级别的记录
        return UnifiedVulnerability(
            vulnerability_id=self._generate_vulnerability_id(scan_session_id, index),
            scan_session_id=scan_session_id,
            
            vulnerability_type=VulnerabilityType(
                name=f"依赖包发现: {name}",
                cwe_id=None,
                owasp_category=None
            ),
            
            location=Location(
                file_path=f"dependencies/{pkg_type}/{name}",
                function_name=None,
                class_name=None,
                line_start=0,
                line_end=0,
                code_snippet=None
            ),
            
            severity=Severity(
                level=SeverityLevel.INFO,
                score=0.0,
                exploitability=Exploitability.UNKNOWN
            ),
            
            confidence=Confidence(
                score=100,
                reason="Syft 直接识别的软件包"
            ),
            
            source_tool=SourceTool(
                tool_id=self.tool_id,
                rule_id=f"syft-package-{pkg_type}",
                original_severity="INFO",
                raw_output=artifact
            ),
            
            description=Description(
                summary=f"发现依赖包: {name} (版本 {version})",
                detail=f"类型: {pkg_type}, 来源: {artifact.get('foundBy', 'unknown')}",
                impact="需要进一步检查该依赖是否存在已知漏洞",
                remediation="使用漏洞数据库（如 Grype）检查此包的安全状态"
            ),
            
            metadata=VulnerabilityMetadata(
                detected_at=datetime.now(),
                language=artifact.get("language", None),
                tags=["dependency", "sbom", pkg_type],
                references=[]
            ),
            
            verification=Verification()
        )


# 示例用法
if __name__ == "__main__":
    adapter = SyftAdapter()
    
    # 打印能力声明
    capability = adapter.get_capability()
    print("=== Syft 能力声明 ===")
    print(capability.model_dump_json(indent=2))
    
    # 测试扫描（需要提供真实路径）
    # scan_request = {
    #     "scan_id": "test_scan_002",
    #     "target": {
    #         "type": "LOCAL_PATH",
    #         "path": "/path/to/your/project"
    #     }
    # }
    # 
    # vulnerabilities = adapter.run(scan_request)
    # print(f"\n发现 {len(vulnerabilities)} 个软件包")


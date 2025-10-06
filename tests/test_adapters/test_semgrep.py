"""
Semgrep 适配器单元测试
"""
import pytest
import tempfile
import os
from pathlib import Path

from safeflow.adapters.semgrep_adapter import SemgrepAdapter
from safeflow.adapters.base import InputValidationError, ExecutionError


class TestSemgrepAdapter:
    """Semgrep 适配器测试类"""
    
    @pytest.fixture
    def adapter(self):
        """创建适配器实例"""
        return SemgrepAdapter()
    
    @pytest.fixture
    def temp_project(self):
        """创建临时测试项目"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建包含漏洞的测试文件
            test_file = Path(tmpdir) / "vulnerable.py"
            test_file.write_text("""
# 这是一个包含安全漏洞的测试文件

def get_user(user_id):
    # SQL 注入漏洞
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return execute_query(query)

def render_page(user_input):
    # XSS 漏洞
    html = f"<div>{user_input}</div>"
    return html

def execute_command(cmd):
    # 命令注入漏洞
    import os
    os.system(f"ls {cmd}")
    
# 硬编码密钥
API_KEY = "sk-1234567890abcdef"
PASSWORD = "admin123"
""")
            yield tmpdir
    
    def test_get_capability(self, adapter):
        """测试获取工具能力声明"""
        capability = adapter.get_capability()
        
        assert capability.tool_name == "Semgrep"
        assert capability.tool_type.value == "SAST"
        assert "python" in capability.capabilities.supported_languages
        assert "sql_injection" in capability.capabilities.detection_types
        assert 89 in capability.capabilities.cwe_coverage  # CWE-89: SQL Injection
    
    def test_validate_input_valid(self, adapter, temp_project):
        """测试有效输入验证"""
        scan_request = {
            "scan_id": "test_001",
            "target": {
                "type": "LOCAL_PATH",
                "path": temp_project
            }
        }
        
        assert adapter.validate_input(scan_request) is True
    
    def test_validate_input_missing_path(self, adapter):
        """测试缺少路径的输入验证"""
        scan_request = {
            "scan_id": "test_002",
            "target": {
                "type": "LOCAL_PATH"
            }
        }
        
        with pytest.raises(InputValidationError):
            adapter.validate_input(scan_request)
    
    def test_validate_input_nonexistent_path(self, adapter):
        """测试不存在的路径"""
        scan_request = {
            "scan_id": "test_003",
            "target": {
                "type": "LOCAL_PATH",
                "path": "/nonexistent/path"
            }
        }
        
        with pytest.raises(InputValidationError):
            adapter.validate_input(scan_request)
    
    def test_run_scan(self, adapter, temp_project):
        """测试完整扫描流程"""
        scan_request = {
            "scan_id": "test_004",
            "target": {
                "type": "LOCAL_PATH",
                "path": temp_project
            },
            "options": {
                "rules": "auto"
            }
        }
        
        vulnerabilities = adapter.run(scan_request)
        
        # 应该能检测到多个漏洞
        assert len(vulnerabilities) > 0
        
        # 检查漏洞结构
        vuln = vulnerabilities[0]
        assert vuln.vulnerability_id is not None
        assert vuln.scan_session_id == "test_004"
        assert vuln.source_tool.tool_id == adapter.tool_id
        assert vuln.location.file_path.endswith("vulnerable.py")
        assert vuln.severity.level.value in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    
    def test_severity_mapping(self, adapter):
        """测试严重度映射"""
        assert adapter._severity_to_score("ERROR") == 8.5
        assert adapter._severity_to_score("WARNING") == 6.0
        assert adapter._severity_to_score("INFO") == 3.0
    
    def test_confidence_mapping(self, adapter):
        """测试置信度映射"""
        assert adapter._severity_to_confidence("ERROR") == 90
        assert adapter._severity_to_confidence("WARNING") == 80
        assert adapter._severity_to_confidence("INFO") == 70


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


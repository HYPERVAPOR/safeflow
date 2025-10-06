"""
SafeFlow 配置示例文件
复制此文件为 config.py 并根据实际情况修改
"""

# 应用配置
APP_NAME = "SafeFlow"
APP_VERSION = "0.1.0"
DEBUG = True

# API 配置
API_HOST = "0.0.0.0"
API_PORT = 8000

# 数据库配置
DATABASE_URL = "sqlite:///./safeflow.db"
# DATABASE_URL = "postgresql://safeflow:password@localhost:5432/safeflow"

# Redis 配置（可选）
REDIS_URL = "redis://localhost:6379/0"

# 日志配置
LOG_LEVEL = "INFO"
LOG_DIR = "./logs"

# 工具超时配置（秒）
SEMGREP_TIMEOUT = 600
SYFT_TIMEOUT = 300

# 工作目录
WORK_DIR = "/tmp/safeflow_workspace"

# 结果存储
RESULTS_DIR = "./results"

# 证据链存储
EVIDENCE_DIR = "./evidence"


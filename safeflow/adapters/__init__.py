"""
工具适配器模块

实现各种安全工具的统一接入
"""
from safeflow.adapters.base import (
    BaseAdapter,
    AdapterError,
    InputValidationError,
    ExecutionError,
    ParseError
)
from safeflow.adapters.semgrep_adapter import SemgrepAdapter
from safeflow.adapters.syft_adapter import SyftAdapter

__all__ = [
    # Base
    "BaseAdapter",
    "AdapterError",
    "InputValidationError",
    "ExecutionError",
    "ParseError",
    
    # Adapters
    "SemgrepAdapter",
    "SyftAdapter"
]


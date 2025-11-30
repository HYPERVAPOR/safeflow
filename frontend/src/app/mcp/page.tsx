'use client'

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import * as Icons from '@/components/icons';

const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false });

interface MCPServerStatus {
  name: string;
  version: string;
  initialized: boolean;
  available_tools_count: number;
  total_tools_count: number;
  tools: Record<string, any>;
}

interface MCPTool {
  name: string;
  description: string;
  category: string;
  available: boolean;
  version?: string;
  capability: {
    version?: string;
    author?: string;
    homepage?: string;
    documentation?: string;
    supported_languages?: string[];
    supported_formats?: string[];
    output_formats?: string[];
    tags?: string[];
    category?: string;
  };
  inputSchema: {
    type: 'object';
    properties: Record<string, any>;
    required: string[];
  };
}

interface ExecutionRequest {
  tool_name: string;
  arguments: Record<string, any>;
  user_id?: string;
  session_id?: string;
  workspace_dir?: string;
  timeout: number;
  enable_network: boolean;
}

interface ExecutionResult {
  success: boolean;
  tool_name: string;
  execution_time: number;
  output?: string;
  metadata?: Record<string, any>;
  error?: string;
}

interface LogEntry {
  id: string;
  timestamp: Date;
  type: 'info' | 'error' | 'success' | 'warning';
  message: string;
}

const DETAIL_TABS = [
  { id: 'overview', label: '概览', icon: 'overview' },
  { id: 'parameters', label: '参数', icon: 'parameters' }
] as const;

type DetailTab = (typeof DETAIL_TABS)[number]['id'];

type ColumnWidths = {
  left: number;
  center: number;
  right: number;
};

const TOOL_ICONS: Record<string, React.FC<{ size?: number | string; className?: string }>> = {
  static_analysis: Icons.StaticAnalysisIcon,
  dependency_analysis: Icons.DependencyAnalysisIcon,
  web_security: Icons.WebSecurityIcon,
  dynamic_analysis: Icons.DynamicAnalysisIcon,
  fuzzing: Icons.FuzzingIcon,
  observability: Icons.ObservabilityIcon,
  orchestration: Icons.OrchestrationIcon,
  unknown: Icons.UnknownToolIcon
};

const COLUMN_MIN_WIDTH: ColumnWidths = {
  left: 220,
  center: 520,
  right: 280
};

const DEFAULT_COLUMN_WIDTH: ColumnWidths = {
  left: 280,   
  center: 1200,  
  right: 280   
};

const clampValue = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value));

const formatCategory = (category: string) =>
  category
    ? category
        .split('_')
        .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1))
        .join(' ')
    : 'Uncategorized';

const sampleValueFromSchema = (schema: any): any => {
  if (!schema) return 'value';
  if (schema.example !== undefined) return schema.example;
  if (schema.enum?.length) return schema.enum[0];

  switch (schema.type) {
    case 'string':
      if (schema.format === 'uri' || schema.format === 'url') return 'https://api.example.com';
      if (schema.format === 'date-time') return new Date().toISOString();
      return schema.default ?? 'text';
    case 'number':
    case 'integer':
      return schema.default ?? schema.minimum ?? 1;
    case 'boolean':
      return schema.default ?? true;
    case 'array':
      return [sampleValueFromSchema(schema.items || { type: 'string' })];
    case 'object':
      if (schema.properties) {
        const nested: Record<string, any> = {};
        Object.entries(schema.properties).forEach(([key, value]) => {
          nested[key] = sampleValueFromSchema(value);
        });
        return nested;
      }
      return {};
    default:
      return 'value';
  }
};

const buildExampleArguments = (tool: MCPTool) => {
  // 为 semgrep 提供专门优化的示例
  if (tool.name === 'semgrep') {
    const semgrepExample = {
      "target_path": ".",
      "config": "auto",
      "severity": "ERROR",
      "output_format": "json",
      "include": ["*.py"],
      "exclude": ["**/test_*.py", "__pycache__", "*.test.js", "*.spec.ts", "node_modules", "vendor", ".git"],
      "timeout": 300
    };
    return JSON.stringify(semgrepExample, null, 2);
  }

  // 为 trivy 提供专门优化的示例
  if (tool.name === 'trivy') {
    const trivyExample = {
      "target": ".",
      "scan_type": "fs",
      "severity": ["MEDIUM", "HIGH", "CRITICAL"],
      "security_checks": ["vuln", "config"],
      "output_format": "json",
      "timeout": 300
    };
    return JSON.stringify(trivyExample, null, 2);
  }

  // 为 owasp_zap 提供专门优化的示例
  if (tool.name === 'owasp_zap') {
    const zapExample = {
      "target_url": "https://httpbin.org/",
      "scan_type": "quick",
      "auth_type": "none",
      "output_format": "json",
      "timeout": 300
    };
    return JSON.stringify(zapExample, null, 2);
  }

  // 为其他工具使用自动生成的示例
  const props = tool.inputSchema?.properties || {};
  if (Object.keys(props).length === 0) return '';

  const payload: Record<string, any> = {};
  Object.entries(props).forEach(([key, schema]) => {
    payload[key] = sampleValueFromSchema(schema);
  });
  return JSON.stringify(payload, null, 2);
};

const getToolIcon = (category: string) => TOOL_ICONS[category] || TOOL_ICONS.unknown;

const renderToolIcon = (category: string, size: number | string = 20, className: string = '') => {
  const IconComponent = getToolIcon(category);
  return <IconComponent size={size} className={className} />;
};

const renderIcon = (iconType: string, size: number | string = 16, className: string = '') => {
  switch (iconType) {
    case 'overview':
      return <Icons.OverviewIcon size={size} className={className} />;
    case 'parameters':
      return <Icons.ParametersIcon size={size} className={className} />;
    default:
      return null;
  }
};

const renderStatusIcon = (iconType: string, size: number | string = 16, className: string = '') => {
  switch (iconType) {
    case 'StatusSuccessIcon':
      return <Icons.StatusSuccessIcon size={size} className={className} />;
    case 'StatusErrorIcon':
      return <Icons.StatusErrorIcon size={size} className={className} />;
    case 'StatusWarningIcon':
      return <Icons.StatusWarningIcon size={size} className={className} />;
    case 'StatusRunningIcon':
      return <Icons.StatusRunningIcon size={size} className={className} />;
    default:
      return null;
  }
};

const calculateSchemaEditorHeight = (schema: any) => {
  const lines = JSON.stringify(schema, null, 2).split('\n').length;
  const lineHeight = 20; // Monaco编辑器的大概行高（像素）
  const padding = 40; // 上下padding
  const calculatedHeight = Math.max(120, lines * lineHeight + padding);
  return `${calculatedHeight}px`;
};

export default function MCPInspectorPage() {
  const [serverStatus, setServerStatus] = useState<MCPServerStatus | null>(null);
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [selectedTool, setSelectedTool] = useState<MCPTool | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [detailTab, setDetailTab] = useState<DetailTab>('overview');
  const [executionForm, setExecutionForm] = useState<ExecutionRequest>({
    tool_name: '',
    arguments: {},
    timeout: 300,
    enable_network: false
  });
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [jsonInput, setJsonInput] = useState('');
  const [schemaInput, setSchemaInput] = useState('');
  const [schemaEditorHeight, setSchemaEditorHeight] = useState('120px');
  const [responseTime, setResponseTime] = useState<number | null>(null);
  const [copyState, setCopyState] = useState<'request' | 'response' | 'schema' | null>(null);
  const [columnWidths, setColumnWidths] = useState<ColumnWidths>(DEFAULT_COLUMN_WIDTH);

  const logCounterRef = useRef(0);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const executionStartTime = useRef<number>(0);
  const columnDragState = useRef<{ edge: 'left' | 'right' | null; startX: number; startWidths: ColumnWidths }>(
    { edge: null, startX: 0, startWidths: DEFAULT_COLUMN_WIDTH }
  );

  // Removed auto-scroll to console - users want manual control

  useEffect(() => {
    if (!copyState) return;
    const timer = setTimeout(() => setCopyState(null), 1200);
    return () => clearTimeout(timer);
  }, [copyState]);

  const addLog = useCallback((message: string, type: LogEntry['type'] = 'info') => {
    const logEntry: LogEntry = {
      id: `log-${++logCounterRef.current}-${Date.now()}`,
      timestamp: new Date(),
      type,
      message
    };
    setLogs((prev) => [...prev.slice(-100), logEntry]);
  }, []);

  const loadServerStatus = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      addLog('正在连接 MCP 服务器...');

      const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      const [statusResponse, toolsResponse] = await Promise.all([
        fetch(`${apiBaseUrl}/api/v1/mcp/status`),
        fetch(`${apiBaseUrl}/api/v1/mcp/tools?available_only=false`)
      ]);

      if (!statusResponse.ok || !toolsResponse.ok) {
        throw new Error('无法获取服务器状态');
      }

      const statusData = await statusResponse.json();
      const toolsData = await toolsResponse.json();

      setServerStatus(statusData);
      addLog('连接成功，载入工具列表', 'success');

      const toolList = (toolsData.tools || []).map((tool: any) => ({
        name: tool.name,
        description: tool.description,
        category: tool.capability?.category || tool.category || 'unknown',
        available: tool.available !== false,
        version: tool.capability?.version || 'Unknown',
        capability: tool.capability || {},
        inputSchema: tool.inputSchema || { type: 'object', properties: {}, required: [] }
      }));

      setTools(toolList);
      addLog(`已载入 ${toolList.filter((t: MCPTool) => t.available).length}/${toolList.length} 个可用工具`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '未知错误';
      setError(errorMessage);
      addLog(`连接失败: ${errorMessage}`, 'error');
    } finally {
      setLoading(false);
    }
  }, [addLog]);

  useEffect(() => {
    loadServerStatus();
  }, [loadServerStatus]);

  useEffect(() => {
    if (!selectedTool && tools.length > 0) {
      setSelectedTool(tools[0]);
    }
  }, [tools, selectedTool]);

  useEffect(() => {
    if (!selectedTool) return;
    setExecutionForm((prev) => ({
      ...prev,
      tool_name: selectedTool.name,
      arguments: {}
    }));
    setJsonInput(buildExampleArguments(selectedTool));
    setSchemaInput(JSON.stringify(selectedTool.inputSchema, null, 2));
    setSchemaEditorHeight(calculateSchemaEditorHeight(selectedTool.inputSchema));
    setExecutionResult(null);
    setResponseTime(null);
    setDetailTab('overview');
  }, [selectedTool]);

  const handleCopy = useCallback(
    (type: 'request' | 'response' | 'schema') => {
      if (type === 'request' && !jsonInput.trim()) return;
      if (type === 'response' && !executionResult) return;
      if (type === 'schema' && !schemaInput.trim()) return;
      let text = '';
      if (type === 'request') text = jsonInput;
      else if (type === 'response') text = JSON.stringify(executionResult, null, 2);
      else if (type === 'schema') text = schemaInput;
      navigator.clipboard?.writeText(text).then(() => setCopyState(type));
    },
    [jsonInput, executionResult, schemaInput]
  );

  const filteredTools = useMemo(
    () =>
      tools.filter((tool) =>
        tool.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        tool.description.toLowerCase().includes(searchTerm.toLowerCase())
      ),
    [tools, searchTerm]
  );

  const groupedTools = useMemo(() => {
    return filteredTools.reduce((acc, tool) => {
      const key = tool.category || 'unknown';
      acc[key] = acc[key] ? [...acc[key], tool] : [tool];
      return acc;
    }, {} as Record<string, MCPTool[]>);
  }, [filteredTools]);

  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});

  useEffect(() => {
    setExpandedGroups((prev) => {
      const clone = { ...prev };
      Object.keys(groupedTools).forEach((key) => {
        if (clone[key] === undefined) {
          clone[key] = true;
        }
      });
      return clone;
    });
  }, [groupedTools]);

  const executeTool = useCallback(async () => {
    if (!selectedTool || !selectedTool.available) return;

    let parsedArguments: Record<string, any> = executionForm.arguments;
    if (jsonInput.trim()) {
      try {
        parsedArguments = JSON.parse(jsonInput);
      } catch (parseError) {
        addLog('JSON 参数解析失败，请检查格式', 'error');
        setExecutionResult({
          success: false,
          tool_name: selectedTool.name,
          execution_time: 0,
          error: 'JSON 解析失败'
        });
        return;
      }
    }

    try {
      setIsExecuting(true);
      setExecutionResult(null);
      setResponseTime(null);
      executionStartTime.current = Date.now();
      addLog(`执行 ${selectedTool.name} 中...`);

      const requestBody = {
        ...executionForm,
        tool_name: selectedTool.name,
        arguments: parsedArguments
      };

      const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      const response = await fetch(`${apiBaseUrl}/api/v1/mcp/tools/${selectedTool.name}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || '执行失败');
      }

      const timeTaken = Date.now() - executionStartTime.current;
      setResponseTime(timeTaken);
      setExecutionResult(result);
      addLog(`执行成功 (${timeTaken}ms)`, 'success');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '执行失败';
      const timeTaken = Date.now() - executionStartTime.current;
      setResponseTime(timeTaken);
      setExecutionResult({
        success: false,
        tool_name: selectedTool?.name || 'unknown',
        execution_time: timeTaken / 1000,
        error: errorMessage
      });
      addLog(`执行失败: ${errorMessage}`, 'error');
    } finally {
      setIsExecuting(false);
    }
  }, [selectedTool, executionForm, jsonInput, addLog]);

  const handleColumnDragStart = useCallback(
    (event: React.MouseEvent<HTMLDivElement>, edge: 'left' | 'right') => {
      event.preventDefault();
      columnDragState.current = {
        edge,
        startX: event.clientX,
        startWidths: columnWidths
      };
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    },
    [columnWidths]
  );

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      const state = columnDragState.current;
      if (!state.edge) return;
      const delta = event.clientX - state.startX;

      if (state.edge === 'left') {
        const total = state.startWidths.left + state.startWidths.center;
        const newLeft = clampValue(
          state.startWidths.left + delta,
          COLUMN_MIN_WIDTH.left,
          total - COLUMN_MIN_WIDTH.center
        );
        const newCenter = total - newLeft;
        setColumnWidths((prev) => {
          if (prev.left === newLeft && prev.center === newCenter) return prev;
          return { ...prev, left: newLeft, center: newCenter };
        });
      } else {
        // 调整中间和右栏之间的分隔条
        const totalWidth = window.innerWidth;
        const leftWidth = sidebarCollapsed ? 72 : state.startWidths.left;
        const separatorWidth = 6; // 两个分隔条的总宽度
        const minRightWidth = COLUMN_MIN_WIDTH.right;

        // 计算新的中间栏宽度，确保右栏在合理范围内
        const newCenter = clampValue(
          state.startWidths.center + delta,
          COLUMN_MIN_WIDTH.center,
          totalWidth - leftWidth - minRightWidth - separatorWidth
        );

        setColumnWidths((prev) => {
          if (prev.center === newCenter) return prev;
          // 计算右栏的实际宽度（用于显示，虽然实际使用 flex: 1）
          const actualRightWidth = totalWidth - leftWidth - newCenter - separatorWidth;
          return { ...prev, center: newCenter, right: Math.max(minRightWidth, actualRightWidth) };
        });
      }
    };

    const handleMouseUp = () => {
      if (!columnDragState.current.edge) return;
      columnDragState.current = { ...columnDragState.current, edge: null };
      document.body.style.removeProperty('cursor');
      document.body.style.removeProperty('user-select');
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  const availabilityRatio = serverStatus?.total_tools_count
    ? serverStatus.available_tools_count / serverStatus.total_tools_count
    : 0;
  const ringCircumference = 2 * Math.PI * 36;
  const ringOffset = ringCircumference * (1 - availabilityRatio);

  const statusMeta = useMemo(() => {
    if (!serverStatus) return { label: '未连接', tone: 'warning', icon: 'StatusWarningIcon' };
    if (!serverStatus.initialized) return { label: '异常', tone: 'error', icon: 'StatusErrorIcon' };
    if (availabilityRatio < 0.5) return { label: '警告', tone: 'warning', icon: 'StatusWarningIcon' };
    return { label: '运行中', tone: 'success', icon: 'StatusSuccessIcon' };
  }, [serverStatus, availabilityRatio]);

  return (
    <div className="h-screen w-screen bg-gray-950 text-gray-200 overflow-hidden flex flex-col">
      <header className="flex-shrink-0 border-b border-gray-700 bg-gray-900/95 backdrop-blur-sm">
        <div className="flex items-center justify-between px-8 py-4">
          <div className="flex items-center space-x-4">
            <Link href="/" className="flex items-center space-x-1 text-gray-400 hover:text-gray-100 transition-colors text-sm">
              <Icons.ChevronLeftIcon size={16} />
              <span>返回首页</span>
            </Link>
            <div>
              <p className="text-xs uppercase tracking-[0.4em] text-gray-500">MCP Inspector</p>
              <h1 className="text-2xl font-semibold text-gradient">Server Control Plane</h1>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            {serverStatus?.version && (
              <div className="text-xs text-gray-500 uppercase tracking-wide">v{serverStatus.version}</div>
            )}
            <div className="flex items-center space-x-2 rounded-full border border-gray-700 px-4 py-2">
              <span
                className={`w-2.5 h-2.5 rounded-full breathing-dot ${
                  statusMeta.tone === 'success'
                    ? 'bg-green-500'
                    : statusMeta.tone === 'warning'
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
                }`}
              ></span>
              <span className="text-sm text-gray-300">
                {statusMeta.label}
              </span>
            </div>
            <button onClick={loadServerStatus} disabled={loading} className="btn btn-secondary">
              {loading ? <Icons.LoadingSpinner size={16} /> : <Icons.RefreshIcon size={16} />}
            </button>
          </div>
        </div>
        {error && (
          <div className="px-8 py-2 text-sm text-gray-error bg-red-500/10 border-t border-night-error/30">
            {error}
          </div>
        )}
      </header>

      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-hidden">
          <div className="flex h-full w-full overflow-hidden">
            {/* Tool List */}
            <aside
              style={{ width: sidebarCollapsed ? 72 : columnWidths.left, flexShrink: 0 }}
              className="h-full border-r border-gray-700 bg-gray-800 flex flex-col"
            >
              <div className="flex items-center justify-between px-4 py-4 border-b border-gray-700 bg-night-750/30">
                {!sidebarCollapsed && (
                  <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wide">工具集</p>
                    <p className="text-gray-300 text-sm">
                      {serverStatus?.available_tools_count ?? 0}/{serverStatus?.total_tools_count ?? 0} 可用
                    </p>
                  </div>
                )}
                <button
                  onClick={() => setSidebarCollapsed((prev) => !prev)}
                  className="rounded-full border border-gray-700 text-gray-400 hover:text-gray-100 hover:border-night-500 transition-colors p-2"
                >
                  {sidebarCollapsed ? <Icons.ChevronRightIcon size={12} /> : <Icons.ChevronLeftIcon size={12} />}
                </button>
              </div>

              {!sidebarCollapsed && (
                <div className="px-4 py-3 border-b border-gray-700 bg-night-750/20">
                  <div className="relative">
                    <Icons.SearchIcon
                      size={14}
                      className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500"
                    />
                    <input
                      type="text"
                      placeholder="搜索工具..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="input text-sm pl-10"
                    />
                  </div>
                </div>
              )}

              <div className="flex-1 overflow-y-auto px-3 pb-6 scrollbar-custom">
                {loading ? (
                  <div className="flex flex-col space-y-3 py-6">
                    {Array.from({ length: 6 }).map((_, idx) => (
                      <div key={idx} className="skeleton h-14 rounded-xl" />
                    ))}
                  </div>
                ) : filteredTools.length === 0 ? (
                  <div className="text-center text-sm text-gray-500 mt-10">没有匹配的工具</div>
                ) : (
                  Object.entries(groupedTools).map(([category, categoryTools]) => (
                    <div key={category} className="mb-4">
                      <button
                        className="flex w-full items-center justify-between text-xs uppercase tracking-wide text-gray-500 hover:text-gray-200 transition-colors"
                        onClick={() =>
                          setExpandedGroups((prev) => ({ ...prev, [category]: !prev[category] }))
                        }
                      >
                        <span className="flex items-center space-x-2">
                          <span className="w-7 h-7 rounded-xl bg-gray-800 border border-gray-700 flex items-center justify-center">
                            {renderToolIcon(category, 16)}
                          </span>
                          {!sidebarCollapsed && <span>{formatCategory(category)}</span>}
                        </span>
                        {!sidebarCollapsed && (
                          <span className="text-gray-600">
                            {expandedGroups[category] ? <Icons.ChevronDownIcon size={12} /> : <Icons.ChevronRightIcon size={12} />}
                          </span>
                        )}
                      </button>
                      {expandedGroups[category] && (
                        <div className="mt-3 space-y-2">
                          {categoryTools.map((tool) => (
                            <div
                              key={tool.name}
                              onClick={() => setSelectedTool(tool)}
                              className={`rounded-2xl border px-3 py-3 cursor-pointer transition-all duration-200 hover:border-blue-400/60 hover:bg-blue-500/5 ${
                                selectedTool?.name === tool.name
                                  ? 'border-blue-400 bg-blue-500/10 shadow-glow-blue'
                                  : 'border-gray-700 bg-gray-900/40'
                              }`}
                            >
                              <div className="flex items-center justify-between">
                                <div className="font-medium text-gray-100 truncate">{tool.name}</div>
                                <span className={tool.available ? 'text-green-500' : 'text-red-500'}>
                                  {renderStatusIcon(
                                    tool.available ? 'StatusSuccessIcon' : 'StatusErrorIcon',
                                    10
                                  )}
                                </span>
                              </div>
                              {!sidebarCollapsed && (
                                <>
                                  <p className="text-xs text-gray-500 line-clamp-2 mt-1">{tool.description}</p>
                                  <div className="mt-2 flex items-center justify-between text-[11px] text-gray-500">
                                    <span>{tool.version}</span>
                                    <span>{formatCategory(tool.category)}</span>
                                  </div>
                                </>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </aside>

            {/* Divider */}
            <div
              role="separator"
              onMouseDown={(event) => handleColumnDragStart(event, 'left')}
              className="flex items-center justify-center w-3 cursor-col-resize select-none border-r border-gray-700/50 bg-night-700/30 hover:bg-night-600/50 transition-colors"
            >
              <div className="h-16 w-0.5 rounded-full bg-night-600/50" />
            </div>

            {/* Tool details */}
            <main
              style={{ width: columnWidths.center, flexShrink: 0 }}
              className="h-full overflow-hidden px-6 py-6 bg-gray-850"
            >
              <div className="h-full overflow-y-auto space-y-6 scrollbar-custom pr-2">
                <section className="glass-panel p-5 flex items-center justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-gray-500">服务可用性</p>
                    <p className="text-2xl font-semibold text-gray-100 mt-2">
                      {(availabilityRatio * 100).toFixed(0)}%
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {serverStatus?.available_tools_count ?? 0} / {serverStatus?.total_tools_count ?? 0} 工具在线
                    </p>
                  </div>
                  <svg width="96" height="96" viewBox="0 0 96 96" className="-rotate-90">
                    <circle cx="48" cy="48" r="36" stroke="rgba(255,255,255,0.08)" strokeWidth="8" fill="none" />
                    <circle
                      cx="48"
                      cy="48"
                      r="36"
                      stroke="#06b6d4"
                      strokeWidth="8"
                      strokeDasharray={`${ringCircumference}`}
                      strokeDashoffset={`${ringOffset}`}
                      strokeLinecap="round"
                      fill="none"
                    />
                  </svg>
                </section>

                {selectedTool ? (
                  <section key={selectedTool.name} className="space-y-6 animate-tool-panel">
                    <div className="glass-panel p-6">
                      <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
                        <div className="space-y-3">
                          <div className="flex items-center space-x-3">
                            <div className="tool-icon text-2xl">{renderToolIcon(selectedTool.category, 28)}</div>
                            <div>
                              <h2 className="text-2xl font-semibold text-gray-100">{selectedTool.name}</h2>
                              <p className="text-gray-500 text-sm">{selectedTool.capability.author || '未知作者'}</p>
                            </div>
                          </div>
                          <div className="flex flex-wrap items-center gap-3 text-sm">
                            <span
                              className={`status-badge ${
                                selectedTool.available ? 'status-badge-success' : 'status-badge-error'
                              }`}
                            >
                              {selectedTool.available ? '可用' : '不可用'}
                            </span>
                            <span className="inline-flex items-center rounded-full border border-gray-700 px-3 py-1 text-xs text-gray-400">
                              v{selectedTool.version}
                            </span>
                            <span className="text-gray-400">{formatCategory(selectedTool.category)}</span>
                          </div>
                        </div>
                        <div className="flex items-center space-x-3">
                          {selectedTool.capability.documentation && (
                            <Link href={selectedTool.capability.documentation} target="_blank" className="btn btn-ghost text-sm flex items-center space-x-1">
                              <Icons.DocumentationIcon size={14} />
                              <span>文档</span>
                            </Link>
                          )}
                          {selectedTool.capability.homepage && (
                            <Link href={selectedTool.capability.homepage} target="_blank" className="btn btn-ghost text-sm flex items-center space-x-1">
                              <Icons.ExternalLinkIcon size={14} />
                              <span>官网</span>
                            </Link>
                          )}
                        </div>
                      </div>

                      <div className="mt-6 flex flex-wrap gap-2">
                        {DETAIL_TABS.map((tab) => (
                          <button
                            key={tab.id}
                            onClick={() => setDetailTab(tab.id)}
                            className={`nav-item transition-all duration-150 transform active:scale-95 hover:scale-105 cursor-pointer ${
                              detailTab === tab.id ? 'nav-item-active' : 'nav-item-inactive'
                            }`}
                          >
                            <span className="mr-2">{renderIcon(tab.icon, 14)}</span>
                            {tab.label}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="glass-panel p-6">
                      {detailTab === 'overview' ? (
                        <div className="space-y-6 notion-block">
                          <div>
                            <h3 className="text-lg font-semibold mb-2">工具简介</h3>
                            <p>{selectedTool.description}</p>
                          </div>
                          <div className="grid gap-4 md:grid-cols-2">
                            <div className="rounded-2xl border border-gray-700 bg-gray-900/40 p-4 space-y-3">
                              <h4 className="text-sm text-gray-400 uppercase tracking-wide">基础信息</h4>
                              <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                  <span className="text-gray-500">版本</span>
                                  <span className="font-mono text-gray-100">{selectedTool.capability.version || '未标注'}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-500">作者</span>
                                  <span className="text-gray-100">{selectedTool.capability.author || '未知'}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-500">分类</span>
                                  <span className="text-gray-100">{formatCategory(selectedTool.category)}</span>
                                </div>
                              </div>
                            </div>
                            <div className="rounded-2xl border border-gray-700 bg-gray-900/40 p-4 space-y-3">
                              <h4 className="text-sm text-gray-400 uppercase tracking-wide">能力标签</h4>
                              <div className="space-y-2 text-sm">
                                <div>
                                  <p className="text-gray-500">语言支持</p>
                                  <div className="mt-1 flex flex-wrap gap-2">
                                    {selectedTool.capability.supported_languages?.map((lang) => (
                                      <span
                                        key={lang}
                                        className="px-2 py-0.5 rounded-full bg-gray-800 border border-gray-700 text-xs"
                                      >
                                        {lang}
                                      </span>
                                    )) || <span className="text-gray-600">未提供</span>}
                                  </div>
                                </div>
                                <div>
                                  <p className="text-gray-500">输出格式</p>
                                  <div className="mt-1 flex flex-wrap gap-2">
                                    {selectedTool.capability.output_formats?.map((format) => (
                                      <span
                                        key={format}
                                        className="px-2 py-0.5 rounded-full bg-gray-800 border border-gray-700 text-xs"
                                      >
                                        {format}
                                      </span>
                                    )) || <span className="text-gray-600">未提供</span>}
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>

                          {selectedTool.capability.tags && selectedTool.capability.tags.length > 0 && (
                            <div>
                              <h4 className="text-sm text-gray-400 uppercase tracking-wide mb-2">标签</h4>
                              <div className="flex flex-wrap gap-2">
                                {selectedTool.capability.tags.map((tag) => (
                                  <span
                                    key={tag}
                                    className="px-3 py-1 rounded-full bg-night-accent/10 text-gray-accent text-xs font-medium"
                                  >
                                    #{tag}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <h4 className="text-sm font-medium text-gray-200">输入 Schema</h4>
                              <button
                                onClick={() => handleCopy('schema')}
                                className="text-xs text-gray-accent hover:text-white transition-colors flex items-center space-x-1"
                                disabled={!schemaInput.trim()}
                              >
                                <Icons.CopyIcon size={12} />
                                <span>{copyState === 'schema' ? '已复制' : '复制'}</span>
                              </button>
                            </div>
                            <div className="rounded-2xl border border-gray-700/50 bg-[#000000]/95 overflow-hidden">
                              <MonacoEditor
                                height={schemaEditorHeight}
                                defaultLanguage="json"
                                theme="vs-dark"
                                value={schemaInput}
                                onChange={(value) => setSchemaInput(value ?? '')}
                                options={{
                                  readOnly: true,
                                  minimap: { enabled: false },
                                  fontSize: 13,
                                  fontLigatures: true,
                                  fontFamily: 'JetBrains Mono, monospace',
                                  scrollBeyondLastLine: false,
                                  smoothScrolling: true,
                                  renderLineHighlight: 'all',
                                  automaticLayout: true,
                                  lineNumbers: 'on',
                                  glyphMargin: true,
                                  folding: false,
                                  contextmenu: false,
                                  scrollbar: {
                                    vertical: 'hidden',
                                    horizontal: 'hidden',
                                    handleMouseWheel: false
                                  },
                                  colorDecorators: true,
                                }}
                              />
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-4">
                          {selectedTool.inputSchema && Object.keys(selectedTool.inputSchema.properties).length > 0 ? (
                            Object.entries(selectedTool.inputSchema.properties).map(([paramName, paramConfig]: [string, any]) => {
                              const isRequired = selectedTool.inputSchema.required.includes(paramName);
                              return (
                                <div
                                  key={paramName}
                                  className={`rounded-2xl border px-4 py-4 transition-colors ${
                                    isRequired
                                      ? 'border-night-accent/40 bg-night-accent/5'
                                      : 'border-gray-700 bg-gray-900/30'
                                  }`}
                                >
                                  <div className="flex items-center justify-between">
                                    <span className="font-mono text-gray-100">{paramName}</span>
                                    <span
                                      className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                                        isRequired
                                          ? 'bg-red-500/20 text-gray-error'
                                          : 'bg-yellow-500/20 text-gray-warning'
                                      }`}
                                    >
                                      {isRequired ? '必填' : '可选'}
                                    </span>
                                  </div>
                                  <div className="mt-2 text-xs text-gray-500 uppercase tracking-wide">
                                    类型：{paramConfig.type || '未知'}
                                  </div>
                                  {paramConfig.description && (
                                    <p className="mt-2 text-sm text-gray-300">{paramConfig.description}</p>
                                  )}
                                </div>
                              );
                            })
                          ) : (
                            <div className="text-center text-gray-500 py-10">该工具无需额外参数</div>
                          )}
                        </div>
                      )}
                    </div>
                  </section>
                ) : (
                  <div className="glass-panel p-12 text-center">
                    <div className="text-4xl mb-4 text-gray-400">
                      <Icons.CompassIcon size={32} />
                    </div>
                    <h2 className="text-xl font-semibold mb-2">请选择一个工具</h2>
                    <p className="text-gray-500">从左侧列表中选择工具以查看详情并进行调用测试。</p>
                  </div>
                )}
              </div>
            </main>

            {/* Divider */}
            <div
              role="separator"
              onMouseDown={(event) => handleColumnDragStart(event, 'right')}
              className="flex items-center justify-center w-3 cursor-col-resize select-none border-l border-gray-700/50 bg-night-700/30 hover:bg-night-600/50 transition-colors"
            >
              <div className="h-16 w-0.5 rounded-full bg-night-600/50" />
            </div>

            {/* Try it out */}
            <section
              style={{ flex: 1, minWidth: COLUMN_MIN_WIDTH.right }}
              className="h-full border-l border-gray-700 bg-gray-900 flex flex-col"
            >
              <div className="p-6 border-b border-gray-700 bg-night-750/30 flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-wide text-gray-500">Try It Out</p>
                  <h3 className="text-lg font-semibold text-gray-100">实时调用</h3>
                </div>
                <button
                  onClick={executeTool}
                  disabled={!selectedTool || !selectedTool.available || isExecuting}
                  className="btn btn-primary"
                >
                  {isExecuting ? (
                    <>
                      <Icons.LoadingSpinner size={14} className="mr-2" />
                      执行中...
                    </>
                  ) : (
                    <>
                      <Icons.ExecuteIcon size={14} className="mr-2" />
                      Execute
                    </>
                  )}
                </button>
              </div>

              {selectedTool ? (
                <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 scrollbar-custom">
                  <div className="rounded-2xl border border-gray-700 bg-gray-900/50 p-4 space-y-3">
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <label className="text-gray-500">
                        Timeout (s)
                        <input
                          type="number"
                          min={30}
                          max={3600}
                          value={executionForm.timeout}
                          onChange={(e) =>
                            setExecutionForm((prev) => ({
                              ...prev,
                              timeout: Number(e.target.value) || 300
                            }))
                          }
                          className="input mt-1"
                        />
                      </label>
                      <label className="text-gray-500">
                        Session Id
                        <input
                          type="text"
                          value={executionForm.session_id || ''}
                          onChange={(e) =>
                            setExecutionForm((prev) => ({
                              ...prev,
                              session_id: e.target.value || undefined
                            }))
                          }
                          className="input mt-1"
                        />
                      </label>
                      <label className="text-gray-500">
                        User Id
                        <input
                          type="text"
                          value={executionForm.user_id || ''}
                          onChange={(e) =>
                            setExecutionForm((prev) => ({
                              ...prev,
                              user_id: e.target.value || undefined
                            }))
                          }
                          className="input mt-1"
                        />
                      </label>
                      <label className="text-gray-500">
                        Workspace
                        <input
                          type="text"
                          value={executionForm.workspace_dir || ''}
                          onChange={(e) =>
                            setExecutionForm((prev) => ({
                              ...prev,
                              workspace_dir: e.target.value || undefined
                            }))
                          }
                          className="input mt-1"
                        />
                      </label>
                    </div>
                    <label className="inline-flex items-center space-x-2 text-sm text-gray-300">
                      <input
                        type="checkbox"
                        checked={executionForm.enable_network}
                        onChange={(e) =>
                          setExecutionForm((prev) => ({
                            ...prev,
                            enable_network: e.target.checked
                          }))
                        }
                      />
                      <span>允许网络访问</span>
                    </label>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-sm font-medium text-gray-200">请求体 (JSON)</h4>
                        <p className="text-xs text-gray-500">Monaco 编辑器自动高亮并提供滚动</p>
                      </div>
                      <button
                        onClick={() => handleCopy('request')}
                        className="text-xs text-gray-accent hover:text-white transition-colors flex items-center space-x-1"
                        disabled={!jsonInput.trim()}
                      >
                        <Icons.CopyIcon size={12} />
                        <span>{copyState === 'request' ? '已复制' : '复制'}</span>
                      </button>
                    </div>
                    <div className="rounded-2xl border border-gray-700/50 bg-[#000000]/95 overflow-hidden">
                      <MonacoEditor
                        height="320px"
                        defaultLanguage="json"
                        theme="vs-dark"
                        value={jsonInput}
                        onChange={(value) => setJsonInput(value ?? '')}
                        options={{
                          minimap: { enabled: false },
                          fontSize: 13,
                          fontLigatures: true,
                          fontFamily: 'JetBrains Mono, monospace',
                          scrollBeyondLastLine: false,
                          smoothScrolling: true,
                          renderLineHighlight: 'all',
                          automaticLayout: true,
                          lineNumbers: 'on',
                          glyphMargin: true,
                          folding: false,
                          contextmenu: false,
                          scrollbar: {
                            vertical: 'auto',
                            horizontal: 'auto',
                            verticalScrollbarSize: 8,
                            horizontalScrollbarSize: 8
                          },
                          colorDecorators: true,
                          lineNumbersMinChars: 3
                        }}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-medium text-gray-200">响应</h4>
                      <div className="flex items-center space-x-2 text-xs text-gray-500">
                        {responseTime !== null && <span>{responseTime}ms</span>}
                        <button
                          onClick={() => handleCopy('response')}
                          className="text-gray-accent hover:text-white transition-colors flex items-center space-x-1"
                          disabled={!executionResult}
                        >
                          <Icons.CopyIcon size={12} />
                          <span>{copyState === 'response' ? '已复制' : '复制'}</span>
                        </button>
                      </div>
                    </div>
                    <div className="rounded-2xl border border-gray-700 bg-gray-900/60 p-4 h-64 overflow-auto scrollbar-custom">
                      {isExecuting && !executionResult ? (
                        <div className="space-y-3">
                          <div className="loading-bar" />
                          <div className="loading-bar w-2/3" />
                          <div className="loading-bar w-1/2" />
                        </div>
                      ) : executionResult ? (
                        <>
                          <div className="flex items-center justify-between text-xs mb-3">
                            <div className="flex items-center space-x-2">
                              <span className={executionResult.success ? 'text-green-500' : 'text-red-500'}>
                                {renderStatusIcon(
                                  executionResult.success ? 'StatusSuccessIcon' : 'StatusErrorIcon',
                                  12
                                )}
                              </span>
                              <span
                                className={`status-badge ${
                                  executionResult.success ? 'status-badge-success' : 'status-badge-error'
                                }`}
                              >
                                {executionResult.success ? 'Success' : 'Error'}
                              </span>
                            </div>
                            <span className="text-gray-500">耗时 {executionResult.execution_time.toFixed(2)}s</span>
                          </div>
                          {executionResult.error && (
                            <p className="text-gray-error text-sm mb-2">{executionResult.error}</p>
                          )}
                          <pre className="text-xs text-gray-200 whitespace-pre-wrap font-mono">
                            {JSON.stringify(executionResult, null, 2)}
                          </pre>
                        </>
                      ) : (
                        <div className="text-sm text-gray-500 h-full flex items-center justify-center">
                          暂无响应，执行后将在此展示。
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex items-center justify-center text-gray-500">选择工具后可实时调试</div>
              )}
            </section>
          </div>
        </div>

        {/* Console footer */}
        <div className="border-t border-gray-700 bg-gray-900 h-56 flex-shrink-0">
          <div className="flex items-center justify-between px-6 py-3">
            <div className="flex items-center space-x-2">
              <Icons.ConsoleIcon size={16} />
              <h4 className="text-sm font-medium text-gray-200">Console Logs</h4>
            </div>
            <button onClick={() => setLogs([])} className="text-xs text-gray-500 hover:text-gray-200 transition-colors flex items-center space-x-1">
              <Icons.CloseIcon size={12} />
              <span>清空</span>
            </button>
          </div>
          <div className="h-[calc(100%-48px)] overflow-y-auto space-y-2 text-xs font-mono px-6 pb-4">
            {logs.length === 0 ? (
              <div className="text-gray-600 text-center py-6">暂无日志</div>
            ) : (
              logs.map((log) => (
                <div key={log.id} className="leading-relaxed">
                  <span className="text-gray-500">[{log.timestamp.toLocaleTimeString([], { hour12: false })}]</span>{' '}
                  <span
                    className={
                      log.type === 'error'
                        ? 'text-red-400'
                        : log.type === 'success'
                        ? 'text-green-400'
                        : log.type === 'warning'
                        ? 'text-yellow-400'
                        : 'text-gray-300'
                    }
                  >
                    {log.message}
                  </span>
                </div>
              ))
            )}
            <div ref={logsEndRef} />
          </div>
        </div>
      </div>
    </div>
  );
}

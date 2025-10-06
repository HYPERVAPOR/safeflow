#!/usr/bin/env python
"""
MCP HTTP 代理服务器

将 MCP stdio 协议转换为 HTTP API，方便在无图形界面环境下测试
"""
import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    import uvicorn
except ImportError:
    print("❌ 错误: FastAPI 未安装")
    print("请运行: pip install fastapi uvicorn")
    sys.exit(1)

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

app = FastAPI(
    title="SafeFlow MCP HTTP Proxy",
    description="将 MCP stdio 协议转换为 HTTP API",
    version="1.0.0"
)

# 全局 MCP 进程
mcp_process = None
request_id = 0


class MCPProxy:
    """MCP 代理类，处理 stdio 通信"""
    
    def __init__(self):
        self.process = None
        self.request_id = 0
    
    async def start(self):
        """启动 MCP 服务器进程"""
        try:
            self.process = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "safeflow.mcp.server",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # 发送初始化请求
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "http-proxy", "version": "1.0.0"}
                }
            }
            
            await self.send_request(init_request)
            print("✅ MCP 服务器已启动并初始化")
            
        except Exception as e:
            print(f"❌ 启动 MCP 服务器失败: {e}")
            raise
    
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """发送请求到 MCP 服务器"""
        if not self.process:
            raise HTTPException(status_code=500, detail="MCP 服务器未启动")
        
        self.request_id += 1
        request["id"] = self.request_id
        
        try:
            # 发送请求
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json.encode())
            await self.process.stdin.drain()
            
            # 读取响应
            response_line = await self.process.stdout.readline()
            response_json = response_line.decode().strip()
            
            if response_json:
                return json.loads(response_json)
            else:
                raise HTTPException(status_code=500, detail="MCP 服务器无响应")
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"通信错误: {str(e)}")
    
    async def stop(self):
        """停止 MCP 服务器"""
        if self.process:
            self.process.terminate()
            await self.process.wait()


# 全局代理实例
mcp_proxy = MCPProxy()


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化 MCP 代理"""
    await mcp_proxy.start()


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理 MCP 代理"""
    await mcp_proxy.stop()


@app.get("/")
async def root():
    """根路径，返回 API 信息"""
    return {
        "name": "SafeFlow MCP HTTP Proxy",
        "version": "1.0.0",
        "description": "将 MCP stdio 协议转换为 HTTP API",
        "endpoints": {
            "GET /": "API 信息",
            "GET /tools": "列出所有工具",
            "GET /resources": "列出所有资源",
            "POST /tools/{tool_name}": "调用工具",
            "GET /resources/{resource_uri}": "读取资源",
            "POST /scan/semgrep": "执行 Semgrep 扫描",
            "POST /scan/syft": "执行 Syft 扫描",
            "POST /scan/all": "执行全工具扫描"
        }
    }


@app.get("/tools")
async def list_tools():
    """列出所有可用工具"""
    request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {}
    }
    
    response = await mcp_proxy.send_request(request)
    return response.get("result", {})


@app.get("/resources")
async def list_resources():
    """列出所有可用资源"""
    request = {
        "jsonrpc": "2.0",
        "method": "resources/list",
        "params": {}
    }
    
    response = await mcp_proxy.send_request(request)
    return response.get("result", {})


@app.post("/tools/{tool_name}")
async def call_tool(tool_name: str, arguments: Dict[str, Any] = None):
    """调用指定工具"""
    if arguments is None:
        arguments = {}
    
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    response = await mcp_proxy.send_request(request)
    return response.get("result", {})


@app.get("/resources/{resource_uri:path}")
async def read_resource(resource_uri: str):
    """读取指定资源"""
    request = {
        "jsonrpc": "2.0",
        "method": "resources/read",
        "params": {
            "uri": resource_uri
        }
    }
    
    response = await mcp_proxy.send_request(request)
    return response.get("result", {})


@app.post("/scan/semgrep")
async def scan_semgrep(target_path: str, rules: str = "auto"):
    """执行 Semgrep 扫描"""
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "scan_with_semgrep",
            "arguments": {
                "target_path": target_path,
                "rules": rules
            }
        }
    }
    
    response = await mcp_proxy.send_request(request)
    result = response.get("result", {})
    
    # 解析 JSON 字符串结果
    if result.get("content"):
        content = result["content"][0].get("text", "")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"raw_response": content}
    
    return result


@app.post("/scan/syft")
async def scan_syft(target_path: str):
    """执行 Syft 扫描"""
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "scan_with_syft",
            "arguments": {
                "target_path": target_path
            }
        }
    }
    
    response = await mcp_proxy.send_request(request)
    result = response.get("result", {})
    
    # 解析 JSON 字符串结果
    if result.get("content"):
        content = result["content"][0].get("text", "")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"raw_response": content}
    
    return result


@app.post("/scan/all")
async def scan_all(target_path: str):
    """执行全工具扫描"""
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "scan_with_all_tools",
            "arguments": {
                "target_path": target_path
            }
        }
    }
    
    response = await mcp_proxy.send_request(request)
    result = response.get("result", {})
    
    # 解析 JSON 字符串结果
    if result.get("content"):
        content = result["content"][0].get("text", "")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"raw_response": content}
    
    return result


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mcp_server": "running" if mcp_proxy.process else "stopped"
    }


def main():
    """主函数"""
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║           SafeFlow MCP HTTP 代理服务器                    ║")
    print("║           将 MCP stdio 协议转换为 HTTP API                ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print("")
    print("🚀 启动 HTTP 代理服务器...")
    print("   URL: http://localhost:8000")
    print("   API 文档: http://localhost:8000/docs")
    print("")
    print("💡 使用示例:")
    print("   curl http://localhost:8000/tools")
    print("   curl -X POST http://localhost:8000/scan/semgrep -H 'Content-Type: application/json' -d '{\"target_path\": \"./safeflow\"}'")
    print("")
    print("按 Ctrl+C 停止服务器")
    print("")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()

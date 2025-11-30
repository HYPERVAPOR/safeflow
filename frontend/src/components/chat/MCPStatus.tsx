'use client';

import { useState, useEffect } from 'react';
import { MCPService, mockMCPServices } from '@/lib/ai';
import { CheckCircle, XCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function MCPStatus() {
  const [services, setServices] = useState<MCPService[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchMCPServices = async () => {
    setIsLoading(true);
    try {
      // In a real implementation, this would call your backend API
      // const response = await fetch('/api/mcp/services');
      // const data = await response.json();

      // For now, use mock data
      await new Promise(resolve => setTimeout(resolve, 1000));
      setServices(mockMCPServices);
    } catch (error) {
      console.error('Failed to fetch MCP services:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMCPServices();
    const interval = fetchMCPServices;
    const id = setInterval(interval, 30000); // Refresh every 30 seconds
    return () => clearInterval(id);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'inactive':
        return <XCircle className="w-4 h-4 text-gray-400" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-green-500 bg-green-50 border-green-200';
      case 'inactive':
        return 'text-gray-500 bg-gray-50 border-gray-200';
      case 'error':
        return 'text-red-500 bg-red-50 border-red-200';
      default:
        return 'text-gray-500 bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-safeflow-text-primary">
          MCP 服务状态
        </h3>
        <button
          onClick={fetchMCPServices}
          disabled={isLoading}
          className="p-1 rounded hover:bg-safeflow-bg-tertiary transition-colors"
        >
          <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
        </button>
      </div>

      <div className="space-y-2">
        {services.map((service) => (
          <div
            key={service.name}
            className="bg-safeflow-bg-card border border-safeflow-border rounded-lg p-3"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                {getStatusIcon(service.status)}
                <span className="text-sm font-medium text-safeflow-text-primary">
                  {service.name}
                </span>
              </div>
              <span className={cn(
                "text-xs px-2 py-1 rounded-full border",
                getStatusColor(service.status)
              )}>
                {service.status}
              </span>
            </div>

            <div className="space-y-1">
              <div className="text-xs text-safeflow-text-secondary">
                {service.tools.length} 个工具可用
              </div>
              <div className="flex flex-wrap gap-1">
                {service.tools.slice(0, 3).map((tool) => (
                  <span
                    key={tool.name}
                    className="text-xs bg-safeflow-bg-secondary text-safeflow-text-secondary px-2 py-1 rounded"
                  >
                    {tool.name}
                  </span>
                ))}
                {service.tools.length > 3 && (
                  <span className="text-xs text-safeflow-text-tertiary">
                    +{service.tools.length - 3} 更多
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {services.length === 0 && !isLoading && (
        <div className="text-center py-8 text-safeflow-text-secondary">
          <div className="text-sm">暂无活跃的 MCP 服务</div>
        </div>
      )}
    </div>
  );
}
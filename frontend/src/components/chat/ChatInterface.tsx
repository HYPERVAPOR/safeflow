'use client';

import { Bot, User, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';
import { mcpClient } from '@/lib/mcp-client';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'tool_call' | 'tool_result';
  content: string;
  toolInfo?: {
    toolName: string;
    status: 'pending' | 'running' | 'success' | 'error';
    input?: Record<string, any>;
    output?: string;
    error?: string;
    executionTime?: number;
  };
}

export default function ChatInterface() {
  const [isMCPEnabled, setIsMCPEnabled] = useState(true);
  const [mcpStatus, setMcpStatus] = useState<string>('检测中...');
  const [responseTime, setResponseTime] = useState<number | null>(null);
  const [isRefreshingStatus, setIsRefreshingStatus] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [showWelcome, setShowWelcome] = useState(true);
  const [welcomeText, setWelcomeText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自定义拖拽调整高度的状态
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [startY, setStartY] = useState(0);
  const [startHeight, setStartHeight] = useState(100);

  // 拖拽处理函数
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setStartY(e.clientY);
    setStartHeight(textareaRef.current?.clientHeight || 100);
    e.preventDefault();
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging || !textareaRef.current) return;

      const deltaY = startY - e.clientY;
      const newHeight = Math.min(240, Math.max(100, startHeight + deltaY));
      textareaRef.current.style.height = `${newHeight}px`;
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, startY, startHeight]);

  // 欢迎语列表
  const welcomeMessages = [
    "💭 准备好开始智能对话了吗？",
    "🚀 让我们一起探索技术的边界",
    "🎯 需要什么技术支持和帮助？",
    "🔍 有什么想要深入了解的？",
    "🛠️ 准备好开始工作了吗？",
    "💡 让我为您提供专业建议",
    "✨ 今天有什么学习计划吗？",
    "⚡ 需要解决什么技术难题？"
  ];

  // 检测 MCP 服务状态
  const checkMCPStatus = async () => {
    try {
      setIsRefreshingStatus(true);
      const startTime = Date.now();
      const status = await mcpClient.getStatus();
      const timeTaken = Date.now() - startTime;
      setResponseTime(timeTaken);
      const isRunning = status.initialized === true && status.available_tools_count > 0;
      setIsMCPEnabled(isRunning);
      setMcpStatus(isRunning ? 'MCP 服务正常' : 'MCP 服务离线');
    } catch (error) {
      console.error('Failed to check MCP status:', error);
      setIsMCPEnabled(false);
      setMcpStatus('MCP 连接失败');
      setResponseTime(null);
    } finally {
      setIsRefreshingStatus(false);
    }
  };

  // 初始化时检测 MCP 状态和选择欢迎语
  useEffect(() => {
    const randomIndex = Math.floor(Math.random() * welcomeMessages.length);
    setWelcomeText(welcomeMessages[randomIndex]);

    // 检测 MCP 状态
    checkMCPStatus();

    // 定期检测 MCP 状态（每30秒）
    const interval = setInterval(checkMCPStatus, 30000);

    return () => clearInterval(interval);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleFormSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      // 隐藏欢迎语
      if (showWelcome) {
        setShowWelcome(false);
      }

      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content: input.trim()
      };

      setMessages(prev => [...prev, userMessage]);
      setInput('');
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            messages: [...messages, userMessage].map(({ id, ...msg }) => msg)
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to send message');
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('No response stream');
        }

        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: ''
        };

        setMessages(prev => [...prev, assistantMessage]);

        const decoder = new TextDecoder();
        let accumulatedContent = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          accumulatedContent += chunk;
          setMessages(prev =>
            prev.map(msg =>
              msg.id === assistantMessage.id
                ? { ...msg, content: accumulatedContent }
                : msg
            )
          );
        }
      } catch (err) {
        // 创建友好的错误响应消息
        const errorMessage: Message = {
          id: (Date.now() + 2).toString(),
          role: 'assistant',
          content: `## 连接出现问题

很抱歉，我在与 AI 服务通信时遇到了问题。

### 可能的解决方案：
- 检查 DeepSeek API Key 是否有效
- 确认网络连接正常
- 验证 API 服务是否可用

**错误详情：** ${err instanceof Error ? err.message : '未知错误'}

请检查配置后重试，或者联系管理员获取帮助。`
        };

        setMessages(prev => [...prev, errorMessage]);
        console.error('Chat API Error:', err);
      } finally {
        setIsLoading(false);
        setTimeout(scrollToBottom, 100);
      }
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    // 自动调整高度
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      const newHeight = Math.min(240, Math.max(100, scrollHeight));
      textareaRef.current.style.height = `${newHeight}px`;
    }
  };

  const statusMeta = {
    label: mcpStatus,
    tone: isMCPEnabled ? 'success' : 'error',
    icon: isMCPEnabled ? 'StatusSuccessIcon' : 'StatusErrorIcon'
  };

  return (
    <div className="h-screen w-screen bg-dev-bg-primary text-dev-text-primary overflow-hidden flex flex-col font-sans">
      {/* Professional Header */}
      <header className="flex-shrink-0 border-b border-dev-border-subtle bg-dev-bg-overlay/95 backdrop-blur-sm">
        <div className="flex items-center justify-between px-8 py-4">
          <div className="flex items-center space-x-4">
            <div className="p-3 rounded-xl bg-dev-tertiary/50 border border-dev-border-accent">
              <Bot className="w-6 h-6 text-dev-text-muted" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.4em] text-dev-text-muted font-semibold">AI Assistant</p>
              <h1 className="text-2xl font-semibold text-gradient">SafeFlow</h1>
            </div>
          </div>

          {/* Status & Navigation */}
          <div className="flex items-center space-x-4">
            {/* MCP 服务按钮 */}
            <a
              href="/mcp"
              className="btn btn-ghost flex items-center space-x-2"
            >
              <span>MCP 服务</span>
            </a>

            {/* 状态指示器 */}
            <div className="flex items-center space-x-2 rounded-full border border-dev-border-accent bg-dev-tertiary/50 px-4 py-2">
              <span
                className={`w-2.5 h-2.5 rounded-full breathing-dot ${
                  isMCPEnabled ? 'bg-green-500' : 'bg-red-500'
                }`}
              />
              <span className="text-sm text-dev-text-primary font-medium">
                {statusMeta.label}
              </span>
            </div>

            <button onClick={checkMCPStatus} disabled={isRefreshingStatus} className="btn btn-secondary">
              {isRefreshingStatus ? (
                <div className="w-4 h-4 border-2 border-dev-bg-primary border-t-dev-accent rounded-full animate-spin" />
              ) : (
                <RefreshCw size={16} />
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Professional Chat Area */}
      <div className="flex-1 overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto relative">
          {/* Welcome Message - Professional Full Screen */}
          {showWelcome && messages.length === 0 && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center max-w-2xl mx-auto px-8 welcome-fade-in">
                <div className="mb-8">
                  <div className="w-24 h-24 mx-auto mb-6 p-6 rounded-full bg-dev-tertiary/30 border border-dev-border-secondary flex items-center justify-center">
                    <Bot className="w-12 h-12 text-dev-text-muted" />
                  </div>
                  <h2 className="text-3xl font-semibold mb-4 text-gradient">欢迎使用 SafeFlow</h2>
                  <p className="text-lg text-dev-text-muted leading-relaxed">
                    {welcomeText}
                  </p>
                </div>

                </div>
            </div>
          )}

          {/* Chat Messages Container */}
          <div className="max-w-5xl mx-auto px-6 py-8">
            {/* Chat Messages */}
            <div className="space-y-8">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={cn(
                    "flex items-start space-x-4 welcome-fade-in",
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  )}
                >
                  {message.role === 'assistant' && (
                    <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-dev-tertiary/50 border border-dev-border-accent flex items-center justify-center">
                      <Bot className="w-6 h-6 text-dev-text-muted" />
                    </div>
                  )}

                  <div className={cn(
                    "max-w-4xl",
                    message.role === 'user' ? 'max-w-3xl' : 'max-w-4xl'
                  )}>
                    <div className={cn(
                      "rounded-2xl transition-all duration-200 border shadow-glow-accent",
                      message.role === 'user'
                        ? "bg-dev-tertiary border-dev-border-secondary"
                        : "glass-panel"
                    )}>
                      <div className="px-6 py-4">
                        <div className={cn(
                          "text-sm leading-relaxed prose prose-invert max-w-none",
                          message.role === 'user'
                            ? "prose-headings:text-dev-text-primary prose-p:text-dev-text-primary prose-strong:text-dev-text-primary prose-code:text-dev-accent"
                            : "prose-headings:text-dev-text-primary prose-p:text-dev-text-primary prose-strong:text-dev-text-primary prose-code:text-dev-accent"
                        )}>
                          {message.role === 'user' ? (
                            <div className="whitespace-pre-wrap">{message.content}</div>
                          ) : (
                            <ReactMarkdown
                              remarkPlugins={[remarkGfm]}
                              rehypePlugins={[rehypeHighlight]}
                              components={{
                                // 自定义代码块样式
                                code({ node, className, children, ...props }: any) {
                                  const inline = (props as any).inline;
                                  const match = /language-(\w+)/.exec(className || '');
                                  return !inline && match ? (
                                    <pre className={cn(
                                      "bg-dev-tertiary border border-dev-border-secondary rounded-lg p-4 overflow-x-auto",
                                      "scrollbar-custom text-sm"
                                    )}>
                                      <code className={className} {...props}>
                                        {children}
                                      </code>
                                    </pre>
                                  ) : (
                                    <code className={cn(
                                      "bg-dev-tertiary border border-dev-border-accent px-2 py-1 rounded text-sm font-mono",
                                      "text-dev-accent"
                                    )} {...props}>
                                      {children}
                                    </code>
                                  );
                                },
                                // 自定义表格样式
                                table({ children }) {
                                  return (
                                    <div className="overflow-x-auto scrollbar-custom">
                                      <table className="min-w-full border-collapse border border-dev-border-secondary rounded-lg overflow-hidden">
                                        {children}
                                      </table>
                                    </div>
                                  );
                                },
                                th({ children }) {
                                  return (
                                    <th className="border border-dev-border-secondary bg-dev-tertiary px-4 py-3 text-left font-semibold text-dev-text-primary">
                                      {children}
                                    </th>
                                  );
                                },
                                td({ children }) {
                                  return (
                                    <td className="border border-dev-border-secondary bg-dev-hover/30 px-4 py-3 text-dev-text-primary">
                                      {children}
                                    </td>
                                  );
                                },
                                // 自定义列表样式
                                ul({ children }) {
                                  return (
                                    <ul className="list-disc list-inside space-y-2 text-dev-text-primary">
                                      {children}
                                    </ul>
                                  );
                                },
                                ol({ children }) {
                                  return (
                                    <ol className="list-decimal list-inside space-y-2 text-dev-text-primary">
                                      {children}
                                    </ol>
                                  );
                                },
                                // 自定义标题样式
                                h1({ children }) {
                                  return (
                                    <h1 className="text-xl font-bold text-dev-accent mb-4 mt-6">
                                      {children}
                                    </h1>
                                  );
                                },
                                h2({ children }) {
                                  return (
                                    <h2 className="text-lg font-semibold text-dev-accent mb-3 mt-5">
                                      {children}
                                    </h2>
                                  );
                                },
                                h3({ children }) {
                                  return (
                                    <h3 className="text-base font-semibold text-dev-accent mb-2 mt-4">
                                      {children}
                                    </h3>
                                  );
                                },
                                // 自定义引用样式
                                blockquote({ children }) {
                                  return (
                                    <blockquote className="border-l-4 border-dev-accent pl-4 italic text-dev-text-muted bg-dev-hover/20 rounded-r-lg py-3">
                                      {children}
                                    </blockquote>
                                  );
                                },
                                // 自定义链接样式
                                a({ href, children }) {
                                  return (
                                    <a
                                      href={href}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-dev-accent hover:text-dev-accent-hover underline transition-colors"
                                    >
                                      {children}
                                    </a>
                                  );
                                },
                              }}
                            >
                              {message.content}
                            </ReactMarkdown>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  {message.role === 'user' && (
                    <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-dev-accent-subtle border border-dev-accent/30 flex items-center justify-center">
                      <User className="w-6 h-6 text-dev-accent" />
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Tool Call Status Messages */}
            {messages
              .filter(msg => msg.role === 'tool_call' || msg.role === 'tool_result')
              .map((message) => (
                <div key={message.id} className="max-w-5xl mx-auto px-6 py-4">
                  <div className="glass-panel p-6">
                    {/* Tool Call Header */}
                    <div className="flex items-center space-x-3 mb-4">
                      <div className={`w-3 h-3 rounded-full ${
                        message.toolInfo?.status === 'pending' ? 'bg-yellow-500' :
                        message.toolInfo?.status === 'running' ? 'bg-blue-500 animate-pulse' :
                        message.toolInfo?.status === 'success' ? 'bg-green-500' :
                        'bg-red-500'
                      }`} />
                      <span className="text-sm font-medium text-dev-text-primary">
                        {message.role === 'tool_call' ? '正在调用工具' : '工具执行结果'}
                      </span>
                      {message.toolInfo && (
                        <span className="text-xs text-dev-text-muted bg-dev-tertiary px-2 py-1 rounded border border-dev-border-accent font-mono">
                          {message.toolInfo.toolName}
                        </span>
                      )}
                    </div>

                    {/* Tool Input */}
                    {message.toolInfo?.input && (
                      <div className="mb-4">
                        <div className="text-xs text-dev-text-muted mb-2 font-semibold uppercase tracking-wider">🔧 输入参数</div>
                        <div className="bg-dev-tertiary rounded-lg border border-dev-border-secondary p-4">
                          <pre className="text-xs font-mono text-dev-text-primary whitespace-pre-wrap">
                            {JSON.stringify(message.toolInfo.input, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}

                    {/* Tool Output */}
                    {message.toolInfo?.output && (
                      <div className="mb-4">
                        <div className="text-xs text-dev-text-muted mb-2 font-semibold uppercase tracking-wider">📤 执行输出</div>
                        <div className="bg-dev-tertiary rounded-lg border border-dev-border-secondary p-4 max-h-60 overflow-y-auto scrollbar-custom">
                          <pre className="text-xs font-mono text-dev-success whitespace-pre-wrap">
                            {message.toolInfo.output}
                          </pre>
                        </div>
                      </div>
                    )}

                    {/* Tool Error */}
                    {message.toolInfo?.error && (
                      <div className="mb-4">
                        <div className="text-xs text-dev-text-muted mb-2 font-semibold uppercase tracking-wider">❌ 错误信息</div>
                        <div className="bg-dev-error-subtle border border-dev-error/30 rounded-lg p-4">
                          <pre className="text-xs font-mono text-dev-error whitespace-pre-wrap">
                            {message.toolInfo.error}
                          </pre>
                        </div>
                      </div>
                    )}

                    {/* Execution Time */}
                    {message.toolInfo?.executionTime && (
                      <div className="flex items-center space-x-2 text-xs text-dev-text-muted">
                        <span>⏱️ 执行时间</span>
                        <span className="bg-dev-tertiary px-2 py-1 rounded border border-dev-border-accent font-mono">
                          {(message.toolInfo.executionTime / 1000).toFixed(2)}s
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}

            {/* Error State */}
            {error && (
              <div className="max-w-5xl mx-auto px-6 py-8">
                <div className="glass-panel border border-dev-error/30 bg-dev-error-subtle rounded-2xl p-6 welcome-fade-in">
                  <div className="text-dev-error flex items-center space-x-3">
                    <span className="text-xl">⚠️</span>
                    <span className="font-medium">出错了：{error}</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Professional Input Area */}
        <div className="border-t border-dev-border-subtle bg-dev-bg-secondary/95 backdrop-blur-sm px-8 py-6">
          <div className="max-w-5xl mx-auto">
            <form onSubmit={handleFormSubmit} className="relative">
              {/* Professional Drag Handle */}
              <div
                className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-10"
                onMouseDown={handleMouseDown}
                style={{ touchAction: 'none' }}
              >
                <div className="w-12 h-1 bg-dev-border rounded-full hover:bg-dev-accent transition-colors cursor-ns-resize" />
              </div>

              <div className="relative">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={handleInputChange}
                  placeholder="询问任何问题..."
                  className="w-full px-6 py-4 bg-dev-tertiary/50 border border-dev-border-secondary focus:border-dev-accent focus:shadow-glow-accent resize-none rounded-2xl text-dev-text-primary placeholder-dev-text-muted transition-all duration-200 scrollbar-custom pr-14"
                  style={{ height: '100px' }}
                  rows={1}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleFormSubmit(e as any);
                    }
                  }}
                />

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={!input.trim() || isLoading}
                  className="absolute right-2 bottom-2 w-8 h-8 rounded-lg bg-dev-accent hover:bg-dev-accent-hover disabled:bg-dev-border disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
                >
                  {isLoading ? (
                    <div className="w-4 h-4 border-2 border-dev-bg-primary border-t-dev-accent rounded-full animate-spin" />
                  ) : (
                    <svg
                      className="w-4 h-4 text-dev-bg-primary"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                      />
                    </svg>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
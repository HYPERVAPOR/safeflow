'use client';

import { Bot, User } from 'lucide-react';
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
  const [startHeight, setStartHeight] = useState(80);

  // 拖拽处理函数
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setStartY(e.clientY);
    setStartHeight(textareaRef.current?.clientHeight || 80);
    e.preventDefault();
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging || !textareaRef.current) return;

      const deltaY = startY - e.clientY;
      const newHeight = Math.min(200, Math.max(80, startHeight + deltaY));
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
    "👋 今天想聊点什么？",
    "💭 有什么可以帮助您的吗？",
    "🚀 准备好开始探索了吗？",
    "🎯 让我们一起解决问题吧！",
    "⚡ 需要什么技术支持？",
    "🔍 有什么想要了解的？",
    "🛠️ 准备好开始工作了吗？",
    "💡 让我为您提供帮助",
    "🎊 欢迎回来！有什么新计划吗？",
    "✨ 今天有什么想学习的吗？"
  ];

  // 检测 MCP 服务状态
  const checkMCPStatus = async () => {
    try {
      const status = await mcpClient.getStatus();
      const isRunning = status.initialized === true && status.available_tools_count > 0;
      setIsMCPEnabled(isRunning);
      setMcpStatus(isRunning ? 'MCP 已连接' : 'MCP 未连接');
    } catch (error) {
      console.error('Failed to check MCP status:', error);
      setIsMCPEnabled(false);
      setMcpStatus('MCP 连接失败');
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
          content: `🚫 **连接出现问题**

很抱歉，我在与 AI 服务通信时遇到了问题。这可能是由于以下原因：

🔧 **可能的解决方案：**
1. 检查 DeepSeek API Key 是否有效
2. 确认网络连接正常
3. 验证 API 服务是否可用

📝 **错误详情：** ${err instanceof Error ? err.message : '未知错误'}

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
  };

  return (
    <div className="h-screen w-screen bg-gray-950 text-gray-200 overflow-hidden flex flex-col">
      {/* Header */}
      <header className="flex-shrink-0 border-b border-gray-700 bg-gray-900/95 backdrop-blur-sm">
        <div className="flex items-center justify-between px-8 py-4">
          <div className="flex items-center space-x-4">
            <div className="p-3 rounded-xl bg-safeflow-accent/5 border border-gray-700/30">
              <Bot className="w-6 h-6 text-gray-400" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.4em] text-gray-500">AI Assistant</p>
              <h1 className="text-2xl font-semibold text-gradient">SafeFlow</h1>
            </div>
          </div>

          {/* MCP Status & Navigation */}
          <div className="flex items-center space-x-3">
            {/* MCP 服务按钮 */}
            <a
              href="/mcp"
              className="inline-flex items-center px-4 py-2 text-sm font-medium rounded-lg border border-blue-500/30 text-blue-400 bg-blue-500/5 hover:bg-blue-500/10 hover:border-blue-500/50 hover:shadow-glow-blue transition-all duration-200"
            >
              <span>MCP 服务</span>
            </a>

            <div className="flex items-center space-x-2 rounded-full border border-gray-700 px-4 py-2">
              <span
                className={`w-2.5 h-2.5 rounded-full breathing-dot ${
                  isMCPEnabled ? 'bg-green-500' : 'bg-red-500'
                }`}
              />
              <span className="text-sm text-gray-300">
                {mcpStatus}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto relative">
        {/* Welcome Message - Full screen overlay when no messages */}
        {showWelcome && messages.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center welcome-fade-in">
              <p className="text-4xl font-medium text-gray-400">
                {welcomeText}
              </p>
            </div>
          </div>
        )}

        <div className="max-w-4xl mx-auto px-6 py-8">

          {/* Chat Messages */}
          <div className="space-y-6">
            {messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  "flex items-start space-x-4 animate-fade-in",
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                {message.role === 'assistant' && (
                  <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-safeflow-accent/5 border border-gray-700/30 flex items-center justify-center">
                    <Bot className="w-5 h-5 text-gray-400" />
                  </div>
                )}

                <div className={cn(
                  "max-w-3xl px-5 py-4 rounded-2xl transition-all duration-200",
                  "bg-gray-800/50 border border-gray-700/50"
                )}>
                  <div className={cn(
                    "text-sm leading-relaxed prose prose-invert max-w-none",
                    message.role === 'user'
                      ? "prose-headings:text-white prose-p:text-white prose-strong:text-white prose-code:text-white"
                      : "prose-headings:text-safeflow-text-primary prose-p:text-safeflow-text-primary prose-strong:text-safeflow-text-primary prose-code:text-safeflow-accent"
                  )}>
                    {message.role === 'user' ? (
                      // 用户消息保持纯文本，支持换行
                      <div className="whitespace-pre-wrap">{message.content}</div>
                    ) : (
                      // AI 助手消息支持 Markdown 渲染
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
                                "bg-gray-800/80 border border-gray-700 rounded-lg p-4 overflow-x-auto",
                                "scrollbar-custom text-sm"
                              )}>
                                <code className={className} {...props}>
                                  {children}
                                </code>
                              </pre>
                            ) : (
                              <code className={cn(
                                "bg-safeflow-bg-card border border-safeflow-border px-2 py-1 rounded text-sm font-mono",
                                "text-safeflow-accent"
                              )} {...props}>
                                {children}
                              </code>
                            );
                          },
                          // 自定义表格样式
                          table({ children }) {
                            return (
                              <div className="overflow-x-auto scrollbar-custom">
                                <table className="min-w-full border-collapse border border-gray-700 rounded-lg overflow-hidden">
                                  {children}
                                </table>
                              </div>
                            );
                          },
                          th({ children }) {
                            return (
                              <th className="border border-gray-700 bg-safeflow-bg-card px-4 py-2 text-left font-semibold text-safeflow-text-primary">
                                {children}
                              </th>
                            );
                          },
                          td({ children }) {
                            return (
                              <td className="border border-gray-700 bg-safeflow-bg-primary/50 px-4 py-2 text-safeflow-text-primary">
                                {children}
                              </td>
                            );
                          },
                          // 自定义列表样式
                          ul({ children }) {
                            return (
                              <ul className="list-disc list-inside space-y-1 text-safeflow-text-primary">
                                {children}
                              </ul>
                            );
                          },
                          ol({ children }) {
                            return (
                              <ol className="list-decimal list-inside space-y-1 text-safeflow-text-primary">
                                {children}
                              </ol>
                            );
                          },
                          // 自定义标题样式
                          h1({ children }) {
                            return (
                              <h1 className="text-xl font-bold text-safeflow-accent mb-3 mt-4">
                                {children}
                              </h1>
                            );
                          },
                          h2({ children }) {
                            return (
                              <h2 className="text-lg font-semibold text-safeflow-accent mb-2 mt-3">
                                {children}
                              </h2>
                            );
                          },
                          h3({ children }) {
                            return (
                              <h3 className="text-base font-semibold text-safeflow-accent mb-2 mt-2">
                                {children}
                              </h3>
                            );
                          },
                          // 自定义引用样式
                          blockquote({ children }) {
                            return (
                              <blockquote className="border-l-4 border-safeflow-accent pl-4 italic text-safeflow-text-secondary bg-safeflow-bg-card/30 rounded-r-lg py-2">
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
                                className="text-safeflow-accent hover:text-safeflow-accent-hover underline transition-colors"
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

                {message.role === 'user' && (
                  <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-safeflow-accent/10 border border-gray-700/50 flex items-center justify-center">
                    <User className="w-5 h-5 text-safeflow-accent" />
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Tool Call Status Messages */}
          {messages
            .filter(msg => msg.role === 'tool_call' || msg.role === 'tool_result')
            .map((message) => (
              <div key={message.id} className="max-w-4xl mx-auto px-6 py-4">
                <div className="border border-gray-700/50 bg-gray-900/30 rounded-2xl p-4">
                  {/* Tool Call Header */}
                  <div className="flex items-center space-x-3 mb-3">
                    <div className={`w-3 h-3 rounded-full ${
                      message.toolInfo?.status === 'pending' ? 'bg-yellow-500' :
                      message.toolInfo?.status === 'running' ? 'bg-blue-500 animate-pulse' :
                      message.toolInfo?.status === 'success' ? 'bg-green-500' :
                      'bg-red-500'
                    }`} />
                    <span className="text-sm font-medium text-gray-300">
                      {message.role === 'tool_call' ? '正在调用工具' : '工具执行结果'}
                    </span>
                    {message.toolInfo && (
                      <span className="text-xs text-gray-500">
                        {message.toolInfo.toolName}
                      </span>
                    )}
                  </div>

                  {/* Tool Input */}
                  {message.toolInfo?.input && (
                    <div className="mb-3">
                      <div className="text-xs text-gray-400 mb-1">🔧 输入参数：</div>
                      <div className="bg-gray-800/50 rounded-lg p-3 text-xs font-mono text-gray-300">
                        {JSON.stringify(message.toolInfo.input, null, 2)}
                      </div>
                    </div>
                  )}

                  {/* Tool Output or Error */}
                  {message.toolInfo?.output && (
                    <div className="mb-3">
                      <div className="text-xs text-gray-400 mb-1">📤 执行输出：</div>
                      <div className="bg-gray-800/50 rounded-lg p-3 text-xs font-mono text-green-400 max-h-60 overflow-y-auto">
                        {message.toolInfo.output}
                      </div>
                    </div>
                  )}

                  {message.toolInfo?.error && (
                    <div className="mb-3">
                      <div className="text-xs text-gray-400 mb-1">❌ 错误信息：</div>
                      <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-3 text-xs font-mono text-red-400">
                        {message.toolInfo.error}
                      </div>
                    </div>
                  )}

                  {/* Execution Time */}
                  {message.toolInfo?.executionTime && (
                    <div className="text-xs text-gray-500">
                      ⏱️ 执行时间：{(message.toolInfo.executionTime / 1000).toFixed(2)}秒
                    </div>
                  )}
                </div>
              </div>
            ))}

        {/* Error State */}
        {error && (
          <div className="max-w-4xl mx-auto px-6 py-8">
            <div className="glass-panel border border-red-500/30 bg-red-500/10 rounded-2xl p-4 animate-fade-in">
              <div className="text-sm text-red-400 flex items-center">
                <span className="mr-2">⚠️</span>
                <span>出错了：{error}</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Form */}
      <div className="px-8 py-6">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleFormSubmit} className="relative">
            {/* 拖拽区域 - 在输入框上方 */}
            <div
              className="absolute top-0 left-0 right-0 h-2 flex items-center justify-center cursor-ns-resize z-10"
              onMouseDown={handleMouseDown}
              style={{ touchAction: 'none' }}
            >
              <div className="w-16 h-1 bg-gray-600 rounded-full hover:bg-gray-400 transition-colors" />
            </div>

            <textarea
              ref={textareaRef}
              value={input}
              onChange={handleInputChange}
              placeholder="询问任何事... "
              className="w-full px-5 pt-8 pb-4 bg-gray-950 resize-none border border-gray-700 focus:outline-none focus:shadow-glow-blue/30 focus:border-blue-500/50 rounded-3xl text-gray-200 placeholder-gray-500 transition-all duration-200"
              style={{ height: '80px' }}
              rows={1}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleFormSubmit(e as any);
                }
              }}
            />
          </form>

          </div>
      </div>
    </div>
  );
}
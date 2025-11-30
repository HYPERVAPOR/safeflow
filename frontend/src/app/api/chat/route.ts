import { NextRequest } from 'next/server';
import { chatWithAI } from '@/lib/ai';

// 处理工具调用相关的辅助函数
function processToolCallMessage(content: string): string {
  // 移除工具调用的原始标记，使其更友好
  return content
    .replace(/<\|tool_calls_begin\|>/g, '')
    .replace(/<\|tool_call_begin\|>/g, '')
    .replace(/<\|tool_sep\|>/g, '')
    .replace(/<\|tool_call_end\|>/g, '')
    .replace(/<\|tool_calls_end\|>/g, '');
}

export async function POST(req: NextRequest) {
  try {
    const { messages } = await req.json();

    // 检查 API Key 是否配置
    if (!process.env.DEEPSEEK_API_KEY || process.env.DEEPSEEK_API_KEY === 'your_deepseek_api_key_here') {
      throw new Error('DeepSeek API Key 未配置或无效，请检查 .env.local 文件中的 DEEPSEEK_API_KEY');
    }

    const response = await chatWithAI(messages);
    return response;
  } catch (error) {
    console.error('Chat API Error:', error);

    // 返回更详细的错误信息用于调试
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';

    return new Response(
      JSON.stringify({
        error: 'Failed to process chat request',
        details: errorMessage,
        suggestion: '请检查 DeepSeek API Key 配置和网络连接'
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}
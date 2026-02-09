import client from './client';
import type { ChatRequest, ChatResponse } from '../types';

export async function sendChatQuery(request: ChatRequest): Promise<ChatResponse> {
  const response = await client.post<ChatResponse>('/chat/query', request);
  return response.data;
}

export async function getChatHistory(limit: number = 10): Promise<{ message: string; limit: number }> {
  const response = await client.get('/chat/history', {
    params: { limit },
  });
  return response.data;
}

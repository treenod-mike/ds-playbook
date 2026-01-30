/**
 * Message Entity - API Layer
 *
 * 채팅 API 호출
 */
import axios from 'axios'
import type { ChatRequest, ChatResponse } from '../model/types'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export const messageApi = {
  /**
   * 채팅 메시지 전송
   */
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await axios.post<ChatResponse>(
      `${BACKEND_URL}/api/chat`,
      request
    )
    return response.data
  },
}

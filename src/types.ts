export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  response: string;
  sql?: string;
  row_count?: number;
  data?: any[];
  suggestions?: string[];
  error?: string;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  context?: Record<string, any>;
  suggestions?: string[];
}
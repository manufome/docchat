/** DocChat TypeScript type definitions. */

export interface User {
  id: string;
  email: string;
  created_at: string;
  llm_provider?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
}

export interface ApiKeyData {
  api_key: string;
  provider: "openai" | "gemini" | "groq";
}

export interface ApiKeyResponse {
  message: string;
}

export interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: string;
  chunk_count: number | null;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  index: number;
  document_name: string;
  page: string | number;
  text_preview: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[] | null;
  created_at: string;
}

export interface UserProviderResponse {
  provider: string;
  has_key: boolean;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

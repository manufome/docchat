/** HTTP client for DocChat API. */

import type {
  ApiKeyData,
  ApiKeyResponse,
  Document,
  LoginData,
  RegisterData,
  TokenResponse,
  User,
  UserProviderResponse,
} from "../types";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = localStorage.getItem("token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      if (body.detail) detail = body.detail;
    } catch {
      // ignore parse errors
    }
    throw new ApiError(detail, response.status);
  }

  return response.json() as Promise<T>;
}

/** Upload a file (multipart) — no Content-Type set, browser includes boundary. */
async function uploadFile(
  path: string,
  file: File,
  signal?: AbortSignal,
): Promise<Document> {
  const token = localStorage.getItem("token");
  const formData = new FormData();
  formData.append("file", file);

  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    body: formData,
    headers,
    signal,
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      if (body.detail) detail = body.detail;
    } catch {
      // ignore parse errors
    }
    throw new ApiError(detail, response.status);
  }

  return response.json() as Promise<Document>;
}

export const auth = {
  register: (data: RegisterData) =>
    request<TokenResponse>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  login: (data: LoginData) =>
    request<TokenResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  me: () => request<User>("/api/auth/me"),

  setApiKey: (data: ApiKeyData) =>
    request<ApiKeyResponse>("/api/users/me/api-key", {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  getProvider: () => request<UserProviderResponse>("/api/users/me/provider"),
};

export const documents = {
  list: () => request<Document[]>("/api/documents"),

  upload: (file: File, signal?: AbortSignal) =>
    uploadFile("/api/documents/upload", file, signal),

  remove: (id: string) =>
    request<{ detail: string }>(`/api/documents/${id}`, {
      method: "DELETE",
    }),
};

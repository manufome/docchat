/** Conversations management hook for DocChat. */

import { useCallback, useEffect, useState } from "react";
import type { Conversation } from "../types";
import { getApiBaseUrl } from "../lib/apiBase";

const API_BASE = getApiBaseUrl();

interface UseConversationsReturn {
  conversations: Conversation[];
  selectedId: string | null;
  isLoading: boolean;
  createConversation: (title?: string) => Promise<Conversation | undefined>;
  deleteConversation: (id: string) => Promise<void>;
  selectConversation: (id: string) => void;
  refreshConversations: () => Promise<void>;
}

async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      if (body.detail) detail = body.detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

export function useConversations(): UseConversationsReturn {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const refreshConversations = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await apiRequest<Conversation[]>("/api/conversations");
      setConversations(data);
      // Auto-select first conversation if none selected and list is not empty
      if (data.length > 0) {
        setSelectedId((prev) => prev ?? data[0].id);
      }
    } catch {
      // Silently fail — conversations remain empty
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Load conversations on mount
  useEffect(() => {
    refreshConversations();
  }, [refreshConversations]);

  const createConversation = useCallback(
    async (title?: string): Promise<Conversation | undefined> => {
      try {
        const conv = await apiRequest<Conversation>("/api/conversations", {
          method: "POST",
          body: JSON.stringify({ title: title ?? null }),
        });
        setConversations((prev) => [conv, ...prev]);
        setSelectedId(conv.id);
        return conv;
      } catch (err) {
        throw err;
      }
    },
    [],
  );

  const deleteConversation = useCallback(async (id: string) => {
    try {
      await apiRequest<{ detail: string }>(`/api/conversations/${id}`, {
        method: "DELETE",
      });
      setConversations((prev) => prev.filter((c) => c.id !== id));
      setSelectedId((prev) => (prev === id ? null : prev));
    } catch {
      // Silently fail
    }
  }, []);

  const selectConversation = useCallback((id: string) => {
    setSelectedId(id);
  }, []);

  return {
    conversations,
    selectedId,
    isLoading,
    createConversation,
    deleteConversation,
    selectConversation,
    refreshConversations,
  };
}

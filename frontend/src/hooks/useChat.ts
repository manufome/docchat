/** SSE streaming hook for DocChat chat completions. */

import { useCallback, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL ?? "";
const STREAM_TIMEOUT_MS = 60_000; // Abort if no event arrives within 60s

export interface ChatMessage {
  id?: string;
  role: "user" | "assistant";
  content: string;
  citations?: Array<{
    index: number;
    document_name: string;
    page: number | string;
    text_preview: string;
  }>;
}

interface UseChatReturn {
  messages: ChatMessage[];
  isStreaming: boolean;
  error: string | null;
  sendMessage: (message: string, conversationId?: string) => Promise<string | undefined>;
  clearMessages: () => void;
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  const sendMessage = useCallback(
    async (message: string, conversationId?: string): Promise<string | undefined> => {
      setError(null);

      // Add user message immediately
      const userMessage: ChatMessage = { role: "user", content: message };
      setMessages((prev) => [...prev, userMessage]);

      // Add placeholder assistant message
      const assistantMessage: ChatMessage = { role: "assistant", content: "" };
      setMessages((prev) => [...prev, assistantMessage]);
      setIsStreaming(true);

      // Abort previous request if any
      if (abortRef.current) {
        abortRef.current.abort();
      }
      const controller = new AbortController();
      abortRef.current = controller;

      // Watchdog timer — if no event arrives within STREAM_TIMEOUT_MS, abort
      const watchdogRef = { timerId: null as ReturnType<typeof setTimeout> | null };
      function resetWatchdog() {
        if (watchdogRef.timerId) clearTimeout(watchdogRef.timerId);
        watchdogRef.timerId = setTimeout(() => {
          controller.abort();
          setError("El servicio no está respondiendo. Intente de nuevo o cambie de proveedor.");
          setIsStreaming(false);
        }, STREAM_TIMEOUT_MS);
      }

      const token = localStorage.getItem("token");
      const body: Record<string, unknown> = { message };
      if (conversationId) {
        body.conversation_id = conversationId;
      }

      try {
        const response = await fetch(`${API_BASE}/api/chat/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify(body),
          signal: controller.signal,
        });

        if (!response.ok) {
          if (watchdogRef.timerId) clearTimeout(watchdogRef.timerId);
          let detail = `HTTP ${response.status}`;
          try {
            const errBody = await response.json();
            if (errBody.detail) detail = errBody.detail;
          } catch {
            // ignore
          }
          setError(detail);
          setMessages((prev) => prev.slice(0, -1)); // Remove placeholder
          setIsStreaming(false);
          return undefined;
        }

        const reader = response.body?.getReader();
        if (!reader) {
          if (watchdogRef.timerId) clearTimeout(watchdogRef.timerId);
          setError("No se pudo establecer conexión de streaming.");
          setMessages((prev) => prev.slice(0, -1));
          setIsStreaming(false);
          return undefined;
        }

        const decoder = new TextDecoder();
        let buffer = "";
        let currentCitations: ChatMessage["citations"] = [];
        let resolvedConversationId: string | undefined = conversationId;

        // Start the watchdog timer
        resetWatchdog();

        // Read the stream
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || ""; // Keep incomplete line in buffer

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const data = line.slice(6);
            let event: Record<string, unknown>;
            try {
              event = JSON.parse(data);
            } catch {
              continue;
            }

            resetWatchdog(); // Reset timer on each event

            switch (event.type) {
              case "token": {
                const content = String(event.content ?? "");
                setMessages((prev) => {
                  const updated = [...prev];
                  const last = updated[updated.length - 1];
                  if (last && last.role === "assistant") {
                    updated[updated.length - 1] = {
                      ...last,
                      content: last.content + content,
                    };
                  }
                  return updated;
                });
                break;
              }
              case "citation": {
                const citation = event.citation as NonNullable<ChatMessage["citations"]>[number];
                if (citation) {
                  currentCitations = [...currentCitations, citation];
                }
                break;
              }
              case "done": {
                // Attach citations to the assistant message
                if (currentCitations.length > 0) {
                  setMessages((prev) => {
                    const updated = [...prev];
                    const last = updated[updated.length - 1];
                    if (last && last.role === "assistant") {
                      updated[updated.length - 1] = {
                        ...last,
                        citations: currentCitations,
                      };
                    }
                    return updated;
                  });
                }
                resolvedConversationId = (event.message_id as string) || resolvedConversationId;
                break;
              }
              case "error": {
                setError(String(event.content ?? "Error desconocido."));
                setMessages((prev) => prev.slice(0, -1));
                break;
              }
            }
          }
        }

        if (watchdogRef.timerId) clearTimeout(watchdogRef.timerId);
        setIsStreaming(false);
        return resolvedConversationId;
      } catch (err: unknown) {
        if (watchdogRef.timerId) clearTimeout(watchdogRef.timerId);
        if (err instanceof DOMException && err.name === "AbortError") {
          // User aborted or watchdog timed out — ignore
          setIsStreaming(false);
          return undefined;
        }
        const msg = err instanceof Error ? err.message : "Error de conexión.";
        setError(msg);
        setMessages((prev) => prev.slice(0, -1));
        setIsStreaming(false);
        return undefined;
      }
    },
    [],
  );

  return { messages, isStreaming, error, sendMessage, clearMessages };
}

/** Chat page — split layout with conversations sidebar and chat area. */

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useChat, type ChatMessage } from "../hooks/useChat";
import { useConversations } from "../hooks/useConversations";
import { ChatWindow } from "../components/chat/ChatWindow";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

export default function ChatPage() {
  const { user, logout } = useAuth();
  const {
    messages,
    isStreaming,
    error,
    sendMessage,
    clearMessages,
  } = useChat();
  const {
    conversations,
    selectedId,
    isLoading: convsLoading,
    createConversation,
    deleteConversation,
    selectConversation,
  } = useConversations();

  const [convMessages, setConvMessages] = useState<
    Array<{ id: string; role: "user" | "assistant"; content: string; citations?: unknown[] }>
  >([]);
  const [loadingMessages, setLoadingMessages] = useState(false);

  // Load messages when a conversation is selected
  useEffect(() => {
    if (!selectedId) {
      setConvMessages([]);
      return;
    }

    const loadMessages = async () => {
      setLoadingMessages(true);
      const token = localStorage.getItem("token");
      try {
        const response = await fetch(`${API_BASE}/api/conversations/${selectedId}/messages`, {
          headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
        });
        if (response.ok) {
          const data = await response.json();
          setConvMessages(data);
        }
      } catch {
        // ignore
      } finally {
        setLoadingMessages(false);
      }
    };

    loadMessages();
  }, [selectedId]);

  // Merge useChat messages (for streaming) with conversation messages (from history)
  // When streaming, use useChat messages; otherwise use convMessages
  const displayMessages = messages.length > 0 ? messages : convMessages;

  const handleSend = useCallback(
    async (message: string) => {
      const newConvId = await sendMessage(message, selectedId ?? undefined);
      // If this is a new conversation (no selectedId), the create happens on the backend
      if (!selectedId) {
        // Refresh conversations list to pick up the new one
        // The conversation was created on the server side in the SSE handler
      }
    },
    [sendMessage, selectedId],
  );

  const handleNewChat = useCallback(async () => {
    clearMessages();
    setConvMessages([]);
    await createConversation("Nueva conversación");
  }, [clearMessages, createConversation]);

  const handleDeleteConv = useCallback(
    async (id: string) => {
      if (selectedId === id) {
        clearMessages();
        setConvMessages([]);
      }
      await deleteConversation(id);
    },
    [selectedId, clearMessages, deleteConversation],
  );

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-72 flex-shrink-0 bg-white border-r border-gray-200 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-lg font-bold text-gray-900">DocChat</h1>
            <span className="text-xs text-gray-500 truncate max-w-[120px]">
              {user?.email}
            </span>
          </div>
          <button
            onClick={handleNewChat}
            className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            + Nueva conversación
          </button>
        </div>

        {/* Conversations list */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {convsLoading && conversations.length === 0 && (
            <div className="flex justify-center py-8">
              <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            </div>
          )}

          {!convsLoading && conversations.length === 0 && (
            <p className="text-sm text-gray-400 text-center py-8">
              No hay conversaciones
            </p>
          )}

          {conversations.map((conv) => (
            <div
              key={conv.id}
              className={`group flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition-colors ${
                selectedId === conv.id
                  ? "bg-blue-50 text-blue-700"
                  : "text-gray-700 hover:bg-gray-100"
              }`}
              onClick={() => selectConversation(conv.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter") selectConversation(conv.id);
              }}
            >
              <span className="text-sm truncate flex-1">
                {conv.title || "Sin título"}
              </span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteConv(conv.id);
                }}
                className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-all"
                aria-label={`Eliminar ${conv.title || "conversación"}`}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          ))}
        </div>

        {/* Logout */}
        <div className="p-4 border-t border-gray-200">
          <button
            onClick={logout}
            className="w-full px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cerrar sesión
          </button>
        </div>
      </aside>

      {/* Main chat area */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Error banner */}
        {error && (
          <div className="px-4 py-2 bg-red-50 border-b border-red-200 text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Chat window */}
        <div className="flex-1 flex flex-col min-h-0">
          {loadingMessages ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <ChatWindow
              messages={displayMessages.map((m) => ({
                role: m.role as "user" | "assistant",
                content: m.content,
                citations: m.citations as ChatMessage["citations"],
              }))}
              isStreaming={isStreaming}
              onSend={handleSend}
            />
          )}
        </div>
      </main>
    </div>
  );
}

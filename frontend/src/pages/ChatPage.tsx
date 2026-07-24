/** Chat page — split layout with conversations sidebar and chat area. */

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useToast } from "../components/shared/Toast";
import { useChat, type ChatMessage } from "../hooks/useChat";
import { useConversations } from "../hooks/useConversations";
import { ChatWindow } from "../components/chat/ChatWindow";
import { CitationSidePanel } from "../components/chat/CitationSidePanel";
import { DeleteConfirmationDialog } from "../components/shared/DeleteConfirmationDialog";
import { getApiBaseUrl } from "../lib/apiBase";

const API_BASE = getApiBaseUrl();

export default function ChatPage() {
  const { user } = useAuth();
  const { addToast } = useToast();
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
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  // Citation side panel state
  const [citationPanel, setCitationPanel] = useState<{
    citations: Array<{ index: number; document_name: string; page: number | string; text_preview: string }>;
    activeIndex: number;
  } | null>(null);

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
        addToast("Error al cargar los mensajes de la conversación.", "error");
      } finally {
        setLoadingMessages(false);
      }
    };

    loadMessages();
  }, [selectedId, addToast]);

  // Merge useChat messages (for streaming) with conversation messages (from history)
  const displayMessages = messages.length > 0 ? messages : convMessages;

  const handleSend = useCallback(
    async (message: string) => {
      const newConvId = await sendMessage(message, selectedId ?? undefined);
      if (!selectedId && newConvId) {
        // Refresh conversations list to pick up the new one
      }
    },
    [sendMessage, selectedId],
  );

  const handleNewChat = useCallback(async () => {
    clearMessages();
    setConvMessages([]);
    try {
      await createConversation("Nueva conversación");
    } catch {
      addToast("Error al crear la conversación.", "error");
    }
  }, [clearMessages, createConversation, addToast]);

  const handleCitationClick = useCallback(
    (citation: { index: number; document_name: string; page: number | string; text_preview: string }, allCitations: typeof citation[]) => {
      setCitationPanel({ citations: allCitations, activeIndex: citation.index });
    },
    [],
  );

  const handleDeleteConv = useCallback(
    async (id: string) => {
      if (selectedId === id) {
        clearMessages();
        setConvMessages([]);
      }
      try {
        await deleteConversation(id);
        addToast("Conversación eliminada.", "info");
      } catch {
        addToast("Error al eliminar la conversación.", "error");
      }
      setDeleteTarget(null);
    },
    [selectedId, clearMessages, deleteConversation, addToast],
  );

  const hasNoConversation = !selectedId && displayMessages.length === 0 && !isStreaming;

  return (
    <div className="flex h-[calc(100vh-3.5rem)] bg-gray-50">
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
            <div className="flex flex-col items-center justify-center py-8 px-4 text-center">
              <svg className="w-8 h-8 text-gray-300 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <p className="text-sm text-gray-400">
                Selecciona una conversación o crea una nueva
              </p>
            </div>
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
                  setDeleteTarget(conv.id);
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
      </aside>

      {/* Main chat area */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Error banner for streaming errors */}
        {error && (
          <div className="px-4 py-2 bg-red-50 border-b border-red-200 text-red-700 text-sm flex items-center gap-2">
            <span>✕</span>
            <span className="flex-1">{error}</span>
            <button
              onClick={() => {/* error is cleared by useChat on next send */}}
              className="text-red-500 hover:text-red-700 text-xs font-medium"
            >
              Cerrar
            </button>
          </div>
        )}

        {/* Chat window or empty state */}
        <div className="flex-1 flex flex-col min-h-0">
          {loadingMessages ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : hasNoConversation ? (
            /* Empty state — no conversation selected and no messages */
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
              <div className="w-16 h-16 mb-4 rounded-full bg-blue-100 flex items-center justify-center">
                <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Selecciona una conversación o crea una nueva
              </h3>
              <p className="text-sm text-gray-500 max-w-sm mb-4">
                Tus documentos están listos. Hacé una pregunta sobre su contenido.
              </p>
              <button
                onClick={handleNewChat}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
              >
                + Nueva conversación
              </button>
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
              onCitationClick={handleCitationClick}
            />
          )}
        </div>
      </main>

      {/* Delete confirmation dialog */}
      {/* Citation side panel */}
      <CitationSidePanel
        isOpen={citationPanel !== null}
        citations={citationPanel?.citations ?? []}
        activeIndex={citationPanel?.activeIndex ?? null}
        onClose={() => setCitationPanel(null)}
      />

      <DeleteConfirmationDialog
        isOpen={deleteTarget !== null}
        title="Eliminar conversación"
        message="¿Estás seguro de que querés eliminar esta conversación? Esta acción no se puede deshacer."
        onCancel={() => setDeleteTarget(null)}
        onConfirm={() => deleteTarget && handleDeleteConv(deleteTarget)}
      />
    </div>
  );
}

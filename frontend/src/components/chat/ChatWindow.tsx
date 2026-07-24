/** Chat window — displays messages and input area. */

import { useEffect, useRef } from "react";
import type { ChatMessage } from "../../hooks/useChat";
import { ChatInput } from "./ChatInput";
import { MessageBubble } from "./MessageBubble";

interface CitationData {
  index: number;
  document_name: string;
  page: number | string;
  text_preview: string;
}

interface ChatWindowProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  onSend: (message: string) => Promise<void> | void;
  onCitationClick?: (citation: CitationData, allCitations: CitationData[]) => void;
}

export function ChatWindow({ messages, isStreaming, onSend, onCitationClick }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-1">
        {/* Initial state — no messages yet */}
        {messages.length === 0 && !isStreaming && (
          <div className="flex flex-col items-center justify-center h-full text-center p-8">
            <div className="w-16 h-16 mb-4 rounded-full bg-blue-100 flex items-center justify-center">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Tus documentos están listos
            </h3>
            <p className="text-sm text-gray-500 max-w-sm">
              Hacé una pregunta sobre su contenido.
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble
            key={i}
            message={msg}
            onCitationClick={onCitationClick}
          />
        ))}

        {/* Skeleton loading bars — ChatGPT-style while waiting for first token of a new assistant message */}
        {isStreaming && messages.length > 0 && messages[messages.length - 1].role === "assistant" && messages[messages.length - 1].content === "" && (
          <div className="flex justify-start mb-4">
            <div className="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-3">
              <div className="flex gap-1.5 items-center h-6">
                <div className="w-1.5 h-4 bg-blue-500 rounded-full skeleton-bar" />
                <div className="w-1.5 h-3 bg-blue-500 rounded-full skeleton-bar" />
                <div className="w-1.5 h-5 bg-blue-500 rounded-full skeleton-bar" />
              </div>
            </div>
          </div>
        )}

        {/* Streaming cursor on last assistant message */}
        {isStreaming && messages.length > 0 && messages[messages.length - 1].role === "assistant" && messages[messages.length - 1].content !== "" && (
          <div className="flex justify-start mb-4">
            <span className="inline-block w-2 h-4 bg-blue-600 animate-pulse rounded-sm ml-1" />
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <ChatInput onSend={onSend} isStreaming={isStreaming} />
    </div>
  );
}

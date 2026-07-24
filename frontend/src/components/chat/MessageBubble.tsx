/** Message bubble component — renders user or assistant messages. */

import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "../../hooks/useChat";

interface CitationData {
  index: number;
  document_name: string;
  page: number | string;
  text_preview: string;
}

interface MessageBubbleProps {
  message: ChatMessage;
  onCitationClick?: (citation: CitationData, allCitations: CitationData[]) => void;
}

export function MessageBubble({ message, onCitationClick }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const citations = (message.citations ?? []) as CitationData[];
  const hasCitations = !isUser && citations.length > 0;

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-blue-600 text-white rounded-br-md"
            : "bg-gray-100 text-gray-900 rounded-bl-md"
        }`}
      >
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="prose prose-sm max-w-none">
            <Markdown remarkPlugins={[remarkGfm]}>{message.content}</Markdown>
          </div>
        )}

        {/* Citation badges — click to open side panel */}
        {hasCitations && (
          <div className="flex flex-wrap gap-1 mt-2">
            {citations.map((citation) => (
              <button
                key={citation.index}
                type="button"
                onClick={() => onCitationClick?.(citation, citations)}
                className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded-full hover:bg-blue-200 transition-colors cursor-pointer"
              >
                [{citation.index}]
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/** Message bubble component — renders user or assistant messages. */

import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "../../hooks/useChat";
import { CitationPopover } from "./CitationPopover";

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const hasCitations = !isUser && message.citations && message.citations.length > 0;

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

        {/* Citation badges with popovers */}
        {hasCitations && (
          <div className="flex flex-wrap gap-1 mt-2">
            {message.citations!.map((citation) => (
              <CitationPopover
                key={citation.index}
                index={citation.index}
                documentName={citation.document_name}
                page={citation.page}
                textPreview={citation.text_preview}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

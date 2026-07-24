/** Citation side panel — shows all cited document chunks for the active assistant message. */

import { useEffect, useRef } from "react";

interface Citation {
  index: number;
  document_name: string;
  page: number | string;
  text_preview: string;
}

interface CitationSidePanelProps {
  isOpen: boolean;
  citations: Citation[];
  activeIndex: number | null;
  onClose: () => void;
}

export function CitationSidePanel({
  isOpen,
  citations,
  activeIndex,
  onClose,
}: CitationSidePanelProps) {
  const activeRef = useRef<HTMLDivElement>(null);

  // Scroll active citation into view when it changes
  useEffect(() => {
    if (isOpen && activeIndex !== null && activeRef.current) {
      activeRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [isOpen, activeIndex]);

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 z-40 transition-opacity"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Panel */}
      <div
        className={`fixed top-14 right-0 h-[calc(100vh-3.5rem)] w-96 bg-white border-l border-gray-200 shadow-xl z-50 transform transition-transform duration-300 ease-in-out ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
          <h2 className="text-sm font-semibold text-gray-900">
            Documentos citados
          </h2>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Cerrar panel"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto h-full pb-8">
          {citations.length === 0 ? (
            <div className="flex items-center justify-center h-32 text-sm text-gray-400">
              No hay documentos citados.
            </div>
          ) : (
            <div className="p-3 space-y-3">
              {citations.map((citation) => {
                const isActive = citation.index === activeIndex;
                return (
                  <div
                    key={citation.index}
                    ref={isActive ? activeRef : undefined}
                    className={`rounded-lg border p-3 transition-colors ${
                      isActive
                        ? "border-blue-400 bg-blue-50 ring-1 ring-blue-300"
                        : "border-gray-200 bg-white hover:border-gray-300"
                    }`}
                  >
                    {/* Header row */}
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <span
                          className={`inline-flex items-center justify-center w-5 h-5 text-xs font-bold rounded-full flex-shrink-0 ${
                            isActive
                              ? "bg-blue-600 text-white"
                              : "bg-blue-100 text-blue-800"
                          }`}
                        >
                          {citation.index}
                        </span>
                        <span className="text-xs font-medium text-gray-900 truncate">
                          {citation.document_name}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500 flex-shrink-0 ml-2">
                        Pág. {citation.page}
                      </span>
                    </div>

                    {/* Text preview — full content, not truncated */}
                    <p
                      className={`text-xs leading-relaxed ${
                        isActive ? "text-blue-900" : "text-gray-600"
                      }`}
                    >
                      {citation.text_preview}
                    </p>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

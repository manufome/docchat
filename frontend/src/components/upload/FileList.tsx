/** List of uploaded documents with status and delete action. */

import { documents } from "../../lib/api";
import type { Document } from "../../types";

interface Props {
  docs: Document[];
  onDeleted: (id: string) => void;
  onError: (msg: string) => void;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("es-AR", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function FileIcon({ type }: { type: string }) {
  const iconPath =
    type === "pdf"
      ? "M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
      : type === "docx"
        ? "M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zM14 2v6h6"
        : "M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zM14 2v6h6M8 13h2m-2 4h6m4-8l-4-4";

  return (
    <svg
      className="w-8 h-8 text-gray-400 shrink-0"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
        d={iconPath}
      />
    </svg>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    processing: "bg-yellow-100 text-yellow-800",
    ready: "bg-green-100 text-green-800",
    failed: "bg-red-100 text-red-800",
  };

  const labels: Record<string, string> = {
    processing: "Procesando",
    ready: "Listo",
    failed: "Error",
  };

  return (
    <span
      className={`inline-block px-2 py-0.5 text-xs font-medium rounded-full ${
        styles[status] ?? "bg-gray-100 text-gray-800"
      }`}
    >
      {labels[status] ?? status}
    </span>
  );
}

export default function FileList({ docs, onDeleted, onError }: Props) {
  if (docs.length === 0) {
    return (
      <div className="py-12 text-center text-gray-400">
        <p className="text-sm">Aún no has subido documentos.</p>
        <p className="text-xs mt-1">
          Arrastra un archivo arriba para comenzar.
        </p>
      </div>
    );
  }

  const handleDelete = async (id: string, filename: string) => {
    try {
      await documents.remove(id);
      onDeleted(id);
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? `Error al eliminar ${filename}: ${err.message}`
          : "Error al eliminar el documento.";
      onError(msg);
    }
  };

  return (
    <ul className="divide-y divide-gray-100">
      {docs.map((doc) => (
        <li
          key={doc.id}
          className="flex items-center gap-3 py-3 px-2 rounded-lg hover:bg-gray-50 transition-colors"
        >
          <FileIcon type={doc.file_type} />

          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">
              {doc.filename}
            </p>
            <p className="text-xs text-gray-500">
              {formatSize(doc.file_size)} · {formatDate(doc.created_at)}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <StatusBadge status={doc.status} />

            {doc.status === "ready" && (
              <button
                type="button"
                className="px-2 py-1 text-xs font-medium text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                title="Iniciar chat con este documento"
              >
                Chat
              </button>
            )}

            <button
              type="button"
              onClick={() => handleDelete(doc.id, doc.filename)}
              className="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-md transition-colors"
              title="Eliminar documento"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
          </div>
        </li>
      ))}
    </ul>
  );
}

/** Drag-and-drop file upload zone with validation feedback. */

import { useCallback, useState } from "react";
import { useDropzone, type FileRejection } from "react-dropzone";
import { documents } from "../../lib/api";
import type { Document } from "../../types";

const ACCEPTED_TYPES: Record<string, string[]> = {
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
    ".docx",
  ],
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
};

const MAX_SIZE = 10 * 1024 * 1024; // 10 MB

interface Props {
  onUploaded: (doc: Document) => void;
  onError: (msg: string) => void;
}

export default function FileDropzone({ onUploaded, onError }: Props) {
  const [uploading, setUploading] = useState(false);

  const onDrop = useCallback(
    async (accepted: File[], rejected: FileRejection[]) => {
      for (const r of rejected) {
        const msg =
          r.errors[0]?.code === "file-too-large"
            ? `El archivo ${r.file.name} excede el tamaño máximo de 10 MB.`
            : r.errors[0]?.code === "file-invalid-type"
              ? `Tipo de archivo no soportado: ${r.file.name}. Permitidos: PDF, DOCX, XLSX.`
              : `Error con ${r.file.name}: ${r.errors[0]?.message ?? "desconocido"}`;
        onError(msg);
      }

      for (const file of accepted) {
        setUploading(true);
        try {
          const doc = await documents.upload(file);
          onUploaded(doc);
        } catch (err: unknown) {
          const msg =
            err instanceof Error ? err.message : "Error al subir el archivo.";
          onError(msg);
        } finally {
          setUploading(false);
        }
      }
    },
    [onUploaded, onError],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: MAX_SIZE,
    maxFiles: 1,
    disabled: uploading,
  });

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
        isDragActive
          ? "border-blue-500 bg-blue-50"
          : "border-gray-300 hover:border-blue-400 hover:bg-gray-50"
      } ${uploading ? "opacity-50 pointer-events-none" : ""}`}
    >
      <input {...getInputProps()} />
      {uploading ? (
        <div className="flex flex-col items-center gap-2">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-gray-600">Subiendo archivo...</p>
        </div>
      ) : isDragActive ? (
        <p className="text-blue-600 font-medium">Suelta el archivo aquí...</p>
      ) : (
        <div>
          <svg
            className="w-10 h-10 mx-auto mb-3 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          <p className="text-gray-600">
            Arrastra tu archivo aquí o haz clic para seleccionar
          </p>
          <p className="mt-1 text-xs text-gray-400">
            PDF, DOCX o XLSX · Máximo 10 MB
          </p>
        </div>
      )}
    </div>
  );
}

/** Dashboard page: document upload, management, and chat entry point. */

import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import FileDropzone from "../components/upload/FileDropzone";
import FileList from "../components/upload/FileList";
import { useToast } from "../components/shared/Toast";
import { DeleteConfirmationDialog } from "../components/shared/DeleteConfirmationDialog";
import { documents } from "../lib/api";
import type { Document } from "../types";

export default function DashboardPage() {
  const { addToast } = useToast();
  const navigate = useNavigate();
  const [docs, setDocs] = useState<Document[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleteTarget, setDeleteTarget] = useState<Document | null>(null);

  const loadDocs = useCallback(async () => {
    try {
      setLoading(true);
      const data = await documents.list();
      setDocs(data);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Error al cargar documentos.";
      setError(msg);
      addToast("No se puede conectar con el servidor. Verifica que el backend esté corriendo.", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    loadDocs();
  }, [loadDocs]);

  const handleUploaded = useCallback(
    (doc: Document) => {
      setDocs((prev) => [doc, ...prev]);
      setError(null);
      addToast("Documento subido correctamente.", "success");
    },
    [addToast],
  );

  const handleDeleted = useCallback(
    (id: string) => {
      setDocs((prev) => prev.filter((d) => d.id !== id));
      setDeleteTarget(null);
      addToast("Documento eliminado.", "info");
    },
    [addToast],
  );

  const handleError = useCallback(
    (msg: string) => {
      addToast(msg, "error");
      setTimeout(() => setError(null), 5000);
    },
    [addToast],
  );

  const confirmDelete = useCallback(async () => {
    if (!deleteTarget) return;
    try {
      await documents.remove(deleteTarget.id);
      handleDeleted(deleteTarget.id);
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? `Error al eliminar ${deleteTarget.filename}: ${err.message}`
          : "Error al eliminar el documento.";
      addToast(msg, "error");
      setDeleteTarget(null);
    }
  }, [deleteTarget, handleDeleted, addToast]);

  const hasReadyDocs = docs.some((d) => d.status === "ready");

  // Check if backend is reachable — show a different empty state when offline
  const isOnline = !error || error.includes("token") || error.includes("401");

  return (
    <div className="max-w-3xl mx-auto p-6 mt-4">
      {/* Upload zone */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">
          Subir documento
        </h2>
        <FileDropzone onUploaded={handleUploaded} onError={handleError} />
      </section>

      {/* Documents list */}
      <section>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">
          Mis documentos
          {docs.length > 0 && (
            <span className="ml-2 text-sm font-normal text-gray-400">
              ({docs.length}/4)
            </span>
          )}
        </h2>

        {loading ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
            <div className="flex items-center justify-center py-8">
              <div className="w-6 h-6 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
            </div>
          </div>
        ) : docs.length === 0 && !isOnline ? (
          /* Error state — backend connection error */
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
            <div className="w-14 h-14 mx-auto mb-4 rounded-full bg-red-100 flex items-center justify-center">
              <svg className="w-7 h-7 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-1">
              No se puede conectar con el servidor
            </h3>
            <p className="text-sm text-gray-500 mb-4">
              Verifica que el backend esté corriendo e intenta de nuevo.
            </p>
            <button
              onClick={loadDocs}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Reintentar
            </button>
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <FileList
              docs={docs}
              onDeleted={(id) => {
                const doc = docs.find((d) => d.id === id);
                if (doc) setDeleteTarget(doc);
              }}
            />
          </div>
        )}
      </section>

      {/* Chat CTA */}
      {!loading && hasReadyDocs && (
        <div className="mt-8 text-center page-enter">
          <p className="text-sm text-gray-500 mb-3">
            Tienes documentos listos para consultar.
          </p>
          <button
            onClick={() => navigate("/chat")}
            className="inline-block px-6 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Ir al chat
          </button>
        </div>
      )}

      {/* Delete confirmation dialog */}
      <DeleteConfirmationDialog
        isOpen={deleteTarget !== null}
        title="Eliminar documento"
        message={
          deleteTarget
            ? `¿Estás seguro de que querés eliminar "${deleteTarget.filename}"? Esta acción no se puede deshacer.`
            : ""
        }
        onCancel={() => setDeleteTarget(null)}
        onConfirm={confirmDelete}
      />
    </div>
  );
}

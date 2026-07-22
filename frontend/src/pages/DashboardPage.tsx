/** Dashboard page: document upload, management, and chat entry point. */

import { useCallback, useEffect, useState } from "react";
import FileDropzone from "../components/upload/FileDropzone";
import FileList from "../components/upload/FileList";
import { useAuth } from "../contexts/AuthContext";
import { documents } from "../lib/api";
import type { Document } from "../types";

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const [docs, setDocs] = useState<Document[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadDocs = useCallback(async () => {
    try {
      setLoading(true);
      const data = await documents.list();
      setDocs(data);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Error al cargar documentos.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDocs();
  }, [loadDocs]);

  const handleUploaded = useCallback((doc: Document) => {
    setDocs((prev) => [doc, ...prev]);
    setError(null);
  }, []);

  const handleDeleted = useCallback((id: string) => {
    setDocs((prev) => prev.filter((d) => d.id !== id));
    setError(null);
  }, []);

  const handleError = useCallback((msg: string) => {
    setError(msg);
    setTimeout(() => setError(null), 5000);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 bg-white shadow-sm">
        <h1 className="text-xl font-bold text-gray-900">DocChat</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600">{user?.email}</span>
          <button
            onClick={logout}
            className="px-4 py-1.5 text-sm text-gray-700 border rounded-lg hover:bg-gray-100"
          >
            Cerrar Sesión
          </button>
        </div>
      </header>

      <main className="max-w-3xl p-6 mx-auto mt-4">
        {/* Error toast */}
        {error && (
          <div className="mb-4 px-4 py-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">
            {error}
          </div>
        )}

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
            <div className="flex items-center justify-center py-12">
              <div className="w-6 h-6 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <FileList
                docs={docs}
                onDeleted={handleDeleted}
                onError={handleError}
              />
            </div>
          )}
        </section>

        {/* Empty state CTA */}
        {!loading && docs.length > 0 && docs.some((d) => d.status === "ready") && (
          <div className="mt-8 text-center">
            <p className="text-sm text-gray-500 mb-2">
              Tienes documentos listos para consultar.
            </p>
            <p className="text-xs text-gray-400">
              La funcionalidad de chat estará disponible próximamente.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

/** Settings page — configure OpenAI API key. */

import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useToast } from "../components/shared/Toast";
import { auth } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";

export default function SettingsPage() {
  const { user } = useAuth();
  const { addToast } = useToast();
  const navigate = useNavigate();
  const [apiKey, setApiKey] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSave = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!apiKey.trim()) return;

      setSaving(true);
      try {
        await auth.setApiKey({ openai_api_key: apiKey.trim() });
        addToast("API key guardada correctamente.", "success");
        setApiKey("");
      } catch (err: unknown) {
        const msg =
          err instanceof Error ? err.message : "Error al guardar la API key.";
        addToast(msg, "error");
      } finally {
        setSaving(false);
      }
    },
    [apiKey, addToast],
  );

  return (
    <div className="max-w-lg mx-auto p-6 mt-8">
      <button
        onClick={() => navigate(-1)}
        className="mb-6 text-sm text-gray-500 hover:text-gray-700 transition-colors inline-flex items-center gap-1"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Volver
      </button>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <h1 className="text-xl font-semibold text-gray-900 mb-1">Configuración</h1>
        <p className="text-sm text-gray-500 mb-6">
          Configura tu API key de OpenAI para usar DocChat.
        </p>

        {/* User info */}
        <div className="mb-6 p-3 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-500 mb-0.5">Usuario</p>
          <p className="text-sm font-medium text-gray-900">{user?.email}</p>
        </div>

        {/* API Key form */}
        <form onSubmit={handleSave}>
          <label
            htmlFor="api-key"
            className="block text-sm font-medium text-gray-700 mb-1.5"
          >
            OpenAI API Key
          </label>
          <input
            id="api-key"
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="sk-..."
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p className="mt-1 text-xs text-gray-400">
            Tu API key solo se almacena en el servidor y nunca se comparte.
          </p>

          <button
            type="submit"
            disabled={saving || !apiKey.trim()}
            className="mt-4 w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {saving ? "Guardando..." : "Guardar API Key"}
          </button>
        </form>
      </div>
    </div>
  );
}

/** Settings page — configure LLM provider and API key. */

import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useToast } from "../components/shared/Toast";
import { auth } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";

const PROVIDERS = [
  { value: "openai", label: "OpenAI (GPT-4o)", placeholder: "sk-..." },
  { value: "gemini", label: "Google Gemini 2.0 Flash", placeholder: "AIza..." },
  { value: "groq", label: "Groq (Llama 3.3 70B)", placeholder: "gsk_..." },
] as const;

type Provider = (typeof PROVIDERS)[number]["value"];

export default function SettingsPage() {
  const { user } = useAuth();
  const { addToast } = useToast();
  const navigate = useNavigate();
  const [apiKey, setApiKey] = useState("");
  const [provider, setProvider] = useState<Provider>("openai");
  const [currentProvider, setCurrentProvider] = useState<Provider>("openai");
  const [hasKey, setHasKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await auth.getProvider();
        setCurrentProvider(res.provider as Provider);
        setProvider(res.provider as Provider);
        setHasKey(res.has_key);
      } catch {
        // fallback to defaults
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const currentProviderMeta = PROVIDERS.find((p) => p.value === currentProvider);
  const selectedProviderMeta = PROVIDERS.find((p) => p.value === provider);

  const handleSave = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!apiKey.trim()) return;

      setSaving(true);
      try {
        await auth.setApiKey({ api_key: apiKey.trim(), provider });
        addToast(
          `API key de ${selectedProviderMeta?.label} guardada correctamente.`,
          "success",
        );
        setCurrentProvider(provider);
        setHasKey(true);
        setApiKey("");
      } catch (err: unknown) {
        const msg =
          err instanceof Error ? err.message : "Error al guardar la API key.";
        addToast(msg, "error");
      } finally {
        setSaving(false);
      }
    },
    [apiKey, provider, selectedProviderMeta, addToast],
  );

  if (loading) {
    return (
      <div className="max-w-lg mx-auto p-6 mt-8">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3" />
          <div className="h-4 bg-gray-200 rounded w-1/2" />
          <div className="h-32 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

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
          Configura el proveedor de IA y tu API key para usar DocChat.
        </p>

        {/* User info */}
        <div className="mb-6 p-3 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-500 mb-0.5">Usuario</p>
          <p className="text-sm font-medium text-gray-900">{user?.email}</p>
          {hasKey && currentProviderMeta && (
            <p className="text-xs text-green-600 mt-1">
              ✓ API key de {currentProviderMeta.label} configurada
            </p>
          )}
        </div>

        {/* Provider form */}
        <form onSubmit={handleSave}>
          {/* Provider selector */}
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            Proveedor de IA
          </label>
          <div className="grid grid-cols-3 gap-2 mb-4">
            {PROVIDERS.map((p) => (
              <button
                key={p.value}
                type="button"
                onClick={() => setProvider(p.value)}
                className={`px-3 py-2 text-xs font-medium rounded-lg border transition-colors ${
                  provider === p.value
                    ? "border-blue-500 bg-blue-50 text-blue-700"
                    : "border-gray-200 bg-white text-gray-600 hover:border-gray-300"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>

          {/* API Key input */}
          <label htmlFor="api-key" className="block text-sm font-medium text-gray-700 mb-1.5">
            API Key
          </label>
          <input
            id="api-key"
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder={selectedProviderMeta?.placeholder}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p className="mt-1 text-xs text-gray-400">
            Tu API key se almacena encriptada en el servidor y nunca se comparte.
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

      {/* Info box */}
      <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800">
        <p className="font-medium mb-1">ℹ️ Proveedores gratuitos</p>
        <ul className="list-disc list-inside space-y-0.5">
          <li><strong>Google Gemini</strong> — capa gratuita: 60 solicitudes por minuto</li>
          <li><strong>Groq</strong> — capa gratuita: 30 solicitudes por minuto, modelos open-source</li>
          <li><strong>OpenAI</strong> — requiere crédito pago (~$1-3/mes para uso personal)</li>
        </ul>
      </div>
    </div>
  );
}

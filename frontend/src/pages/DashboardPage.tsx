/** Dashboard page (placeholder for future phases). */

import { useAuth } from "../contexts/AuthContext";

export default function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
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

      <main className="max-w-4xl p-6 mx-auto mt-8">
        <div className="p-12 text-center bg-white rounded-xl shadow-sm">
          <h2 className="mb-4 text-2xl font-semibold text-gray-900">
            Bienvenido a DocChat
          </h2>
          <p className="text-gray-600">
            Sube tus documentos y haz preguntas en lenguaje natural.
            Esta funcionalidad estará disponible próximamente.
          </p>
        </div>
      </main>
    </div>
  );
}

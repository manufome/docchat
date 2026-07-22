/** Shared layout component with header navigation. */

import { Link, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

export default function Layout() {
  const { user, isAuthenticated, logout } = useAuth();
  const location = useLocation();
  const isAuthPage = location.pathname === "/login" || location.pathname === "/register";

  return (
    <div className="min-h-screen bg-gray-50 page-enter">
      {/* Header — only shown for authenticated users on non-auth pages */}
      {isAuthenticated && !isAuthPage && (
        <header className="sticky top-0 z-40 bg-white border-b border-gray-200 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-14">
              {/* Brand */}
              <Link
                to="/"
                className="text-lg font-bold text-gray-900 hover:text-blue-600 transition-colors"
              >
                DocChat
              </Link>

              {/* Navigation links */}
              <nav className="flex items-center gap-1">
                <Link
                  to="/"
                  className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                    location.pathname === "/"
                      ? "text-blue-600 bg-blue-50"
                      : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                  }`}
                >
                  Documentos
                </Link>
                <Link
                  to="/chat"
                  className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                    location.pathname === "/chat"
                      ? "text-blue-600 bg-blue-50"
                      : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                  }`}
                >
                  Chat
                </Link>
              </nav>

              {/* User section */}
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-500 hidden sm:inline">
                  {user?.email}
                </span>
                <Link
                  to="/settings"
                  className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                  title="Configuración"
                  aria-label="Configuración"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </Link>
                <button
                  onClick={logout}
                  className="px-3 py-1.5 text-sm font-medium text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 hover:text-gray-900 transition-colors"
                >
                  Cerrar sesión
                </button>
              </div>
            </div>
          </div>
        </header>
      )}

      {/* Page content */}
      <main>
        <Outlet />
      </main>
    </div>
  );
}

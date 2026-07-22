import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider } from "../../contexts/AuthContext";
import { ToastProvider } from "../../components/shared/Toast";
import ChatPage from "../ChatPage";

let mockResponse: unknown = [];

beforeEach(() => {
  mockResponse = [];
  vi.stubGlobal("fetch", vi.fn().mockImplementation(async (url: string) => {
    if (url.includes("/api/conversations/") && url.endsWith("/messages")) {
      return { ok: true, json: async () => [] };
    }
    return { ok: true, json: async () => mockResponse };
  }));
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

function renderWithProviders() {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <ChatPage />
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>,
  );
}

describe("ChatPage", () => {
  it("renders sidebar with new chat button", async () => {
    mockResponse = [];
    renderWithProviders();

    const buttons = await screen.findAllByText(/nueva conversación/i);
    expect(buttons.length).toBeGreaterThanOrEqual(1);
  });

  it("shows conversation list in sidebar", async () => {
    mockResponse = [
      { id: "1", title: "Chat 1", created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z" },
      { id: "2", title: "Chat 2", created_at: "2024-01-02T00:00:00Z", updated_at: "2024-01-02T00:00:00Z" },
    ];

    renderWithProviders();

    expect(await screen.findByText("Chat 1")).toBeInTheDocument();
    expect(await screen.findByText("Chat 2")).toBeInTheDocument();
  });

  it("shows empty state when no conversation selected", async () => {
    mockResponse = [];
    renderWithProviders();

    expect(await screen.findByText(/Selecciona una conversación/i)).toBeInTheDocument();
  });

  it("loads messages when a conversation is selected", async () => {
    mockResponse = [
      { id: "1", title: "Chat 1", created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z" },
    ];

    renderWithProviders();

    const chatTitle = await screen.findByText("Chat 1");
    expect(chatTitle).toBeInTheDocument();

    const user = userEvent.setup();
    await user.click(chatTitle);

    await waitFor(() => {
      expect(screen.getByText(/Tus documentos están listos/i)).toBeInTheDocument();
    });
  });
});

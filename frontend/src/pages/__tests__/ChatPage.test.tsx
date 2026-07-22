import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider } from "../../contexts/AuthContext";
import ChatPage from "../ChatPage";

let mockResponse: unknown = [];

beforeEach(() => {
  mockResponse = [];
  vi.stubGlobal("fetch", vi.fn().mockImplementation(async (url: string) => {
    // Return conversations for /api/conversations, messages for /api/conversations/*/messages
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
        <ChatPage />
      </AuthProvider>
    </BrowserRouter>,
  );
}

describe("ChatPage", () => {
  it("renders sidebar with new chat button", async () => {
    mockResponse = [];
    renderWithProviders();

    const newChatBtn = await screen.findByText(/nueva conversación/i);
    expect(newChatBtn).toBeInTheDocument();
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
      expect(screen.getByText(/Sube documentos/i)).toBeInTheDocument();
    });
  });
});

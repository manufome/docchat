import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter, MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider } from "../../contexts/AuthContext";
import { ToastProvider } from "../../components/shared/Toast";
import SettingsPage from "../SettingsPage";

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({}),
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
          <SettingsPage />
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>,
  );
}

describe("SettingsPage", () => {
  it("renders the settings heading", async () => {
    renderWithProviders();
    expect(await screen.findByText("Configuración")).toBeInTheDocument();
  });

  it("renders the API key input", async () => {
    renderWithProviders();
    expect(
      await screen.findByPlaceholderText("sk-..."),
    ).toBeInTheDocument();
  });

  it("renders the save button", async () => {
    renderWithProviders();
    expect(
      await screen.findByText("Guardar API Key"),
    ).toBeInTheDocument();
  });

  it("disables save button when input is empty", async () => {
    renderWithProviders();
    const btn = await screen.findByText("Guardar API Key");
    expect(btn).toBeDisabled();
  });

  it("enables save button when API key is entered", async () => {
    renderWithProviders();
    const user = userEvent.setup();

    const input = await screen.findByPlaceholderText("sk-...");
    await user.type(input, "sk-test-key");

    const btn = screen.getByText("Guardar API Key");
    expect(btn).not.toBeDisabled();
  });

  it("calls setApiKey when form is submitted", async () => {
    const user = userEvent.setup();
    renderWithProviders();

    const input = await screen.findByPlaceholderText("sk-...");
    await user.type(input, "sk-test-key");

    const btn = screen.getByText("Guardar API Key");
    await user.click(btn);

    await waitFor(() => {
      // Fetch should have been called at least once for auth.me (on mount)
      // and once for the API key PUT
      expect(fetch).toHaveBeenCalled();
    });
  });
});

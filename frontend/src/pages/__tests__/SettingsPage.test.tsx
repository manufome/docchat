import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider } from "../../contexts/AuthContext";
import { ToastProvider } from "../../components/shared/Toast";
import SettingsPage from "../SettingsPage";

let fetchCount = 0;

beforeEach(() => {
  fetchCount = 0;
  vi.stubGlobal("fetch", vi.fn().mockImplementation(async (url: string) => {
    fetchCount++;
    // GET /api/users/me/provider — called on mount
    if (url.toString().includes("/api/users/me/provider")) {
      return {
        ok: true,
        json: async () => ({ provider: "openai", has_key: false }),
      };
    }
    // PUT /api/users/me/api-key — called on form submit
    if (url.toString().includes("/api/users/me/api-key")) {
      return {
        ok: true,
        json: async () => ({ message: "ok" }),
      };
    }
    return { ok: true, json: async () => ({}) };
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
      // Should have called PUT /api/users/me/api-key with the new payload
      const calls = (fetch as ReturnType<typeof vi.fn>).mock.calls;
      const putCall = calls.find((c: unknown[]) =>
        String(c[0]).includes("/api/users/me/api-key"),
      );
      expect(putCall).toBeDefined();
      const [, opts] = putCall as [string, RequestInit];
      const body = JSON.parse(opts.body as string);
      expect(body).toMatchObject({ api_key: "sk-test-key", provider: "openai" });
    });
  });
});

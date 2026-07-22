import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import App from "../App";

vi.mock("../lib/api", () => ({
  auth: {
    login: vi.fn(),
    register: vi.fn(),
    me: vi.fn().mockRejectedValue(new Error("No token")),
    setApiKey: vi.fn(),
  },
}));

describe("App", () => {
  it("renders login page by default when not authenticated", async () => {
    render(<App />);

    // Should redirect to /login when no token
    const heading = await screen.findByRole("heading", {
      name: /iniciar sesión/i,
    });
    expect(heading).toBeInTheDocument();
  });

  it("has register link on login page", async () => {
    render(<App />);

    const registerLink = await screen.findByRole("link", {
      name: /regístrate/i,
    });
    expect(registerLink).toBeInTheDocument();
    expect(registerLink).toHaveAttribute("href", "/register");
  });
});

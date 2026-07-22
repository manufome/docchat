import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import LoginForm from "../LoginForm";
import { AuthProvider } from "../../../contexts/AuthContext";

// Mock the API module
vi.mock("../../../lib/api", () => ({
  auth: {
    login: vi.fn(),
    register: vi.fn(),
    me: vi.fn().mockRejectedValue(new Error("No token")),
    setApiKey: vi.fn(),
  },
}));

function renderLoginForm() {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <LoginForm />
      </AuthProvider>
    </BrowserRouter>,
  );
}

describe("LoginForm", () => {
  it("renders email and password inputs", () => {
    renderLoginForm();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/contraseña/i)).toBeInTheDocument();
  });

  it("shows a register link", () => {
    renderLoginForm();
    expect(screen.getByText(/regístrate/i)).toBeInTheDocument();
  });

  it("shows error when submitting empty form", async () => {
    const user = userEvent.setup();
    renderLoginForm();

    await user.click(screen.getByRole("button", { name: /ingresar/i }));
    expect(screen.getByText("Completa todos los campos")).toBeInTheDocument();
  });

  it("submits with valid data", async () => {
    const { auth } = await import("../../../lib/api");
    const user = userEvent.setup();
    renderLoginForm();

    await user.type(screen.getByLabelText(/email/i), "test@test.com");
    await user.type(screen.getByLabelText(/contraseña/i), "password123");
    await user.click(screen.getByRole("button", { name: /ingresar/i }));

    expect(auth.login).toHaveBeenCalledWith({
      email: "test@test.com",
      password: "password123",
    });
  });
});

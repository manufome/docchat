import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import RegisterForm from "../RegisterForm";
import { AuthProvider } from "../../../contexts/AuthContext";

vi.mock("../../../lib/api", () => ({
  auth: {
    login: vi.fn(),
    register: vi.fn(),
    me: vi.fn().mockRejectedValue(new Error("No token")),
    setApiKey: vi.fn(),
  },
}));

function renderRegisterForm() {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <RegisterForm />
      </AuthProvider>
    </BrowserRouter>,
  );
}

describe("RegisterForm", () => {
  it("renders all fields", () => {
    renderRegisterForm();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    const pwInputs = screen.getAllByLabelText(/contraseña/i);
    expect(pwInputs).toHaveLength(2);
  });

  it("shows error on short password", async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    await user.type(screen.getByLabelText(/email/i), "test@test.com");
    const pwInputs = screen.getAllByLabelText(/contraseña/i) as HTMLInputElement[];
    await user.type(pwInputs[0], "123");
    await user.type(pwInputs[1], "123");
    await user.click(screen.getByRole("button", { name: /crear cuenta/i }));

    expect(
      screen.getByText("La contraseña debe tener al menos 8 caracteres"),
    ).toBeInTheDocument();
  });

  it("shows error on password mismatch", async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    await user.type(screen.getByLabelText(/email/i), "test@test.com");
    const pwInputs = screen.getAllByLabelText(/contraseña/i) as HTMLInputElement[];
    await user.type(pwInputs[0], "password123");
    await user.type(pwInputs[1], "different456");
    await user.click(screen.getByRole("button", { name: /crear cuenta/i }));

    expect(
      screen.getByText("Las contraseñas no coinciden"),
    ).toBeInTheDocument();
  });

  it("submits with valid data", async () => {
    const { auth } = await import("../../../lib/api");
    const user = userEvent.setup();
    renderRegisterForm();

    await user.type(screen.getByLabelText(/email/i), "new@test.com");
    const pwInputs = screen.getAllByLabelText(/contraseña/i) as HTMLInputElement[];
    await user.type(pwInputs[0], "password123");
    await user.type(pwInputs[1], "password123");
    await user.click(screen.getByRole("button", { name: /crear cuenta/i }));

    expect(auth.register).toHaveBeenCalledWith({
      email: "new@test.com",
      password: "password123",
    });
  });
});

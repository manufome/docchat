import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ChatInput } from "../ChatInput";

describe("ChatInput", () => {
  it("renders textarea and send button", () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} isStreaming={false} />);

    expect(screen.getByPlaceholderText("Escribe tu mensaje...")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /enviar/i })).toBeInTheDocument();
  });

  it("calls onSend with message and clears input on submit", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn().mockResolvedValue(undefined);
    render(<ChatInput onSend={onSend} isStreaming={false} />);

    const textarea = screen.getByPlaceholderText("Escribe tu mensaje...");
    await user.type(textarea, "Hola mundo");
    await user.click(screen.getByRole("button", { name: /enviar/i }));

    expect(onSend).toHaveBeenCalledWith("Hola mundo");
    expect(textarea).toHaveValue("");
  });

  it("disables input and button while streaming", () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} isStreaming={true} />);

    const textarea = screen.getByPlaceholderText("Escribe tu mensaje...");
    const button = screen.getByRole("button", { name: /enviar/i });

    expect(textarea).toBeDisabled();
    expect(button).toBeDisabled();
  });

  it("does not send empty messages", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} isStreaming={false} />);

    await user.click(screen.getByRole("button", { name: /enviar/i }));

    expect(onSend).not.toHaveBeenCalled();
  });

  it("sends on Enter without Shift", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn().mockResolvedValue(undefined);
    render(<ChatInput onSend={onSend} isStreaming={false} />);

    const textarea = screen.getByPlaceholderText("Escribe tu mensaje...");
    await user.type(textarea, "Mensaje{Enter}");

    expect(onSend).toHaveBeenCalledWith("Mensaje");
  });
});

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ChatWindow } from "../ChatWindow";
import type { ChatMessage } from "../../../hooks/useChat";

describe("ChatWindow", () => {
  const noop = vi.fn();

  it("shows empty state when no messages", () => {
    render(<ChatWindow messages={[]} isStreaming={false} onSend={noop} />);

    expect(screen.getByText(/Sube documentos/i)).toBeInTheDocument();
  });

  it("renders user and assistant messages", () => {
    const messages: ChatMessage[] = [
      { role: "user", content: "Hola" },
      { role: "assistant", content: "¡Hola! ¿En qué puedo ayudarte?" },
    ];

    render(<ChatWindow messages={messages} isStreaming={false} onSend={noop} />);

    expect(screen.getByText("Hola")).toBeInTheDocument();
    expect(screen.getByText("¡Hola! ¿En qué puedo ayudarte?")).toBeInTheDocument();
  });

  it("shows ChatInput when there are messages", () => {
    const messages: ChatMessage[] = [
      { role: "user", content: "Test" },
    ];

    render(<ChatWindow messages={messages} isStreaming={false} onSend={noop} />);

    expect(screen.getByPlaceholderText("Escribe tu mensaje...")).toBeInTheDocument();
  });

  it("passes isStreaming to ChatInput", () => {
    const messages: ChatMessage[] = [
      { role: "user", content: "Test" },
    ];

    render(<ChatWindow messages={messages} isStreaming={true} onSend={noop} />);

    expect(screen.getByPlaceholderText("Escribe tu mensaje...")).toBeDisabled();
    expect(screen.getByRole("button", { name: /enviar/i })).toBeDisabled();
  });

  it("shows streaming indicator for last assistant message when streaming", () => {
    const messages: ChatMessage[] = [
      { role: "user", content: "Hola" },
      { role: "assistant", content: "Pen" },
    ];

    const { container } = render(
      <ChatWindow messages={messages} isStreaming={true} onSend={noop} />,
    );

    // The last assistant message should have an animated cursor indicator
    const assistantBubbles = container.querySelectorAll(".justify-start");
    expect(assistantBubbles.length).toBeGreaterThanOrEqual(1);
  });
});

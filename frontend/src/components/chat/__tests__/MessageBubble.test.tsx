import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MessageBubble } from "../MessageBubble";
import type { ChatMessage } from "../../../hooks/useChat";

describe("MessageBubble", () => {
  it("renders user message with justify-end alignment", () => {
    const message: ChatMessage = {
      role: "user",
      content: "Hola, ¿cómo estás?",
    };

    const { container } = render(<MessageBubble message={message} />);

    expect(screen.getByText("Hola, ¿cómo estás?")).toBeInTheDocument();
    // User messages are right-aligned in the flex container
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.className).toContain("justify-end");
  });

  it("renders assistant message with justify-start alignment", () => {
    const message: ChatMessage = {
      role: "assistant",
      content: "¡Estoy bien, gracias!",
    };

    const { container } = render(<MessageBubble message={message} />);

    expect(screen.getByText("¡Estoy bien, gracias!")).toBeInTheDocument();
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.className).toContain("justify-start");
  });

  it("renders assistant markdown content", () => {
    const message: ChatMessage = {
      role: "assistant",
      content: "Esto es **negrita** y *cursiva*",
    };

    render(<MessageBubble message={message} />);

    expect(screen.getByText("negrita")).toBeInTheDocument();
    expect(screen.getByText("cursiva")).toBeInTheDocument();
  });

  it("shows citation badges when assistant message has citations", () => {
    const message: ChatMessage = {
      role: "assistant",
      content: "Respuesta basada en documentos[1][2].",
      citations: [
        { index: 1, document_name: "doc1.pdf", page: 2, text_preview: "Texto relevante" },
        { index: 2, document_name: "doc2.pdf", page: 5, text_preview: "Más texto" },
      ],
    };

    render(<MessageBubble message={message} />);

    // Should render citation badges
    expect(screen.getByText("[1]")).toBeInTheDocument();
    expect(screen.getByText("[2]")).toBeInTheDocument();
  });

  it("renders basic text when no citations", () => {
    const message: ChatMessage = {
      role: "assistant",
      content: "Texto simple.",
    };

    render(<MessageBubble message={message} />);

    expect(screen.getByText("Texto simple.")).toBeInTheDocument();
  });
});

import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useChat } from "../useChat";

describe("useChat", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("starts with empty messages and no streaming", () => {
    const { result } = renderHook(() => useChat());

    expect(result.current.messages).toEqual([]);
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("sets isStreaming when sending a message", async () => {
    const mockResponse = new ReadableStream({
      start(controller) {
        controller.enqueue(
          new TextEncoder().encode(
            'data: {"type": "token", "content": "Hello"}\n\ndata: {"type": "done", "message_id": "msg-1"}\n\n',
          ),
        );
        controller.close();
      },
    });

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ "Content-Type": "text/event-stream" }),
      body: mockResponse,
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      result.current.sendMessage("Hi");
    });

    expect(result.current.isStreaming).toBe(false);
    expect(result.current.messages.length).toBe(2); // user + assistant
    expect(result.current.messages[0].role).toBe("user");
    expect(result.current.messages[0].content).toBe("Hi");
    expect(result.current.messages[1].role).toBe("assistant");
    expect(result.current.messages[1].content).toBe("Hello");
  });

  it("accumulates tokens into the assistant message", async () => {
    const mockResponse = new ReadableStream({
      start(controller) {
        controller.enqueue(
          new TextEncoder().encode(
            'data: {"type": "token", "content": "Hello"}\n\n',
          ),
        );
        controller.enqueue(
          new TextEncoder().encode(
            'data: {"type": "token", "content": " World"}\n\n',
          ),
        );
        controller.enqueue(
          new TextEncoder().encode(
            'data: {"type": "done", "message_id": "msg-1"}\n\n',
          ),
        );
        controller.close();
      },
    });

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ "Content-Type": "text/event-stream" }),
      body: mockResponse,
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      result.current.sendMessage("Hi");
    });

    expect(result.current.messages[1].content).toBe("Hello World");
  });

  it("stores citations in the assistant message", async () => {
    const mockResponse = new ReadableStream({
      start(controller) {
        controller.enqueue(
          new TextEncoder().encode(
            'data: {"type": "token", "content": "Respuesta"}\n\n',
          ),
        );
        controller.enqueue(
          new TextEncoder().encode(
            'data: {"type": "citation", "citation": {"index": 1, "document_name": "doc.pdf", "page": 1, "text_preview": "test"}}\n\n',
          ),
        );
        controller.enqueue(
          new TextEncoder().encode(
            'data: {"type": "done", "message_id": "msg-1"}\n\n',
          ),
        );
        controller.close();
      },
    });

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ "Content-Type": "text/event-stream" }),
      body: mockResponse,
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      result.current.sendMessage("Pregunta");
    });

    expect(result.current.messages[1].citations).toHaveLength(1);
    expect(result.current.messages[1].citations![0].index).toBe(1);
  });

  it("handles error events from the stream", async () => {
    const mockResponse = new ReadableStream({
      start(controller) {
        controller.enqueue(
          new TextEncoder().encode(
            'data: {"type": "error", "content": "No hay documentos"}\n\n',
          ),
        );
        controller.close();
      },
    });

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ "Content-Type": "text/event-stream" }),
      body: mockResponse,
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      result.current.sendMessage("Hola");
    });

    expect(result.current.error).toBe("No hay documentos");
    expect(result.current.isStreaming).toBe(false);
  });

  it("handles HTTP errors from fetch", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ detail: "Not authenticated" }),
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("Hola");
    });

    expect(result.current.error).toBe("Not authenticated");
    expect(result.current.isStreaming).toBe(false);
  });

  it("clearMessages resets state", async () => {
    const { result } = renderHook(() => useChat());

    act(() => {
      result.current.clearMessages();
    });

    expect(result.current.messages).toEqual([]);
    expect(result.current.error).toBeNull();
    expect(result.current.isStreaming).toBe(false);
  });
});

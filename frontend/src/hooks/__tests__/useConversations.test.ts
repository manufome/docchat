import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useConversations } from "../useConversations";

describe("useConversations", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.restoreAllMocks();
    fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("loads conversations on mount with empty list", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([]),
    });

    const { result } = renderHook(() => useConversations());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    expect(result.current.conversations).toEqual([]);
    expect(result.current.selectedId).toBeNull();
  });

  it("loads conversations on mount", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve([
          { id: "1", title: "Chat 1", created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z" },
          { id: "2", title: "Chat 2", created_at: "2024-01-02T00:00:00Z", updated_at: "2024-01-02T00:00:00Z" },
        ]),
    });

    const { result } = renderHook(() => useConversations());

    await waitFor(() => {
      expect(result.current.conversations).toHaveLength(2);
    });
    expect(result.current.isLoading).toBe(false);
  });

  it("auto-selects first conversation on load", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve([
          { id: "1", title: "Chat 1", created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z" },
        ]),
    });

    const { result } = renderHook(() => useConversations());

    await waitFor(() => {
      expect(result.current.selectedId).toBe("1");
    });
  });

  it("createConversation adds and selects new conversation", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve([]), // Empty list on load
    });

    const { result } = renderHook(() => useConversations());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Mock create
    fetchMock.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          id: "new-1",
          title: "New Chat",
          created_at: "2024-01-03T00:00:00Z",
          updated_at: "2024-01-03T00:00:00Z",
        }),
    });

    await act(async () => {
      await result.current.createConversation("New Chat");
    });

    expect(result.current.conversations).toHaveLength(1);
    expect(result.current.selectedId).toBe("new-1");
  });

  it("deleteConversation removes conversation and clears selection", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve([
          { id: "1", title: "Chat 1", created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z" },
        ]),
    });

    const { result } = renderHook(() => useConversations());

    await waitFor(() => {
      expect(result.current.selectedId).toBe("1");
    });

    // Mock delete
    fetchMock.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ detail: "Deleted" }),
    });

    await act(async () => {
      await result.current.deleteConversation("1");
    });

    expect(result.current.conversations).toHaveLength(0);
    expect(result.current.selectedId).toBeNull();
  });

  it("selectConversation updates selectedId", () => {
    const { result } = renderHook(() => useConversations());

    act(() => {
      result.current.selectConversation("conv-42");
    });

    expect(result.current.selectedId).toBe("conv-42");
  });

  it("handles load errors gracefully", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ detail: "Server error" }),
    });

    const { result } = renderHook(() => useConversations());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    // Should not crash, conversations should remain empty
    expect(result.current.conversations).toEqual([]);
    expect(result.current.selectedId).toBeNull();
  });
});

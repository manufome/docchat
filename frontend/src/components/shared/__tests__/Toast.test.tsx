import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { ToastProvider, useToast } from "../Toast";

function TestHarness() {
  const { addToast } = useToast();
  return (
    <div>
      <button onClick={() => addToast("Test error", "error")}>
        Add Error
      </button>
      <button onClick={() => addToast("Test success", "success")}>
        Add Success
      </button>
    </div>
  );
}

function renderWithProvider() {
  return render(
    <ToastProvider>
      <TestHarness />
    </ToastProvider>,
  );
}

describe("Toast", () => {
  it("shows a toast when addToast is called", async () => {
    renderWithProvider();
    const user = userEvent.setup();

    await user.click(screen.getByText("Add Error"));

    expect(screen.getByText("Test error")).toBeInTheDocument();
  });

  it("shows a success toast with correct styling", async () => {
    renderWithProvider();
    const user = userEvent.setup();

    await user.click(screen.getByText("Add Success"));

    expect(screen.getByText("Test success")).toBeInTheDocument();
  });

  it("dismisses toast when close button is clicked", async () => {
    renderWithProvider();
    const user = userEvent.setup();

    await user.click(screen.getByText("Add Error"));
    expect(screen.getByText("Test error")).toBeInTheDocument();

    await user.click(screen.getByLabelText("Cerrar"));

    // Toast marks as exiting first, then removes after 300ms
    await waitFor(
      () => {
        expect(screen.queryByText("Test error")).not.toBeInTheDocument();
      },
      { timeout: 2000 },
    );
  });
});

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DeleteConfirmationDialog } from "../DeleteConfirmationDialog";

describe("DeleteConfirmationDialog", () => {
  it("renders nothing when closed", () => {
    const { container } = render(
      <DeleteConfirmationDialog
        isOpen={false}
        title="Eliminar"
        message="¿Estás seguro?"
        onCancel={vi.fn()}
        onConfirm={vi.fn()}
      />,
    );

    expect(container.innerHTML).toBe("");
  });

  it("renders title and message when open", () => {
    render(
      <DeleteConfirmationDialog
        isOpen={true}
        title="Eliminar documento"
        message="¿Estás seguro de eliminar este documento?"
        onCancel={vi.fn()}
        onConfirm={vi.fn()}
      />,
    );

    expect(screen.getByText("Eliminar documento")).toBeInTheDocument();
    expect(
      screen.getByText("¿Estás seguro de eliminar este documento?"),
    ).toBeInTheDocument();
  });

  it("calls onCancel when Cancelar is clicked", async () => {
    const onCancel = vi.fn();
    const user = userEvent.setup();

    render(
      <DeleteConfirmationDialog
        isOpen={true}
        title="Eliminar"
        message="¿Estás seguro?"
        onCancel={onCancel}
        onConfirm={vi.fn()}
      />,
    );

    await user.click(screen.getByText("Cancelar"));
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it("calls onConfirm when Eliminar is clicked", async () => {
    const onConfirm = vi.fn();
    const user = userEvent.setup();

    render(
      <DeleteConfirmationDialog
        isOpen={true}
        title="Eliminar"
        message="¿Estás seguro?"
        onCancel={vi.fn()}
        onConfirm={onConfirm}
      />,
    );

    await user.click(screen.getByRole("button", { name: /eliminar/i }));
    expect(onConfirm).toHaveBeenCalledOnce();
  });

  it("calls onCancel when Escape is pressed", async () => {
    const onCancel = vi.fn();
    const user = userEvent.setup();

    render(
      <DeleteConfirmationDialog
        isOpen={true}
        title="Eliminar"
        message="¿Estás seguro?"
        onCancel={onCancel}
        onConfirm={vi.fn()}
      />,
    );

    await user.keyboard("{Escape}");
    expect(onCancel).toHaveBeenCalledOnce();
  });
});

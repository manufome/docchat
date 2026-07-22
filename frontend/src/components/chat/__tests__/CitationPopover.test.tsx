import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { CitationPopover } from "../CitationPopover";

describe("CitationPopover", () => {
  it("renders a citation badge with the index number", () => {
    render(
      <CitationPopover
        index={1}
        documentName="doc.pdf"
        page={3}
        textPreview="Texto relevante"
      />,
    );

    expect(screen.getByText("[1]")).toBeInTheDocument();
  });

  it("shows document info in popover on click", async () => {
    const user = userEvent.setup();

    render(
      <CitationPopover
        index={2}
        documentName="informe.pdf"
        page={5}
        textPreview="Este es el texto relevante del documento."
      />,
    );

    // Click the badge to open popover
    const badge = screen.getByText("[2]");
    await user.click(badge);

    // Should now show document info
    expect(screen.getByText("informe.pdf")).toBeInTheDocument();
    expect(screen.getByText(/Página 5/)).toBeInTheDocument();
  });

  it("shows text preview in popover", async () => {
    const user = userEvent.setup();

    render(
      <CitationPopover
        index={3}
        documentName="doc.pdf"
        page={1}
        textPreview="Texto de ejemplo para la citación."
      />,
    );

    await user.click(screen.getByText("[3]"));

    expect(screen.getByText("Texto de ejemplo para la citación.")).toBeInTheDocument();
  });
});

import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import NotFoundPage from "../NotFoundPage";

function renderWithRouter() {
  return render(
    <BrowserRouter>
      <NotFoundPage />
    </BrowserRouter>,
  );
}

describe("NotFoundPage", () => {
  it("renders 404 title", () => {
    renderWithRouter();
    expect(screen.getByText("Página no encontrada")).toBeInTheDocument();
  });

  it("has a link back to home", () => {
    renderWithRouter();
    const link = screen.getByText("Volver al inicio");
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "/");
  });
});

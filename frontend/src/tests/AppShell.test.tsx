import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { AppShell } from "../components/layout/AppShell";

describe("AppShell", () => {
  it("renders navigation links", () => {
    render(
      <MemoryRouter initialEntries={["/app/chat"]}>
        <Routes>
          <Route path="/app" element={<AppShell />}>
            <Route path="chat" element={<div>Chat content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText("Chat")).toBeInTheDocument();
    expect(screen.getByText("Outfits")).toBeInTheDocument();
    expect(screen.getByText("Wardrobe")).toBeInTheDocument();
    expect(screen.getByText("Reviewer")).toBeInTheDocument();
  });

  it("opens the mobile navigation menu", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/app/chat"]}>
        <Routes>
          <Route path="/app" element={<AppShell />}>
            <Route path="chat" element={<div>Chat content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    );

    await user.click(screen.getByLabelText(/open menu/i));

    expect(await screen.findByText("Menu")).toBeInTheDocument();
  });
});

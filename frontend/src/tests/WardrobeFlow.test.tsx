import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it } from "vitest";
import type { ReactNode } from "react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { server } from "../mocks/server";
import WardrobeListPage from "../pages/WardrobeListPage";
import WardrobeItemEditPage from "../pages/WardrobeItemEditPage";
import { ToastContextProvider } from "../components/ui/use-toast";
import { Toaster } from "../components/ui/toaster";

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ToastContextProvider>
        {children}
        <Toaster />
      </ToastContextProvider>
    </QueryClientProvider>
  );
};

describe("Wardrobe flows", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("renders wardrobe items and filters by category", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <WardrobeListPage />
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(await screen.findByText("Navy Trench")).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText(/category/i), "top");

    expect(screen.getByText("White Tee")).toBeInTheDocument();
    expect(screen.queryByText("Navy Trench")).not.toBeInTheDocument();
  });

  it("creates a wardrobe item, shows a toast, and returns to the list", async () => {
    const user = userEvent.setup();
    const items: Array<Record<string, unknown>> = [];

    server.use(
      http.get("/wardrobe", () => HttpResponse.json({ items })),
      http.post("/wardrobe", async ({ request }) => {
        const body = (await request.json()) as Record<string, unknown>;
        const item = { id: "wardrobe-99", ...body };
        items.push(item);
        return HttpResponse.json(item);
      })
    );

    render(
      <MemoryRouter initialEntries={["/app/wardrobe/new"]}>
        <Routes>
          <Route path="/app/wardrobe" element={<WardrobeListPage />} />
          <Route path="/app/wardrobe/new" element={<WardrobeItemEditPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    await user.type(screen.getByLabelText(/name/i), "Test Blazer");
    await user.type(screen.getByLabelText(/category/i), "outerwear");
    await user.type(screen.getByLabelText(/color/i), "black");
    await user.type(screen.getByLabelText(/season tags/i), "cold_weather");
    await user.type(screen.getByLabelText(/style tags/i), "business");
    await user.type(screen.getByLabelText(/image url/i), "https://example.com/blazer.png");

    await user.click(screen.getByRole("button", { name: /save item/i }));

    expect(await screen.findByText(/wardrobe item created/i)).toBeInTheDocument();
    expect(await screen.findByText("Test Blazer")).toBeInTheDocument();
  });
});

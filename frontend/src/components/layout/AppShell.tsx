import { Outlet, NavLink } from "react-router-dom";
import { Menu } from "lucide-react";
import { Button } from "../ui/button";
import { Sheet, SheetContent, SheetTrigger } from "../ui/sheet";
import { cn } from "../../lib/utils";

const navItems = [
  { label: "Chat", to: "/app/chat" },
  { label: "Outfits", to: "/app/outfits" },
  { label: "Wardrobe", to: "/app/wardrobe" },
  { label: "Settings", to: "/app/settings" }
];

export const AppShell = () => {
  return (
    <div className="flex min-h-screen flex-col bg-muted/20">
      <header className="border-b bg-white">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-4 md:px-6">
          <div className="flex items-center gap-3">
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" className="md:hidden" aria-label="Open menu">
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-64 p-0">
                <nav className="flex h-full flex-col gap-2 p-6">
                  <span className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                    Menu
                  </span>
                  {navItems.map((item) => (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      className={({ isActive }) =>
                        cn(
                          "rounded-lg px-3 py-2 text-sm font-medium transition",
                          isActive
                            ? "bg-primary text-primary-foreground"
                            : "text-muted-foreground hover:bg-muted"
                        )
                      }
                    >
                      {item.label}
                    </NavLink>
                  ))}
                </nav>
              </SheetContent>
            </Sheet>
            <div>
              <p className="text-lg font-semibold">Fashion Concierge</p>
              <p className="text-xs text-muted-foreground">Phase 1 Foundation</p>
            </div>
          </div>
          <div className="hidden items-center gap-4 md:flex">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "rounded-full px-4 py-2 text-sm font-medium transition",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-muted"
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </div>
        </div>
      </header>
      <main className="flex-1">
        <div className="mx-auto w-full max-w-6xl px-4 py-6 md:px-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

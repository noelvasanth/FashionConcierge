import { Link } from "react-router-dom";
import { Button } from "../components/ui/button";

const LandingPage = () => {
  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-white to-muted/30">
      <header className="mx-auto w-full max-w-6xl px-4 py-6 md:px-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-lg font-semibold">Fashion Concierge</p>
            <p className="text-sm text-muted-foreground">AI-styled outfits with your wardrobe</p>
          </div>
          <Link to="/app">
            <Button>Enter App</Button>
          </Link>
        </div>
      </header>
      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-8 px-4 py-10 md:flex-row md:items-center md:px-6">
        <section className="flex-1 space-y-4">
          <h1 className="text-4xl font-semibold tracking-tight md:text-5xl">
            Plan outfits around your day, mood, and weather.
          </h1>
          <p className="text-lg text-muted-foreground">
            This MVP pairs your wardrobe with calendar events and forecast data to suggest ready-to-wear
            looks.
          </p>
          <div className="flex flex-wrap gap-3">
            <Button variant="default">View demo</Button>
            <Button variant="outline">Connect wardrobe</Button>
          </div>
        </section>
        <section className="flex-1">
          <div className="rounded-3xl border bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold">Phase 1 Focus</h2>
            <ul className="mt-4 space-y-3 text-sm text-muted-foreground">
              <li>• Multi-agent recommendations grounded in your closet.</li>
              <li>• Weather + schedule aware outfit planning.</li>
              <li>• Structured collage-ready output for the frontend.</li>
            </ul>
          </div>
        </section>
      </main>
    </div>
  );
};

export default LandingPage;

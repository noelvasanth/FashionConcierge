import { Button } from "../components/ui/button";
import { Link } from "react-router-dom";

const AppHomePage = () => {
  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <p className="text-sm font-semibold uppercase text-muted-foreground">Dashboard</p>
        <h1 className="text-2xl font-semibold">Welcome back</h1>
        <p className="text-muted-foreground">
          Start with a chat prompt or review today&apos;s outfit recs once the backend is connected.
        </p>
      </header>
      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl border bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold">Today&apos;s focus</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Sync your calendar and weather feed to unlock tailored recommendations.
          </p>
          <Button asChild className="mt-4">
            <Link to="/app/planner">Connect data sources</Link>
          </Button>
        </div>
        <div className="rounded-2xl border bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold">Wardrobe snapshot</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Upload or import items to see personalized outfit boards.
          </p>
          <Button variant="outline" className="mt-4">
            Add wardrobe items
          </Button>
        </div>
      </div>
    </div>
  );
};

export default AppHomePage;

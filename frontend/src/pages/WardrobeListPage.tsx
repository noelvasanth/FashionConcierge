import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "../components/ui/button";
import { useWardrobeList } from "../lib/api/hooks";

const WardrobeListPage = () => {
  const { data, isLoading } = useWardrobeList();
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");

  const categories = useMemo(() => {
    const items = data?.items ?? [];
    return Array.from(new Set(items.map((item) => item.category))).sort();
  }, [data?.items]);

  const filteredItems = useMemo(() => {
    const items = data?.items ?? [];
    return items.filter((item) => {
      const matchesSearch = item.name.toLowerCase().includes(search.toLowerCase());
      const matchesCategory = category === "all" ? true : item.category === category;
      return matchesSearch && matchesCategory;
    });
  }, [category, data?.items, search]);

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Wardrobe</h1>
          <p className="text-sm text-muted-foreground">Track and refine your saved wardrobe items.</p>
        </div>
        <Button asChild>
          <Link to="/app/wardrobe/new">Add item</Link>
        </Button>
      </header>

      <div className="grid gap-4 rounded-2xl border bg-white p-4 shadow-sm md:grid-cols-3">
        <div className="md:col-span-2">
          <label className="text-sm font-medium" htmlFor="search">
            Search
          </label>
          <input
            id="search"
            className="mt-2 w-full rounded-lg border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder="Search by name"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>
        <div>
          <label className="text-sm font-medium" htmlFor="category">
            Category
          </label>
          <select
            id="category"
            className="mt-2 w-full rounded-lg border border-input bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            value={category}
            onChange={(event) => setCategory(event.target.value)}
          >
            <option value="all">All</option>
            {categories.map((entry) => (
              <option key={entry} value={entry}>
                {entry}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {isLoading && <p className="text-sm text-muted-foreground">Loading wardrobe...</p>}
        {!isLoading && filteredItems.length === 0 && (
          <div className="rounded-2xl border border-dashed bg-white p-6 text-sm text-muted-foreground">
            No wardrobe items yet. Add your first piece to start building outfits.
          </div>
        )}
        {filteredItems.map((item) => (
          <Link
            key={item.id}
            to={`/app/wardrobe/${item.id}`}
            className="rounded-2xl border bg-white p-4 shadow-sm transition hover:shadow-md"
          >
            <div className="aspect-square w-full rounded-xl bg-muted">
              {item.imageUrl && (
                <img
                  src={item.imageUrl}
                  alt={item.name}
                  className="h-full w-full rounded-xl object-cover"
                />
              )}
            </div>
            <div className="mt-3 space-y-1">
              <h2 className="text-base font-semibold">{item.name}</h2>
              <p className="text-sm text-muted-foreground">{item.category}</p>
              {item.color && <p className="text-xs text-muted-foreground">Color: {item.color}</p>}
              {item.tags && item.tags.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground">
                  {item.tags.map((tag) => (
                    <span key={tag} className="rounded-full bg-muted px-3 py-1">
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default WardrobeListPage;

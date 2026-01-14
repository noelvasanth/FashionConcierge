import { useWardrobe } from "../lib/api/hooks";

const WardrobePage = () => {
  const { data, isLoading } = useWardrobe();

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Wardrobe</h1>
        <p className="text-sm text-muted-foreground">A snapshot of stored wardrobe items.</p>
      </header>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {isLoading && <p className="text-sm text-muted-foreground">Loading wardrobe...</p>}
        {data?.items.map((item) => (
          <div key={item.itemId} className="rounded-2xl border bg-white p-4 shadow-sm">
            <div className="aspect-square w-full rounded-xl bg-muted" />
            <div className="mt-3">
              <h2 className="text-base font-semibold">{item.brand}</h2>
              <p className="text-sm text-muted-foreground">{item.category}</p>
              <p className="text-xs text-muted-foreground">{item.colors.join(", ")}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default WardrobePage;

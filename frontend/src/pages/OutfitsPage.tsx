import { useOutfits } from "../lib/api/hooks";

const OutfitsPage = () => {
  const { data, isLoading } = useOutfits();

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Outfits</h1>
        <p className="text-sm text-muted-foreground">Review curated outfit options.</p>
      </header>
      <div className="grid gap-4 md:grid-cols-2">
        {isLoading && <p className="text-sm text-muted-foreground">Loading recommendations...</p>}
        {data?.outfits.map((outfit) => (
          <div key={outfit.outfitId} className="rounded-2xl border bg-white p-4 shadow-sm">
            <h2 className="text-lg font-semibold">{outfit.name}</h2>
            <p className="mt-2 text-sm text-muted-foreground">{outfit.rationale}</p>
            <div className="mt-4 flex flex-wrap gap-2 text-xs text-muted-foreground">
              {outfit.itemIds.map((itemId) => (
                <span key={itemId} className="rounded-full bg-muted px-3 py-1">
                  {itemId}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default OutfitsPage;

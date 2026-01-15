import { useEffect, useMemo } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Button } from "../components/ui/button";
import { useToast } from "../components/ui/use-toast";
import {
  useWardrobeCreate,
  useWardrobeDelete,
  useWardrobeList,
  useWardrobeUpdate
} from "../lib/api/hooks";
import { formatErrorMessage, trackEvent } from "../lib/telemetry/telemetry";

const wardrobeSchema = z.object({
  name: z.string().min(1, "Name is required"),
  category: z.string().min(1, "Category is required"),
  color: z.string().optional(),
  season: z.string().optional(),
  imageUrl: z.string().url("Enter a valid URL").optional().or(z.literal("")),
  tags: z.string().optional()
});

type WardrobeFormValues = z.infer<typeof wardrobeSchema>;

const parseList = (value?: string) => {
  if (!value) {
    return undefined;
  }
  const parts = value
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean);
  return parts.length > 0 ? parts : undefined;
};

const WardrobeItemEditPage = () => {
  const { id } = useParams<{ id: string }>();
  const isNew = id === undefined;
  const navigate = useNavigate();
  const { toast } = useToast();
  const { data, isLoading } = useWardrobeList();
  const item = useMemo(() => data?.items.find((entry) => entry.id === id), [data?.items, id]);

  const createWardrobe = useWardrobeCreate();
  const updateWardrobe = useWardrobeUpdate();
  const deleteWardrobe = useWardrobeDelete();

  const form = useForm<WardrobeFormValues>({
    resolver: zodResolver(wardrobeSchema),
    defaultValues: {
      name: "",
      category: "",
      color: "",
      season: "",
      imageUrl: "",
      tags: ""
    }
  });

  useEffect(() => {
    if (item) {
      form.reset({
        name: item.name,
        category: item.category,
        color: item.color ?? "",
        season: item.season?.join(", ") ?? "",
        imageUrl: item.imageUrl ?? "",
        tags: item.tags?.join(", ") ?? ""
      });
    }
  }, [form, item]);

  const handleSubmit = async (values: WardrobeFormValues) => {
    try {
      const payload = {
        name: values.name,
        category: values.category,
        color: values.color?.trim() || undefined,
        season: parseList(values.season),
        imageUrl: values.imageUrl?.trim() || undefined,
        tags: parseList(values.tags)
      };

      if (isNew) {
        const created = await createWardrobe.mutateAsync(payload);
        toast({
          title: "Wardrobe item created",
          description: `${created.name} is ready to style.`
        });
        trackEvent("wardrobe.create.ui", { id: created.id });
        navigate("/app/wardrobe");
      } else if (item) {
        const updated = await updateWardrobe.mutateAsync({ id: item.id, ...payload });
        toast({
          title: "Wardrobe item updated",
          description: `${updated.name} has been updated.`
        });
        trackEvent("wardrobe.update.ui", { id: updated.id });
      }
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Unable to save wardrobe item",
        description: formatErrorMessage(error)
      });
    }
  };

  const handleDelete = async () => {
    if (!item) {
      return;
    }
    const confirmed = window.confirm(`Delete ${item.name}? This cannot be undone.`);
    if (!confirmed) {
      return;
    }
    try {
      await deleteWardrobe.mutateAsync(item.id);
      toast({
        title: "Wardrobe item deleted",
        description: `${item.name} was removed.`
      });
      trackEvent("wardrobe.delete.ui", { id: item.id });
      navigate("/app/wardrobe");
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Unable to delete item",
        description: formatErrorMessage(error)
      });
    }
  };

  if (!isNew && isLoading) {
    return <p className="text-sm text-muted-foreground">Loading wardrobe item...</p>;
  }

  if (!isNew && !item) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">Wardrobe item not found</h1>
        <Button asChild>
          <Link to="/app/wardrobe">Back to wardrobe</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">{isNew ? "Add wardrobe item" : "Edit item"}</h1>
          <p className="text-sm text-muted-foreground">
            Capture the essentials so the stylist can recommend with confidence.
          </p>
        </div>
        <Button variant="ghost" asChild>
          <Link to="/app/wardrobe">Back to wardrobe</Link>
        </Button>
      </header>

      <form
        className="space-y-4 rounded-2xl border bg-white p-6 shadow-sm"
        onSubmit={form.handleSubmit(handleSubmit)}
      >
        <div>
          <label className="text-sm font-medium" htmlFor="name">
            Name
          </label>
          <input
            id="name"
            className="mt-2 w-full rounded-lg border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            {...form.register("name")}
          />
          {form.formState.errors.name && (
            <p className="mt-1 text-xs text-destructive">{form.formState.errors.name.message}</p>
          )}
        </div>
        <div>
          <label className="text-sm font-medium" htmlFor="category">
            Category
          </label>
          <input
            id="category"
            className="mt-2 w-full rounded-lg border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            {...form.register("category")}
          />
          {form.formState.errors.category && (
            <p className="mt-1 text-xs text-destructive">{form.formState.errors.category.message}</p>
          )}
        </div>
        <div>
          <label className="text-sm font-medium" htmlFor="color">
            Color
          </label>
          <input
            id="color"
            className="mt-2 w-full rounded-lg border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder="Navy, camel, white"
            {...form.register("color")}
          />
        </div>
        <div>
          <label className="text-sm font-medium" htmlFor="season">
            Season tags
          </label>
          <input
            id="season"
            className="mt-2 w-full rounded-lg border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder="warm_weather, cold_weather"
            {...form.register("season")}
          />
        </div>
        <div>
          <label className="text-sm font-medium" htmlFor="tags">
            Style tags
          </label>
          <input
            id="tags"
            className="mt-2 w-full rounded-lg border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder="casual, business"
            {...form.register("tags")}
          />
        </div>
        <div>
          <label className="text-sm font-medium" htmlFor="imageUrl">
            Image URL
          </label>
          <input
            id="imageUrl"
            className="mt-2 w-full rounded-lg border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder="https://..."
            {...form.register("imageUrl")}
          />
          {form.formState.errors.imageUrl && (
            <p className="mt-1 text-xs text-destructive">
              {form.formState.errors.imageUrl.message}
            </p>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button type="submit" disabled={form.formState.isSubmitting}>
            {form.formState.isSubmitting ? "Saving..." : "Save item"}
          </Button>
          {!isNew && (
            <Button type="button" variant="destructive" onClick={handleDelete}>
              Delete item
            </Button>
          )}
        </div>
      </form>
    </div>
  );
};

export default WardrobeItemEditPage;

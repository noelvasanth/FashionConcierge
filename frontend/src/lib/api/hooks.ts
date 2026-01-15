import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "./apiClient";
import {
  ChatRequest,
  ChatResponseSchema,
  OrchestrateContextResponseSchema,
  OrchestrateOutfitResponseSchema,
  OrchestrateRequest,
  OutfitRecommendationResponseSchema,
  SessionResponseSchema,
  WardrobeListResponseSchema,
  WardrobeMutationResponseSchema,
  FeedbackListResponseSchema,
  FeedbackSchema,
  type FeedbackRecord,
  type WardrobeItem
} from "../contracts";
import { setSession } from "../session/session";
import { trackEvent } from "../telemetry/telemetry";

const CHAT_ENDPOINT = import.meta.env.VITE_CHAT_ENDPOINT ?? "/chat";

export const useChatSend = () => {
  return useMutation({
    mutationFn: (payload: ChatRequest) =>
      apiFetch(CHAT_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        schema: ChatResponseSchema
      }),
    onSuccess: () => {
      trackEvent("chat.send.success", { endpoint: CHAT_ENDPOINT });
    }
  });
};

export const useOutfits = () => {
  return useQuery({
    queryKey: ["outfits"],
    queryFn: () =>
      apiFetch("/outfits", {
        schema: OutfitRecommendationResponseSchema
      })
  });
};

export const useWardrobeList = () => {
  return useQuery({
    queryKey: ["wardrobe"],
    queryFn: () =>
      apiFetch("/wardrobe", {
        schema: WardrobeListResponseSchema
      })
  });
};

export const useWardrobeCreate = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Omit<WardrobeItem, "id">) =>
      apiFetch("/wardrobe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        schema: WardrobeMutationResponseSchema
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(["wardrobe"], (prev?: { items: WardrobeItem[] }) => ({
        items: prev ? [...prev.items, data] : [data]
      }));
      trackEvent("wardrobe.create.success", { id: data.id });
    }
  });
};

export const useWardrobeUpdate = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...payload }: WardrobeItem) =>
      apiFetch(`/wardrobe/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        schema: WardrobeMutationResponseSchema
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(["wardrobe"], (prev?: { items: WardrobeItem[] }) => ({
        items: prev ? prev.items.map((item) => (item.id === data.id ? data : item)) : [data]
      }));
      trackEvent("wardrobe.update.success", { id: data.id });
    }
  });
};

export const useWardrobeDelete = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/wardrobe/${id}`, {
        method: "DELETE"
      }),
    onSuccess: (_, id) => {
      queryClient.setQueryData(["wardrobe"], (prev?: { items: WardrobeItem[] }) => ({
        items: prev ? prev.items.filter((item) => item.id !== id) : []
      }));
      trackEvent("wardrobe.delete.success", { id });
    }
  });
};

export const useCreateSession = () => {
  return useMutation({
    mutationFn: (payload: { userId: string }) =>
      apiFetch("/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        schema: SessionResponseSchema
      }),
    onSuccess: (data, variables) => {
      setSession({ sessionId: data.sessionId, userId: variables.userId });
      trackEvent("session.create.success", { sessionId: data.sessionId });
    }
  });
};

export const useOrchestrateOutfit = () => {
  return useMutation({
    mutationFn: (payload: OrchestrateRequest) =>
      apiFetch("/orchestrate/outfit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        schema: OrchestrateOutfitResponseSchema
      })
  });
};

export const useOrchestrateContext = () => {
  return useMutation({
    mutationFn: (payload: OrchestrateRequest) =>
      apiFetch("/orchestrate/context", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        schema: OrchestrateContextResponseSchema
      })
  });
};

export const useFeedbackCreate = () => {
  return useMutation({
    mutationFn: (payload: Omit<FeedbackRecord, "id">) =>
      apiFetch("/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        schema: FeedbackSchema
      }),
    onSuccess: (data) => {
      trackEvent("feedback.submit.success", { id: data.id, rating: data.rating });
    }
  });
};

export const useFeedbackList = () => {
  return useQuery({
    queryKey: ["feedback"],
    queryFn: () =>
      apiFetch("/feedback", {
        schema: FeedbackListResponseSchema
      })
  });
};

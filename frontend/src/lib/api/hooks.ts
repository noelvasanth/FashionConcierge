import { useMutation, useQuery } from "@tanstack/react-query";
import { apiFetch } from "./apiClient";
import {
  ChatRequest,
  ChatResponseSchema,
  OrchestrateContextResponseSchema,
  OrchestrateOutfitResponseSchema,
  OrchestrateRequest,
  OutfitRecommendationResponseSchema,
  SessionResponseSchema,
  WardrobeResponseSchema
} from "../contracts";

export const useChat = () => {
  return useMutation({
    mutationFn: (payload: ChatRequest) =>
      apiFetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        schema: ChatResponseSchema
      })
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

export const useWardrobe = () => {
  return useQuery({
    queryKey: ["wardrobe"],
    queryFn: () =>
      apiFetch("/wardrobe", {
        schema: WardrobeResponseSchema
      })
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
    onSuccess: (data) => {
      localStorage.setItem("sessionId", data.sessionId);
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

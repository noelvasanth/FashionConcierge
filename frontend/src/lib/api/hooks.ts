import { useMutation, useQuery } from "@tanstack/react-query";
import { apiFetch } from "./apiClient";
import {
  ChatRequest,
  ChatResponseSchema,
  OutfitRecommendationResponseSchema,
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

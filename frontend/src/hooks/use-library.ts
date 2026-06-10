"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { Note } from "@/types";

export function useLibrary(deviceId: string) {
  const queryClient = useQueryClient();

  const notes = useQuery({
    queryKey: ["library", deviceId],
    queryFn: () => apiClient.get<Note[]>(`/api/library?deviceId=${deviceId}`),
  });

  const create = useMutation({
    mutationFn: (data: Omit<Note, "id" | "createdAt" | "updatedAt">) =>
      apiClient.post<Note>("/api/library", data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["library"] }),
  });

  const update = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Note> }) =>
      apiClient.put<Note>(`/api/library/${id}`, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["library"] }),
  });

  const remove = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/library/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["library"] }),
  });

  const search = useMutation({
    mutationFn: ({ deviceId: dId, q }: { deviceId: string; q: string }) =>
      apiClient.get<Note[]>(`/api/library/search?q=${encodeURIComponent(q)}&deviceId=${dId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["library"] }),
  });

  return { notes, create, update, remove, search };
}

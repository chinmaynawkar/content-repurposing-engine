import axios from "axios";
import type { Content, ImageGenerateResponse } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

export const contentApi = {
  uploadContent: async (data: {
    original_text: string;
    title?: string;
    source_url?: string;
  }) => {
    const { data: res } = await api.post<Content>("/api/content/", data);
    return res;
  },
  getContents: async (skip = 0, limit = 10) => {
    const { data } = await api.get<Content[]>("/api/content/", {
      params: { skip, limit },
    });
    return data;
  },
  getContent: async (id: number) => {
    const { data } = await api.get<Content>(`/api/content/${id}`);
    return data;
  },
};

export async function generateImage(
  contentId: number,
  payload: { style: string; type: "cover" | "instagram" }
): Promise<ImageGenerateResponse> {
  const { data } = await api.post<ImageGenerateResponse>(
    `/api/generate/image/${contentId}`,
    payload
  );
  return data;
}

export default api;

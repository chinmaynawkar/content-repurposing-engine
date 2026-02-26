export interface Content {
  id: number;
  original_text: string;
  title?: string;
  word_count: number;
  source_url?: string;
  created_at: string;
}

export interface UploadContentData {
  original_text: string;
  title?: string;
  source_url?: string;
}

export type ImageType = "image_cover" | "image_instagram";

export interface GeneratedImage {
  id: number;
  type: ImageType;
  image_url: string;
  width: number;
  height: number;
  style: string;
  prompt: string;
}

export interface ImageGenerateResponse {
  content_id: number;
  image: GeneratedImage;
}

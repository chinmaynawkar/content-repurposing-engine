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

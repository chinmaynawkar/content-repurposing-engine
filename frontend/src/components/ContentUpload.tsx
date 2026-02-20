import { useState } from "react";
import { contentApi } from "../services/api";
import type { Content, UploadContentData } from "../types";

interface ContentUploadProps {
  readonly onUploadSuccess: (content: Content) => void;
}

export default function ContentUpload({ onUploadSuccess }: ContentUploadProps) {
  const [formData, setFormData] = useState<UploadContentData>({
    original_text: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleChange = (
    e: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!formData.original_text.trim()) {
      setError("Content text is required");
      return;
    }
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const result = await contentApi.uploadContent(formData);
      setSuccess(
        `Content uploaded. ID: ${result.id}, Words: ${result.word_count}`
      );
      onUploadSuccess(result);
      setFormData({ original_text: "" });
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response
              ?.data?.detail
          : null;
      setError(msg ? String(msg) : "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  const wordCount = formData.original_text.trim()
    ? formData.original_text.trim().split(/\s+/).length
    : 0;

  return (
    <div className="upload-container">
      <h2>Upload Content</h2>
      <form onSubmit={handleSubmit} className="upload-form">
        <div className="form-group">
          <label htmlFor="title">Title (optional)</label>
          <input
            id="title"
            name="title"
            value={formData.title ?? ""}
            onChange={handleChange}
            className="form-input"
            maxLength={255}
            placeholder="Enter content title..."
          />
        </div>
        <div className="form-group">
          <label htmlFor="source_url">Source URL (optional)</label>
          <input
            id="source_url"
            name="source_url"
            value={formData.source_url ?? ""}
            onChange={handleChange}
            className="form-input"
            type="url"
            placeholder="https://your-blog.com/post"
          />
        </div>
        <div className="form-group">
          <label htmlFor="original_text">Content * (max 10,000 chars)</label>
          <textarea
            id="original_text"
            name="original_text"
            value={formData.original_text}
            onChange={handleChange}
            rows={10}
            maxLength={10000}
            className="form-textarea"
            placeholder="Paste your blog post, video transcript, or article here..."
          />
          <div className="word-count">
            {wordCount} words · {formData.original_text.length}/10,000 chars
          </div>
        </div>
        {error && <div className="error">{error}</div>}
        {success && <div className="success">{success}</div>}
        <button
          type="submit"
          disabled={loading || !formData.original_text.trim()}
          className="upload-button"
        >
          {loading ? "Uploading…" : "Upload & Analyze"}
        </button>
      </form>
    </div>
  );
}

import { useState } from "react";
import { contentApi } from "../services/api";
import type { Content, UploadContentData } from "../types";

interface ContentUploadProps {
  readonly onUploadSuccess?: (content: Content) => void;
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
      onUploadSuccess?.(result);
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
    <div className="form-card bg-gray-900 rounded-lg shadow-card border border-gray-800 p-4 sm:p-6 md:p-8">
      <h2 className="text-xl font-semibold text-white mb-4 sm:mb-6 border-b border-gray-700 pb-2">
        Upload Content
      </h2>
      <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-5">
        <div className="min-w-0">
          <label
            htmlFor="title"
            className="block text-sm font-medium text-gray-300 mb-1"
          >
            Title (optional)
          </label>
          <input
            id="title"
            name="title"
            value={formData.title ?? ""}
            onChange={handleChange}
            className="input-field min-h-[44px] px-3 py-2 rounded-md bg-gray-800 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-accent-primary focus:ring-1 focus:ring-accent-primary"
            maxLength={255}
            placeholder="Enter content title..."
          />
        </div>
        <div className="min-w-0">
          <label
            htmlFor="source_url"
            className="block text-sm font-medium text-gray-300 mb-1"
          >
            Source URL (optional)
          </label>
          <input
            id="source_url"
            name="source_url"
            value={formData.source_url ?? ""}
            onChange={handleChange}
            className="input-field min-h-[44px] px-3 py-2 rounded-md bg-gray-800 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-accent-primary focus:ring-1 focus:ring-accent-primary"
            type="url"
            placeholder="https://your-blog.com/post"
          />
        </div>
        <div className="min-w-0">
          <label
            htmlFor="original_text"
            className="block text-sm font-medium text-gray-300 mb-1"
          >
            Content * (max 10,000 chars)
          </label>
          <textarea
            id="original_text"
            name="original_text"
            value={formData.original_text}
            onChange={handleChange}
            rows={10}
            maxLength={10000}
            className="input-field px-3 py-2 rounded-md bg-gray-800 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-accent-primary focus:ring-1 focus:ring-accent-primary resize-y min-h-[200px]"
            placeholder="Paste your blog post, video transcript, or article here..."
          />
          <p className="text-gray-500 text-sm mt-1">
            {wordCount} words · {formData.original_text.length}/10,000 chars
          </p>
        </div>
        {error && (
          <div className="p-3 rounded-md bg-danger/10 border border-danger/30 text-danger text-sm">
            {error}
          </div>
        )}
        {success && (
          <div className="p-3 rounded-md bg-success/10 border border-success/30 text-success text-sm">
            {success}
          </div>
        )}
        <button
          type="submit"
          disabled={loading || !formData.original_text.trim()}
          className="w-full min-h-[48px] rounded-md font-medium bg-accent-primary text-black hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors py-3"
        >
          {loading ? "Uploading…" : "Upload & Analyze"}
        </button>
      </form>
    </div>
  );
}

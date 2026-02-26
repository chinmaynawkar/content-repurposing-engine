import { useState } from "react";
import { generateImage } from "../services/api";
import type { Content, GeneratedImage } from "../types";

const STYLE_OPTIONS = [
  { value: "minimal_gradient", label: "Minimal gradient" },
  { value: "photo_realistic", label: "Photo realistic" },
  { value: "tech_dark", label: "Tech dark" },
  { value: "pastel_illustration", label: "Pastel illustration" },
] as const;

const TYPE_OPTIONS = [
  { value: "cover" as const, label: "Cover (1200×630)" },
  { value: "instagram" as const, label: "Instagram (1080×1080)" },
];

interface ImageGeneratorProps {
  readonly selectedContent: Content | null;
}

export default function ImageGenerator({ selectedContent }: ImageGeneratorProps) {
  const [style, setStyle] = useState<string>("minimal_gradient");
  const [type, setType] = useState<"cover" | "instagram">("cover");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [image, setImage] = useState<GeneratedImage | null>(null);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!selectedContent) return;
    setLoading(true);
    setError(null);
    setImage(null);
    try {
      const res = await generateImage(selectedContent.id, { style, type });
      setImage(res.image);
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response
              ?.data?.detail
          : null;
      setError(msg ? String(msg) : "Failed to generate image");
    } finally {
      setLoading(false);
    }
  };

  const handleCopyUrl = () => {
    if (!image?.image_url) return;
    navigator.clipboard.writeText(image.image_url);
  };

  const handleOpenInNewTab = () => {
    if (!image?.image_url) return;
    window.open(image.image_url, "_blank", "noopener,noreferrer");
  };

  if (!selectedContent) {
    return (
      <div className="upload-container">
        <h2>AI Images</h2>
        <p className="image-generator-placeholder">
          Select a content item below to generate an image.
        </p>
      </div>
    );
  }

  return (
    <div className="upload-container">
      <h2>AI Images</h2>
      <p className="image-generator-selected">
        Using: {selectedContent.title || "Untitled"} (ID: {selectedContent.id})
      </p>
      <form onSubmit={handleSubmit} className="upload-form">
        <div className="form-group">
          <label htmlFor="image-style">Style</label>
          <select
            id="image-style"
            value={style}
            onChange={(e) => setStyle(e.target.value)}
            className="form-input"
          >
            {STYLE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label htmlFor="image-type">Format</label>
          <select
            id="image-type"
            value={type}
            onChange={(e) => setType(e.target.value as "cover" | "instagram")}
            className="form-input"
          >
            {TYPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        {error && <div className="error">{error}</div>}
        <button
          type="submit"
          disabled={loading}
          className="upload-button"
        >
          {loading ? "Generating…" : "Generate image"}
        </button>
      </form>

      {image && (
        <div className="image-generator-result">
          <h3>Generated image</h3>
          <img
            src={image.image_url}
            alt={`Generated ${image.style} (${image.width}×${image.height})`}
            className="image-preview"
          />
          <p className="image-meta">
            {image.style} · {image.width}×{image.height}
          </p>
          <div className="image-actions">
            <button
              type="button"
              onClick={handleCopyUrl}
              className="image-action-button"
            >
              Copy image URL
            </button>
            <button
              type="button"
              onClick={handleOpenInNewTab}
              className="image-action-button"
            >
              Open in new tab
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

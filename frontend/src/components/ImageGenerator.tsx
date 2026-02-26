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
      <div className="bg-gray-900 rounded-lg border border-gray-800 p-4 sm:p-6">
        <h2 className="text-lg font-semibold text-white mb-2">AI Images</h2>
        <p className="text-gray-400">Select a content item to generate an image.</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 rounded-lg shadow-card border border-gray-800 p-4 sm:p-6">
      <h2 className="text-lg font-semibold text-white mb-2">AI Images</h2>
      <p className="text-gray-400 text-sm mb-4">
        Using: {selectedContent.title || "Untitled"} (ID: {selectedContent.id})
      </p>
      <form onSubmit={handleSubmit} className="space-y-4 mb-6">
        <div>
          <label htmlFor="image-style" className="block text-sm font-medium text-gray-300 mb-1">
            Style
          </label>
          <select
            id="image-style"
            value={style}
            onChange={(e) => setStyle(e.target.value)}
            className="w-full min-h-[44px] px-3 py-2 rounded-md bg-gray-800 border border-gray-700 text-white focus:outline-none focus:border-accent-primary"
          >
            {STYLE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="image-type" className="block text-sm font-medium text-gray-300 mb-1">
            Format
          </label>
          <select
            id="image-type"
            value={type}
            onChange={(e) => setType(e.target.value as "cover" | "instagram")}
            className="w-full min-h-[44px] px-3 py-2 rounded-md bg-gray-800 border border-gray-700 text-white focus:outline-none focus:border-accent-primary"
          >
            {TYPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        {error && (
          <div className="p-3 rounded-md bg-danger/10 border border-danger/30 text-danger text-sm">
            {error}
          </div>
        )}
        <button
          type="submit"
          disabled={loading}
          className="w-full min-h-[48px] rounded-md font-medium bg-accent-primary text-black hover:bg-accent-hover disabled:opacity-50 py-3"
        >
          {loading ? "Generating…" : "Generate image"}
        </button>
      </form>

      {image && (
        <div className="pt-4 border-t border-gray-800">
          <h3 className="text-white font-medium mb-2">Generated image</h3>
          <img
            src={image.image_url}
            alt={`Generated ${image.style} (${image.width}×${image.height})`}
            className="w-full max-w-md rounded-lg border border-gray-700 block"
          />
          <p className="text-gray-500 text-sm mt-2">
            {image.style} · {image.width}×{image.height}
          </p>
          <div className="flex flex-wrap gap-2 mt-3">
            <button
              type="button"
              onClick={handleCopyUrl}
              className="min-h-[44px] px-4 py-2 rounded-md bg-gray-800 text-white border border-gray-700 hover:bg-gray-700 text-sm"
            >
              Copy image URL
            </button>
            <button
              type="button"
              onClick={handleOpenInNewTab}
              className="min-h-[44px] px-4 py-2 rounded-md bg-gray-800 text-white border border-gray-700 hover:bg-gray-700 text-sm"
            >
              Open in new tab
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

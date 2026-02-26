import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { contentApi } from "../services/api";
import ImageGenerator from "../components/ImageGenerator";
import type { Content } from "../types";

const TABS = [
  { id: "linkedin", label: "LinkedIn" },
  { id: "twitter", label: "Twitter" },
  { id: "instagram", label: "Instagram" },
  { id: "seo", label: "SEO" },
  { id: "images", label: "Images" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function ContentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [content, setContent] = useState<Content | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>("images");

  useEffect(() => {
    const numId = id ? Number.parseInt(id, 10) : Number.NaN;
    if (Number.isNaN(numId)) {
      setError("Invalid content ID");
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const data = await contentApi.getContent(numId);
        if (!cancelled) setContent(data);
      } catch {
        if (!cancelled) setError("Content not found");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) {
    return (
      <div className="w-full">
        <p className="text-gray-400">Loading…</p>
      </div>
    );
  }

  if (error || !content) {
    return (
      <div className="w-full">
        <p className="text-gray-400 mb-4">{error ?? "Content not found"}</p>
        <Link
          to="/library"
          className="text-accent-primary hover:text-accent-hover"
        >
          Back to Library
        </Link>
      </div>
    );
  }

  return (
    <div className="page-full">
      <Link
        to="/library"
        className="inline-block text-gray-400 hover:text-white text-sm mb-4"
      >
        ← Back to Library
      </Link>
      <header className="mb-6 sm:mb-8">
        <h1 className="text-xl sm:text-2xl font-semibold text-white truncate">
          {content.title || "Untitled"}
        </h1>
        <p className="text-gray-500 text-sm mt-1">
          {content.word_count} words
          {content.source_url && (
            <>
              {" · "}
              <a
                href={content.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-accent-primary hover:underline"
              >
                Source
              </a>
            </>
          )}
        </p>
      </header>

      <div className="flex flex-col sm:flex-row gap-2 sm:gap-1 border-b border-gray-800 overflow-x-auto pb-px -mx-1 px-1">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={`min-h-[44px] sm:min-h-0 px-4 py-2.5 sm:py-2 rounded-t-md text-sm font-medium whitespace-nowrap transition-colors ${
              activeTab === tab.id
                ? "bg-gray-800 text-white"
                : "text-gray-400 hover:text-white hover:bg-gray-800/80"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="mt-4 sm:mt-6">
        {activeTab === "linkedin" && (
          <div className="bg-gray-900 rounded-lg border border-gray-800 p-4 sm:p-6">
            <p className="text-gray-400">Generate LinkedIn posts here. (API integration in Phase 4.)</p>
          </div>
        )}
        {activeTab === "twitter" && (
          <div className="bg-gray-900 rounded-lg border border-gray-800 p-4 sm:p-6">
            <p className="text-gray-400">Generate Twitter threads here. (API integration in Phase 4.)</p>
          </div>
        )}
        {activeTab === "instagram" && (
          <div className="bg-gray-900 rounded-lg border border-gray-800 p-4 sm:p-6">
            <p className="text-gray-400">Generate Instagram captions here. (API integration in Phase 4.)</p>
          </div>
        )}
        {activeTab === "seo" && (
          <div className="bg-gray-900 rounded-lg border border-gray-800 p-4 sm:p-6">
            <p className="text-gray-400">Generate SEO meta here. (API integration in Phase 4.)</p>
          </div>
        )}
        {activeTab === "images" && (
          <div className="min-w-0">
            <ImageGenerator selectedContent={content} />
          </div>
        )}
      </div>
    </div>
  );
}

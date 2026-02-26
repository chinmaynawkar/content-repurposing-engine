import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { contentApi } from "../services/api";
import type { Content } from "../types";

const PAGE_SIZE = 10;

export default function LibraryPage() {
  const [contents, setContents] = useState<Content[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [skip, setSkip] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const loadPage = async (offset: number, append: boolean) => {
    if (append) setLoadingMore(true);
    else setLoading(true);
    try {
      const data = await contentApi.getContents(offset, PAGE_SIZE);
      if (append) {
        setContents((prev) => [...prev, ...data]);
      } else {
        setContents(data);
      }
      setHasMore(data.length === PAGE_SIZE);
      setSkip(offset + data.length);
    } catch {
      setHasMore(false);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  useEffect(() => {
    loadPage(0, false);
  }, []);

  const handleLoadMore = () => {
    loadPage(skip, true);
  };

  return (
    <div className="page-full">
      <h1 className="text-2xl sm:text-3xl font-semibold text-white mb-4 sm:mb-6 break-words">
        Your Content Library
      </h1>

      {loading && (
        <p className="text-gray-400">Loading…</p>
      )}

      {!loading && contents.length === 0 && (
        <div className="bg-gray-900 rounded-lg border border-gray-800 p-6 sm:p-8 text-center">
          <p className="text-gray-400 mb-4">No content yet. Upload your first piece.</p>
          <Link
            to="/upload"
            className="inline-flex items-center justify-center rounded-md font-medium bg-accent-primary text-black px-6 py-3 min-h-[48px] hover:bg-accent-hover transition-colors"
          >
            Upload content
          </Link>
        </div>
      )}

      {!loading && contents.length > 0 && (
        <>
          <ul className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 list-none p-0 m-0">
            {contents.map((content) => (
              <li key={content.id}>
                <Link
                  to={`/content/${content.id}`}
                  className="block bg-gray-900 rounded-lg border border-gray-800 p-4 sm:p-5 hover:border-gray-700 hover:shadow-card transition-all text-left min-h-[120px]"
                >
                  <h2 className="text-white font-medium mb-1 truncate">
                    {content.title || "Untitled"}
                  </h2>
                  <p className="text-gray-400 text-sm line-clamp-3 mb-2">
                    {content.original_text.substring(0, 150)}
                    {content.original_text.length > 150 ? "…" : ""}
                  </p>
                  <p className="text-gray-500 text-xs">
                    {content.word_count} words · {new Date(content.created_at).toLocaleDateString()}
                  </p>
                </Link>
              </li>
            ))}
          </ul>
          {hasMore && (
            <div className="mt-6 flex justify-center">
              <button
                type="button"
                onClick={handleLoadMore}
                disabled={loadingMore}
                className="min-h-[48px] px-6 py-3 rounded-md font-medium bg-gray-800 text-white border border-gray-700 hover:bg-gray-700 disabled:opacity-50 transition-colors"
              >
                {loadingMore ? "Loading…" : "Load more"}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

import { useEffect, useState } from "react";
import ContentUpload from "./components/ContentUpload";
import ImageGenerator from "./components/ImageGenerator";
import { contentApi } from "./services/api";
import type { Content } from "./types";
import "./App.css";

function App() {
  const [contents, setContents] = useState<Content[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedContent, setSelectedContent] = useState<Content | null>(null);

  const fetchContents = async () => {
    try {
      setLoading(true);
      const data = await contentApi.getContents(0, 10);
      setContents(data);
    } catch (error) {
      console.error("Failed to fetch contents:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContents();
  }, []);

  const handleUploadSuccess = (newContent: Content) => {
    setContents((prev) => [newContent, ...prev]);
  };

  return (
    <div className="App">
      <header>
        <h1>Content Repurposing Engine</h1>
        <p>Upload once. Generate everywhere. Save hours.</p>
      </header>

      <main>
        <ContentUpload onUploadSuccess={handleUploadSuccess} />

        <div className="content-list">
          <h2>Your Content Library ({contents.length})</h2>

          {loading && <p>Loading...</p>}
          {!loading && contents.length === 0 && (
            <p>No content uploaded yet. Upload your first piece!</p>
          )}
          {!loading && contents.length > 0 &&
            contents.map((content) => (
              <button
                key={content.id}
                type="button"
                className={`content-card ${selectedContent?.id === content.id ? "selected" : ""}`}
                onClick={() =>
                  setSelectedContent((prev) =>
                    prev?.id === content.id ? null : content
                  )
                }
              >
                <h3>{content.title || "Untitled"}</h3>
                <div className="content-preview">
                  {content.original_text.substring(0, 150)}...
                </div>
                <div className="content-meta">
                  <span>{content.word_count} words</span>
                  <span>{new Date(content.created_at).toLocaleDateString()}</span>
                </div>
                {selectedContent?.id === content.id && (
                  <p className="content-card-hint">Selected for AI image. Click again to deselect.</p>
                )}
              </button>
            ))}
        </div>

        <section aria-labelledby="ai-images-heading">
          <h2 id="ai-images-heading" className="visually-hidden">AI Images</h2>
          <ImageGenerator selectedContent={selectedContent} />
        </section>
      </main>
    </div>
  );
}

export default App;

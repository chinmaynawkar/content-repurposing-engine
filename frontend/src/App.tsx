import { useEffect, useState } from "react";
import ContentUpload from "./components/ContentUpload";
import { contentApi } from "./services/api";
import type { Content } from "./types";
import "./App.css";

function App() {
  const [contents, setContents] = useState<Content[]>([]);
  const [loading, setLoading] = useState(false);

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
              <div key={content.id} className="content-card">
                <h3>{content.title || "Untitled"}</h3>
                <div className="content-preview">
                  {content.original_text.substring(0, 150)}...
                </div>
                <div className="content-meta">
                  <span>{content.word_count} words</span>
                  <span>{new Date(content.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
        </div>
      </main>
    </div>
  );
}

export default App;

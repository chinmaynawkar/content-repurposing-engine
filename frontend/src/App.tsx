import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import HomePage from "./pages/HomePage";
import UploadPage from "./pages/UploadPage";
import LibraryPage from "./pages/LibraryPage";
import ContentDetailPage from "./pages/ContentDetailPage";
import AnalyticsPage from "./pages/AnalyticsPage";

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="upload" element={<UploadPage />} />
        <Route path="library" element={<LibraryPage />} />
        <Route path="content/:id" element={<ContentDetailPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
      </Route>
    </Routes>
  );
}

export default App;

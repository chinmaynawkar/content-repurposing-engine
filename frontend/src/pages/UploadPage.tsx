import { useNavigate } from "react-router-dom";
import ContentUpload from "../components/ContentUpload";

export default function UploadPage() {
  const navigate = useNavigate();

  const handleUploadSuccess = (content: { id: number }) => {
    navigate(`/content/${content.id}`, { replace: true });
  };

  return (
    <div className="page-content-wide">
      <h1 className="text-2xl sm:text-3xl font-semibold text-white mb-4 sm:mb-6 break-words">
        Upload
      </h1>
      <ContentUpload onUploadSuccess={handleUploadSuccess} />
    </div>
  );
}

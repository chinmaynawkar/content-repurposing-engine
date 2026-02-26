import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="border-t border-gray-800 bg-gray-900 mt-auto shrink-0">
      <div className="layout-container py-5 sm:py-6">
        <nav
          className="flex flex-wrap gap-x-4 gap-y-2 mb-2 min-h-[44px] sm:min-h-0 items-center"
          aria-label="Footer"
        >
          <Link
            to="/"
            className="text-gray-400 hover:text-white text-sm py-2 sm:py-0"
          >
            Home
          </Link>
          <Link
            to="/upload"
            className="text-gray-400 hover:text-white text-sm py-2 sm:py-0"
          >
            Upload
          </Link>
          <Link
            to="/library"
            className="text-gray-400 hover:text-white text-sm py-2 sm:py-0"
          >
            Library
          </Link>
          <Link
            to="/analytics"
            className="text-gray-400 hover:text-white text-sm py-2 sm:py-0"
          >
            Analytics
          </Link>
        </nav>
        <p className="text-gray-500 text-xs sm:text-sm">No login required – 100% free.</p>
      </div>
    </footer>
  );
}

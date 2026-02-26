import { Link } from "react-router-dom";

export default function HomePage() {
  return (
    <div className="page-content">
      <section className="section-gap">
        <h1 className="text-3xl sm:text-4xl font-semibold text-white mb-3 sm:mb-4 leading-tight break-words">
          Upload once. Generate everywhere. Save hours.
        </h1>
        <p className="text-gray-300 text-base sm:text-lg leading-relaxed mb-8 break-words">
          Paste your long-form content and get LinkedIn posts, Twitter threads, Instagram captions, SEO meta, and images in one place.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
          <Link
            to="/upload"
            className="inline-flex items-center justify-center rounded-md font-medium bg-accent-primary text-black px-6 py-3 sm:py-3.5 min-h-[48px] hover:bg-accent-hover transition-colors"
          >
            Upload content
          </Link>
          <Link
            to="/library"
            className="inline-flex items-center justify-center rounded-md font-medium bg-gray-800 text-white border border-gray-700 px-6 py-3 sm:py-3.5 min-h-[48px] hover:bg-gray-700 transition-colors"
          >
            View library
          </Link>
        </div>
      </section>
      <section className="text-gray-400 text-sm sm:text-base">
        <h2 className="text-gray-300 font-medium mb-2">How it works</h2>
        <ol className="list-decimal list-inside space-y-1 break-words">
          <li>Upload your blog, transcript, or article</li>
          <li>Choose platforms and generate (LinkedIn, Twitter, Instagram, SEO, images)</li>
          <li>Copy and share wherever you post</li>
        </ol>
      </section>
    </div>
  );
}

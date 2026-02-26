import { NavLink } from "react-router-dom";

export default function Header() {
  const navClass = ({ isActive }: { isActive: boolean }) =>
    `block px-4 py-3 sm:px-3 sm:py-2 rounded-md text-sm font-medium transition-colors min-h-[44px] sm:min-h-0 flex items-center justify-center sm:justify-start ${
      isActive
        ? "bg-gray-800 text-white"
        : "text-gray-300 hover:bg-gray-800 hover:text-white"
    }`;

  return (
    <header className="border-b border-gray-800 bg-gray-900">
      <div className="layout-container">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between sm:h-14 gap-2 sm:gap-0 py-3 sm:py-0">
          <NavLink
            to="/"
            className="text-white font-semibold hover:text-accent-primary transition-colors min-h-[44px] flex items-center shrink-0"
          >
            Content Hub
          </NavLink>
          <nav
            className="flex flex-wrap gap-1 sm:gap-1 -mx-2 sm:mx-0"
            aria-label="Main"
          >
            <NavLink to="/" end className={navClass}>
              Home
            </NavLink>
            <NavLink to="/upload" className={navClass}>
              Upload
            </NavLink>
            <NavLink to="/library" className={navClass}>
              Library
            </NavLink>
            <NavLink to="/analytics" className={navClass}>
              Analytics
            </NavLink>
          </nav>
        </div>
      </div>
    </header>
  );
}

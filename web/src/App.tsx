// App shell: top bar with the three routes (workspace, extract, story).
import { NavLink, Route, Routes } from "react-router-dom";
import Workspace from "./pages/Workspace";
import Extract from "./pages/Extract";
import Story from "./pages/Story";

const link = ({ isActive }: { isActive: boolean }) =>
  `px-3 py-1.5 rounded-sheet text-sm font-medium ${isActive ? "bg-ink text-sheet" : "text-graphite hover:text-ink"}`;

export default function App() {
  return (
    <div className="min-h-screen grid-paper">
      <header className="border-b border-rule bg-sheet/90 backdrop-blur sticky top-0 z-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 h-14 flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <Mark />
            <span className="font-semibold tracking-tight">Tie-Point Drift Check</span>
          </div>
          <nav className="ml-auto flex items-center gap-1">
            <NavLink to="/" end className={link}>Workspace</NavLink>
            <NavLink to="/extract" className={link}>Extract</NavLink>
            <NavLink to="/story" className={link}>Story</NavLink>
          </nav>
        </div>
      </header>
      <Routes>
        <Route path="/" element={<Workspace />} />
        <Route path="/extract" element={<Extract />} />
        <Route path="/story" element={<Story />} />
      </Routes>
    </div>
  );
}

function Mark() {
  // two scopes meeting at one tie-point
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden>
      <rect x="1" y="5" width="8" height="12" rx="1.5" fill="none" stroke="#16191D" strokeWidth="1.6" />
      <rect x="13" y="5" width="8" height="12" rx="1.5" fill="none" stroke="#16191D" strokeWidth="1.6" />
      <line x1="9" y1="11" x2="13" y2="11" stroke="#C2410C" strokeWidth="1.8" />
      <circle cx="11" cy="11" r="2" fill="#C2410C" />
    </svg>
  );
}

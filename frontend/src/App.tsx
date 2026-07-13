import { NavLink, Route, Routes } from "react-router-dom";
import { DecisionCard } from "./pages/DecisionCard";
import { PortfolioDashboard } from "./pages/PortfolioDashboard";

export default function App() {
  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">SAGE</span>
          <span className="brand-sub">Sarawak Allocation and Grant Evaluation</span>
        </div>
        <nav>
          <NavLink to="/" end>Decision Card</NavLink>
          <NavLink to="/portfolio">Portfolio</NavLink>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<DecisionCard />} />
          <Route path="/portfolio" element={<PortfolioDashboard />} />
        </Routes>
      </main>
      <footer className="footer">
        Fund evidence. Govern outcomes. · Human authority; AI never scores, vetoes or releases funds.
      </footer>
    </div>
  );
}

import "./style.css";
import { useInvestmentEvolution } from "./hooks/useInvestmentEvolution";
import { InvestmentEvolutionChart } from "./components/InvestmentEvolutionChart";

function App() {
  const { points, loading } = useInvestmentEvolution();

  return (
    <div className="app-root">
      <div className="app-card">
        <header className="app-header">
          <h1 className="app-title">Evolución de tu portafolio</h1>
          <p className="app-subtitle">
            Datos en tiempo real desde <code>investmentEvolutions/user1</code>
          </p>
        </header>

        {loading ? (
          <p className="loading">Cargando datos...</p>
        ) : points.length === 0 ? (
          <p className="empty">
            No hay datos de inversión aún para este usuario.
          </p>
        ) : (
          <>
            <InvestmentEvolutionChart points={points} />
          </>
        )}
      </div>
    </div>
  );
}

export default App;

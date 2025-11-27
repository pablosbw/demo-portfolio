import { ReturnChart } from "./ReturnChart.jsx";
import { PortfolioValueVsInvestedChart } from "./PortfolioValueVsInvestedChart.jsx";
import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";

ChartJS.register(
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
  Filler
);

const hoverLinePlugin = {
  id: "hoverLine",
  afterDatasetsDraw(chart) {
    const {
      ctx,
      tooltip,
      chartArea: { top, bottom },
    } = chart;

    if (!tooltip?.getActiveElements().length) return;

    const activePoint = tooltip.getActiveElements()[0];
    const x = activePoint.element.x;

    ctx.save();
    ctx.beginPath();
    ctx.setLineDash([4, 4]);
    ctx.moveTo(x, top);
    ctx.lineTo(x, bottom);
    ctx.lineWidth = 1;
    ctx.strokeStyle = "rgba(148, 163, 184, 0.9)";
    ctx.stroke();
    ctx.restore();
  },
};

ChartJS.register(hoverLinePlugin);

export function InvestmentEvolutionChart({ points }) {
  const sorted = [...points].sort(
    (a, b) => (a.date?.getTime?.() || 0) - (b.date?.getTime?.() || 0)
  );

  const labels = sorted.map((p) => p.dateLabel);
  const values = sorted.map((p) => p.portfolioValue || 0);
  const totalInvested = sorted.map((p) => p.contributions || 0);

  const percentReturn = values.map((v, i) => {
    const invested = totalInvested[i];
    if (!invested) return null;
    return ((v - invested) / invested) * 100;
  });

  return (
    <div className="chart-root">
      <div className="chart-box">
        <h3 className="chart-title">Valor del portafolio vs Total invertido</h3>
        <PortfolioValueVsInvestedChart
          labels={labels}
          values={values}
          totalInvested={totalInvested}
        />
      </div>

      <div className="chart-box">
        <h3 className="chart-title">Porcentaje de retorno</h3>
        <ReturnChart
          labels={labels}
          totalInvested={totalInvested}
          percentReturn={percentReturn}
        />
      </div>
    </div>
  );
}

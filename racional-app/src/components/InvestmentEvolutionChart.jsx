import { Line } from "react-chartjs-2";
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

function formatMoney(value) {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(1)}k`;
  return `$${value.toLocaleString()}`;
}

/* -----------------------------
 *  Chart 1: Valor vs Invertido
 * ----------------------------*/
function PortfolioValueVsInvestedChart({ labels, values, totalInvested }) {
  const data = {
    labels,
    datasets: [
      {
        label: "Valor del portafolio",
        data: values,
        borderColor: "#3b82f6",
        backgroundColor: "rgba(59, 130, 246, 0.15)",
        fill: true,
        tension: 0.25,
        pointRadius: 0,
        pointHoverRadius: 4,
      },
      {
        label: "Total invertido",
        data: totalInvested,
        borderColor: "#f59e0b",
        backgroundColor: "rgba(245, 158, 11, 0.08)",
        fill: false,
        tension: 0.25,
        pointRadius: 0,
        pointHoverRadius: 4,
        borderDash: [6, 4],
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: "index",
      intersect: false,
    },
    plugins: {
      legend: {
        display: true,
        labels: { usePointStyle: true },
      },
      tooltip: {
        mode: "index",
        intersect: false,
        usePointStyle: true,
        callbacks: {
          label(context) {
            const label = context.dataset.label;
            const value = context.parsed.y;
            return `${label}: ${formatMoney(value)}`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { maxRotation: 30, minRotation: 15 },
      },
      y: {
        grid: { color: "rgba(30, 64, 175, 0.15)" },
        ticks: {
          callback(value) {
            return formatMoney(value);
          },
        },
      },
    },
  };

  return <Line data={data} options={options} />;
}

/* ----------------------------------------
 *  Chart 2: % retorno
 * ---------------------------------------*/
function ReturnChart({ labels, percentReturn }) {
  const data = {
    labels,
    datasets: [
      {
        label: "retorno",
        data: percentReturn,
        borderColor: "#10b981",
        backgroundColor: "rgba(43, 104, 74, 0.15)",
        fill: true,
        tension: 0.25,
        pointRadius: 0,
        pointHoverRadius: 3,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: "index",
      intersect: false,
    },
    plugins: {
      legend: {
        display: true,
        labels: { usePointStyle: true },
      },
      tooltip: {
        mode: "index",
        intersect: false,
        usePointStyle: true,
        callbacks: {
          label(context) {
            const label = context.dataset.label;
            const value = context.parsed.y;

            if (label.includes("retorno")) {
              if (value == null) return `${label}: N/A`;
              return `${label}: ${value.toFixed(2)}%`;
            }
            return `${label}: ${formatMoney(value)}`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: { display: true },
        ticks: { maxRotation: 30, minRotation: 15 },
      },
      y: {
        position: "left",
        ticks: {
          callback(value) {
            return `${value}%`;
          },
        },
      },
    },
  };

  return <Line data={data} options={options} />;
}

/* ----------------------------------------
 *        Parent: orchestrates data
 * ---------------------------------------*/
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

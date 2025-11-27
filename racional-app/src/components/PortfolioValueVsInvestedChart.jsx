import { Line } from "react-chartjs-2";
import { formatMoney } from "../utils.js";
export function PortfolioValueVsInvestedChart({
  labels,
  values,
  totalInvested,
}) {
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

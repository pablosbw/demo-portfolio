import { Line } from "react-chartjs-2";

export function ReturnChart({ labels, percentReturn }) {
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

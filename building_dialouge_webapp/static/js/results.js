import { createChart } from "./charts.js";

const CHARTS = {
  cost_chart: "cost_chart_data",
  emission_chart: "emission_chart_data",
};

for (const chart in CHARTS) {
  const option = JSON.parse(document.getElementById(CHARTS[chart]).textContent);
  createChart(chart, option);
}

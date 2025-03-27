import { createChart } from "./charts.js";

const CHARTS = {
  cost_chart: "cost_chart_data",
  emission_chart: "emission_chart_data",
  heating_chart: "heating_chart_data",
  investment_chart: "investment_chart_data",
  co2_chart: "co2_chart_data",
};

for (const chart in CHARTS) {
  const option = JSON.parse(document.getElementById(CHARTS[chart]).textContent);
  createChart(chart, option);
}

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


document.addEventListener("DOMContentLoaded", function () {
  const buttons = document.querySelectorAll(".tab-button");
  const contents = document.querySelectorAll(".tab-content");

  buttons.forEach(button => {
    button.addEventListener("click", () => {
      // Deactivate all buttons and contents
      buttons.forEach(btn => btn.classList.remove("active"));
      contents.forEach(content => content.classList.remove("active"));

      // Activate the clicked tab and its content
      button.classList.add("active");
      const target = document.getElementById(button.dataset.tab);
      if (target) target.classList.add("active");
    });
  });
});

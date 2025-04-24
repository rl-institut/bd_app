import { createChart } from "./charts.js";

const CHARTS = {
  cost_chart: "cost_chart_data",
  emission_chart: "emission_chart_data",
  heating_chart: "heating_chart_data",
  co2_chart: "co2_chart_data",
  energycost_chart: "energycost_chart_data",
  financial_expense_chart: "financial_expense_chart_data_future",
};

for (const chart in CHARTS) {
  const option = JSON.parse(document.getElementById(CHARTS[chart]).textContent);
  createChart(chart, option);
}


// updating financial_expense_chart when clicking the button
const optionsNow = JSON.parse(document.getElementById("financial_expense_chart_data_now").textContent);
const optionsFuture = JSON.parse(document.getElementById("financial_expense_chart_data_future").textContent);

function updateEnergyCostChart(period) {
  if (period === 'now') {
    createChart("financial_expense_chart", optionsNow);  // true = replace all options
  } else if (period === 'future') {
    createChart("financial_expense_chart", optionsFuture);
  }
}
window.updateEnergyCostChart = updateEnergyCostChart;


// activate and deactivate the tabs (consumption, cost, emission)
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


document.addEventListener("DOMContentLoaded", function () {
  const wrappers = document.querySelectorAll(".foldable-wrapper");

  wrappers.forEach(wrapper => {
    const table = wrapper.querySelector("table");
    if (!table) return;

    const rows = table.querySelectorAll("tbody tr");
    if (rows.length <= 1) return;

    const summaryRow = rows[0];
    summaryRow.classList.add("summary-row");
    summaryRow.style.cursor = "pointer";

    const detailRows = Array.from(rows).slice(1);
    detailRows.forEach(row => row.classList.add("foldable-row"));

    // Initially hidden
    detailRows.forEach(row => {
      row.style.display = "none";
    });

    let expanded = false;
    summaryRow.addEventListener("click", () => {
      expanded = !expanded;
      detailRows.forEach(row => {
        row.style.display = expanded ? "table-row" : "none";
      });
      summaryRow.classList.toggle("open", expanded);
    });
  });
});

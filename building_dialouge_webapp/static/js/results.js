import { createChart } from "./charts.js";

const CHARTS = {
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
    createChart("financial_expense_chart", optionsNow);
  } else if (period === 'future') {
    createChart("financial_expense_chart", optionsFuture);
  }

  document
    .querySelectorAll('.results__cost-buttons button')
    .forEach(btn => {
      const handler = btn.getAttribute('onclick') || '';
      if (handler.includes(`'${period}'`)) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });
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

// unfolding and folding some tables in the costs table
document.addEventListener("DOMContentLoaded", function () {
  const wrappers = document.querySelectorAll(".foldable-wrapper");

  wrappers.forEach(wrapper => {
    const tables = wrapper.querySelectorAll("table");

    tables.forEach(table => {
      const headerRow = table.querySelector("thead tr");
      const rows = table.querySelectorAll("tbody tr");

      if (!headerRow || rows.length === 0) return;

      headerRow.classList.add("summary-row");
      headerRow.style.cursor = "pointer";

      const detailRows = Array.from(rows); // All body rows are foldable

      // Initially hidden
      detailRows.forEach(row => {
        row.classList.add("foldable-row");
        row.style.display = "none";
      });

      let expanded = false;
      headerRow.addEventListener("click", () => {
        expanded = !expanded;
        detailRows.forEach(row => {
          row.style.display = expanded ? "table-row" : "none";
        });
        headerRow.classList.toggle("open", expanded);
      });
    });
  });
});

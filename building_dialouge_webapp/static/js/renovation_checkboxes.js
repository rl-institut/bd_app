document.addEventListener("htmx:afterSwap", setupRenovationCheckboxLogic);
document.addEventListener("DOMContentLoaded", setupRenovationCheckboxLogic);
document.addEventListener("htmx:afterSwap", deleteUnusedDivs);
document.addEventListener("DOMContentLoaded", deleteUnusedDivs);

function setupRenovationCheckboxLogic() {
  document.querySelectorAll("form").forEach((form) => {
    form.addEventListener("submit", () => {
      // For each renovation group, deselect details if main choice is unchecked
      ["roof", "facade"].forEach((section) => {
        const mainCheckboxes = form.querySelectorAll(
          `input[name$="-${section}_renovation_choice"]`
        );
        mainCheckboxes.forEach((mainCheckbox) => {
          const prefix = mainCheckbox.name.replace(`-${section}_renovation_choice`, "");
          if (!mainCheckbox.checked) {
            const detailCheckboxes = form.querySelectorAll(
              `input[name="${prefix}-${section}_renovation_details"]`
            );
            detailCheckboxes.forEach((cb) => (cb.checked = false));
          }
        });
      });
    });
  });

  // Keep your change event handlers for live interaction:
  document.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
    const name = checkbox.name;

    if (name.endsWith("-roof_renovation_choice")) {
      checkbox.addEventListener("change", () => {
        const prefix = name.replace("-roof_renovation_choice", "");
        const details = document.querySelectorAll(
          `input[name="${prefix}-roof_renovation_details"]`
        );
        if (!checkbox.checked) details.forEach((cb) => (cb.checked = false));
      });
    }

    if (name.endsWith("-roof_renovation_details")) {
      checkbox.addEventListener("change", () => {
        const prefix = name.replace("-roof_renovation_details", "");
        const main = document.querySelector(
          `input[name="${prefix}-roof_renovation_choice"]`
        );
        if (checkbox.checked && main && !main.checked) main.checked = true;
      });
    }

    if (name.endsWith("-facade_renovation_choice")) {
      checkbox.addEventListener("change", () => {
        const prefix = name.replace("-facade_renovation_choice", "");
        const details = document.querySelectorAll(
          `input[name="${prefix}-facade_renovation_details"]`
        );
        if (!checkbox.checked) details.forEach((cb) => (cb.checked = false));
      });
    }

    if (name.endsWith("-facade_renovation_details")) {
      checkbox.addEventListener("change", () => {
        const prefix = name.replace("-facade_renovation_details", "");
        const main = document.querySelector(
          `input[name="${prefix}-facade_renovation_choice"]`
        );
        if (checkbox.checked && main && !main.checked) main.checked = true;
      });
    }
  });
}


function deleteUnusedDivs() {
  const container = document.querySelector("#secondary_heating");
  if (!container) return;

  const childDivs = container.querySelectorAll("div");

  childDivs.forEach((div) => {
    if (div.innerHTML.trim() === "") {
      div.style.display = "none";
    } else {
      div.style.display = ""; // reset display if content is present again
    }
  });
}

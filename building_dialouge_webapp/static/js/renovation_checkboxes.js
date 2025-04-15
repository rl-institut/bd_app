
document.addEventListener("htmx:afterSwap", function () {
    document.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
      const name = checkbox.name;

      if (name.endsWith("-roof_renovation")) {
        checkbox.addEventListener("change", function () {
          const prefix = name.replace("-roof_renovation", "");
          const radios = document.querySelectorAll(
            `input[name="${prefix}-roof_renovation_details"]`
          );
          if (!checkbox.checked) {
            radios.forEach((radio) => (radio.checked = false));
          }
        });
      }

      if (name.endsWith("-facade_renovation")) {
        checkbox.addEventListener("change", function () {
          const prefix = name.replace("-facade_renovation", "");
          const radios = document.querySelectorAll(
            `input[name="${prefix}-facade_renovation_details"]`
          );
          if (!checkbox.checked) {
            radios.forEach((radio) => (radio.checked = false));
          }
        });
      }
    });
  });

// Listen for HTMX events and handle validation for all forms
document.addEventListener("htmx:beforeRequest", (event) => {
  const form = event.target.closest(".main"); // Target the closest form
  if (!form) return;

  const requiredFields = form.querySelectorAll("[required]");
  let allValid = true;

  requiredFields.forEach((field) => {
    if (field.type === "radio" || field.type === "checkbox") {
      // RadioButtons and Checkboxes
      const group = form.querySelectorAll(`[name="${field.name}"]`);
      const isChecked = Array.from(group).some((input) => input.checked);
      if (!isChecked) allValid = false;
    } else if (field.tagName === "SELECT") {
      // Select Fields
      if (!field.value) allValid = false;
    } else {
      // For text, number, or other inputs
      if (!field.value.trim()) allValid = false;
    }
  });
  if (!allValid) {
    event.preventDefault(); // Stop the HTMX request
  }
});

// extra check for Checkboxes in RenovationRequest - RenovationDetailsForm
document.addEventListener("htmx:beforeSend", function(event) {
  let checkboxes = document.querySelectorAll('input[name="roof_renovation_details"]');
  let hiddenInput = document.querySelector('input[name="roof_renovation_details_hidden"]');

  let anyChecked = Array.from(checkboxes).some(cb => cb.checked);
  if (!anyChecked) {
      hiddenInput.value = "none";
  }
});


// extra Check for ConsumptionInput Type, when one type cannot be added anymore
document.addEventListener("DOMContentLoaded", function() {
    let disabledInput = document.querySelector("[name='consumption_type']:disabled");
    if (disabledInput) {
        htmx.trigger(disabledInput.form, "htmx:change");
    }
});

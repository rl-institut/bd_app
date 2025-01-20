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

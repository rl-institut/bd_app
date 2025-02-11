// extra Check for ConsumptionInput Type, when one type cannot be added anymore
// needs a manual trigger of htmx change to attach the value of the form and trigger flow transition
document.addEventListener("DOMContentLoaded", function () {
    let disabledInput = document.querySelector("input[name$='consumption_type']:disabled:checked");
    console.log(disabledInput)
    if (disabledInput) {
        // Find closest container with an hx-post attribute (simulating a form)
        let formContainer = disabledInput.closest("[hx-post]");
        if (!formContainer) {
            console.warn("No hx-post container found for the disabled input.");
            return;
        }
        htmx.ajax("POST", formContainer.getAttribute("hx-post"), {
            values: { [disabledInput.name]: disabledInput.value }
        });
    }
  });

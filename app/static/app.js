document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-confirm]").forEach((button) => {
    button.addEventListener("click", (event) => {
      if (!confirm(button.dataset.confirm)) {
        event.preventDefault();
      }
    });
  });

document.querySelectorAll(".alert[data-autohide]").forEach((alert) => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      bsAlert.close();
    }, 5000);
  });

document.querySelectorAll("form[novalidate]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add("was-validated");
    });
  });
});

document.addEventListener('DOMContentLoaded', function() {
    const toastEl = document.getElementById('flashToast');
    if (toastEl) {
      const toast = new bootstrap.Toast(toastEl, {
        delay: 3000,
        autohide: true
      });
      toast.show();
    }
  });
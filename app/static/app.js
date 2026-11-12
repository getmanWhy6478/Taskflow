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


  const toastEl = document.getElementById('flashToast');
  if (toastEl) {
    const toast = new bootstrap.Toast(toastEl, {
      delay: 3000,
      autohide: true
    });
    toast.show();
  }

  const cards = document.querySelectorAll('.kanban-card');
  const columns = document.querySelectorAll('.kanban-cards');
  let draggedCard = null;

  cards.forEach(card => {
    card.addEventListener('dragstart', (e) => {
      draggedCard = card;
      card.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', card.dataset.taskId);
    });

    card.addEventListener('dragend', () => {
      card.classList.remove('dragging');
      draggedCard = null;
      columns.forEach(col => col.classList.remove('drag-over'));
    });
  });

  columns.forEach(column => {
    column.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      column.classList.add('drag-over');

      const afterElement = getDragAfterElement(column, e.clientY);
      if (draggedCard) {
        if (afterElement == null) {
          column.appendChild(draggedCard);
        } else {
          column.insertBefore(draggedCard, afterElement);
        }
      }
    });

    column.addEventListener('dragleave', (e) => {
      if (!column.contains(e.relatedTarget)) {
        column.classList.remove('drag-over');
      }
    });


    column.addEventListener('drop', (e) => {
      e.preventDefault();
      column.classList.remove('drag-over');

      const taskId = e.dataTransfer.getData('text/plain');
      const newStatus = column.dataset.status;

      if (!taskId || !newStatus) return;

      const form = document.createElement('form');
      form.method = 'POST';
      form.action = `/tasks/${taskId}/status`;

      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = 'status';
      input.value = newStatus;

      form.appendChild(input);
      document.body.appendChild(form);

      form.submit();
    });
  });




  function getDragAfterElement(container, y) {
    const draggableElements = [
      ...container.querySelectorAll('.kanban-card:not(.dragging)')
    ];

    return draggableElements.reduce((closest, child) => {
      const box = child.getBoundingClientRect();
      const offset = y - box.top - box.height / 2;
      if (offset < 0 && offset > closest.offset) {
        return { offset: offset, element: child };
      } else {
        return closest;
      }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
  }

  function updateColumnCounters() {
    const cols = document.querySelectorAll('.kanban-cards');
    cols.forEach(column => {
      const status = column.dataset.status;
      const count = column.querySelectorAll('.kanban-card').length;
      const header = document.querySelector(`.kanban-column[data-status="${status}"] .badge`);
      if (header) header.textContent = count;
    });
  }

  function showToast(message, type = 'success') {
    const toast = document.getElementById('kanban-toast');
    if (!toast) return;

    toast.textContent = message;
    toast.className = `kanban-toast ${type}`;
    toast.style.display = 'block';

    setTimeout(() => {
      toast.style.display = 'none';
    }, 3000);
  }
});



function updateThemeIcon(theme) {
  const sunIcon = document.getElementById('theme-icon-sun');
  const moonIcon = document.getElementById('theme-icon-moon');

  if (theme === 'dark') {
    sunIcon.style.display = 'inline-block';
    moonIcon.style.display = 'none';
  } else {
    sunIcon.style.display = 'none';
    moonIcon.style.display = 'inline-block';
  }
}

function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute('data-bs-theme');
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

  document.documentElement.setAttribute('data-bs-theme', newTheme);
  localStorage.setItem('theme', newTheme);
  updateThemeIcon(newTheme);
}


document.addEventListener('DOMContentLoaded', () => {
  const currentTheme = document.documentElement.getAttribute('data-bs-theme');
  updateThemeIcon(currentTheme);
});
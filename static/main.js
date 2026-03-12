function patchTask(taskId, payload) {
  return fetch(`/api/tasks/${taskId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

function moveTaskElement(taskId, status) {
  const element = document.querySelector(`li[data-task-id="${taskId}"]`);
  const targetList = document.getElementById(`column-${status}`);
  if (!element || !targetList) {
    return;
  }
  targetList.appendChild(element);
  const select = document.querySelector(`select[data-task-id="${taskId}"]`);
  if (select) {
    select.value = status;
    select.dataset.currentStatus = status;
  }
}

function setupEditableField(selector, fieldName) {
  document.querySelectorAll(selector).forEach((element) => {
    element.dataset.lastValue = element.textContent.trim();
    element.addEventListener("blur", () => {
      const nextValue = element.textContent.trim();
      if (nextValue === element.dataset.lastValue) {
        return;
      }
      patchTask(element.dataset.taskId, { [fieldName]: nextValue }).catch(() => {
        element.textContent = element.dataset.lastValue;
      });
      element.dataset.lastValue = nextValue;
    });
    element.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        element.blur();
      }
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  setupEditableField(".task-title", "title");

  document.querySelectorAll(".status-select").forEach((select) => {
    select.addEventListener("change", () => {
      const desired = select.value;
      patchTask(select.dataset.taskId, { status: desired })
        .then(() => {
          moveTaskElement(select.dataset.taskId, desired);
        })
        .catch(() => {
          select.value = select.dataset.currentStatus || desired;
        });
    });
  });

  const makeDraggable = (card) => {
    card.addEventListener("dragstart", (event) => {
      const taskId = card.dataset.taskId;
      event.dataTransfer.setData("text/plain", taskId);
      event.dataTransfer.effectAllowed = "move";
      card.classList.add("dragging");
    });
    card.addEventListener("dragend", () => {
      card.classList.remove("dragging");
    });
  };

  document.querySelectorAll(".tasks-column li[draggable='true']").forEach(makeDraggable);

  document.querySelectorAll(".tasks-column").forEach((column) => {
    column.addEventListener("dragover", (event) => {
      event.preventDefault();
      column.classList.add("drag-over");
      event.dataTransfer.dropEffect = "move";
    });
    column.addEventListener("dragleave", () => {
      column.classList.remove("drag-over");
    });
    column.addEventListener("drop", (event) => {
      event.preventDefault();
      column.classList.remove("drag-over");
      const taskId = event.dataTransfer.getData("text/plain");
      if (!taskId) {
        return;
      }
      const status = column.dataset.status;
      patchTask(taskId, { status }).then(() => {
        moveTaskElement(taskId, status);
      });
    });
  });
});

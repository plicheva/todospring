function patchTask(taskId, payload) {
  return fetch(`/api/tasks/${taskId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

function moveTaskElement(taskId, isDone) {
  const element = document.querySelector(`li[data-task-id="${taskId}"]`);
  const pendingList = document.getElementById("pending-list");
  const doneList = document.getElementById("done-list");
  if (!element || !pendingList || !doneList) {
    return;
  }
  const targetList = isDone ? doneList : pendingList;
  targetList.appendChild(element);
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

  document.querySelectorAll(".toggle-done").forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
      const desired = checkbox.checked;
      patchTask(checkbox.dataset.taskId, { done: desired })
        .then(() => {
          moveTaskElement(checkbox.dataset.taskId, desired);
        })
        .catch(() => {
          checkbox.checked = !desired;
        });
    });
  });
});

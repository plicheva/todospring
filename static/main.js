function patchTask(taskId, payload) {
  const csrfToken = document.querySelector("meta[name='csrf-token']")?.content || "";
  return fetch(`/api/tasks/${taskId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfToken,
    },
    body: JSON.stringify(payload),
  }).then((response) => {
    if (!response.ok) {
      throw new Error("Task update failed");
    }
    return response;
  });
}

function getTaskCard(target) {
  return target.closest("li[data-task-id]");
}

function updateColumnCount(column) {
  if (!column) {
    return;
  }
  const counter = column.querySelector("[data-column-count]");
  if (counter) {
    counter.textContent = column.querySelectorAll("li[data-task-id]").length;
  }
}

function clearDragTargets() {
  document.querySelectorAll(".tasks-column.drag-over").forEach((column) => {
    column.classList.remove("drag-over");
  });
}

function getColumnAtPoint(x, y) {
  return document.elementFromPoint(x, y)?.closest(".tasks-column") || null;
}

function restoreDraggedCard(state) {
  const { card, placeholder } = state;
  card.classList.remove("dragging");
  card.style.position = "";
  card.style.left = "";
  card.style.top = "";
  card.style.width = "";
  card.style.margin = "";
  card.style.zIndex = "";
  card.style.pointerEvents = "";
  card.style.transform = "";
  if (placeholder.parentElement) {
    placeholder.remove();
  }
}

function moveTaskElement(taskId, status) {
  const element = document.querySelector(`li[data-task-id="${taskId}"]`);
  const targetList = document.getElementById(`column-${status}`);
  if (!element || !targetList) {
    return;
  }
  const sourceColumn = element.closest(".tasks-column");
  const targetColumn = targetList.closest(".tasks-column");
  const emptyState = targetList.querySelector(".empty-column");
  if (emptyState) {
    emptyState.remove();
  }
  targetList.appendChild(element);
  element.dataset.status = status;
  const select = document.querySelector(`select[data-task-id="${taskId}"]`);
  if (select) {
    select.value = status;
    select.dataset.currentStatus = status;
  }
  updateColumnCount(sourceColumn);
  updateColumnCount(targetColumn);
}

function setupEditableField(selector, fieldName) {
  document.querySelectorAll(selector).forEach((element) => {
    element.dataset.lastValue = element.textContent.trim();
    element.addEventListener("blur", () => {
      const nextValue = element.textContent.trim();
      if (nextValue === element.dataset.lastValue) {
        return;
      }
      patchTask(element.dataset.taskId, { [fieldName]: nextValue })
        .then(() => {
          element.dataset.lastValue = nextValue;
          if (fieldName === "title") {
            const titleInput = document.querySelector(
              `input[data-task-title-input="${element.dataset.taskId}"]`
            );
            if (titleInput) {
              titleInput.value = nextValue;
            }
          }
        })
        .catch(() => {
          element.textContent = element.dataset.lastValue;
        });
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

  document.querySelectorAll(".status-form").forEach((form) => {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
    });
  });

  document.querySelectorAll(".status-select").forEach((select) => {
    select.addEventListener("change", () => {
      const desired = select.value;
      const previous = select.dataset.currentStatus || desired;
      patchTask(select.dataset.taskId, { status: desired })
        .then(() => {
          moveTaskElement(select.dataset.taskId, desired);
        })
        .catch(() => {
          const form = select.closest(".status-form");
          if (form) {
            form.submit();
            return;
          }
          select.value = previous;
        });
    });
  });

  const board = document.querySelector(".kanban-board");
  let dragState = null;
  let pendingDrag = null;

  if (board) {
    function startPointerDrag(event, pending) {
      const { card } = pending;
      const rect = card.getBoundingClientRect();
      const placeholder = document.createElement("li");
      placeholder.className = "drag-placeholder";
      placeholder.style.height = `${rect.height}px`;
      card.after(placeholder);

      dragState = {
        card,
        placeholder,
        taskId: card.dataset.taskId,
        sourceStatus: card.dataset.status,
        startX: pending.startX,
        startY: pending.startY,
        currentColumn: card.closest(".tasks-column"),
      };

      card.classList.add("dragging");
      card.style.position = "fixed";
      card.style.left = `${rect.left}px`;
      card.style.top = `${rect.top}px`;
      card.style.width = `${rect.width}px`;
      card.style.margin = "0";
      card.style.zIndex = "1000";
      card.style.pointerEvents = "none";
      event.preventDefault();
    }

    board.addEventListener("pointerdown", (event) => {
      if (event.button !== 0) {
        return;
      }

      const blockedControl = event.target.closest(
        "a, input, select, textarea, form, button:not(.drag-handle)"
      );
      if (blockedControl) {
        return;
      }

      const card = getTaskCard(event.target);
      if (!card) {
        return;
      }

      pendingDrag = {
        card,
        startX: event.clientX,
        startY: event.clientY,
        fromHandle: Boolean(event.target.closest(".drag-handle")),
      };

      if (pendingDrag.fromHandle) {
        startPointerDrag(event, pendingDrag);
        pendingDrag = null;
      }
    });

    document.addEventListener("pointermove", (event) => {
      if (!dragState && pendingDrag) {
        const dx = event.clientX - pendingDrag.startX;
        const dy = event.clientY - pendingDrag.startY;
        if (Math.hypot(dx, dy) < 6) {
          return;
        }
        startPointerDrag(event, pendingDrag);
        pendingDrag = null;
      }

      if (!dragState) {
        return;
      }
      event.preventDefault();
      const dx = event.clientX - dragState.startX;
      const dy = event.clientY - dragState.startY;
      dragState.card.style.transform = `translate(${dx}px, ${dy}px)`;

      clearDragTargets();
      const column = getColumnAtPoint(event.clientX, event.clientY);
      if (column) {
        column.classList.add("drag-over");
        dragState.currentColumn = column;
      }
    });

    function finishPointerDrag(event) {
      if (pendingDrag && !dragState) {
        pendingDrag = null;
        return;
      }

      if (!dragState) {
        return;
      }
      event.preventDefault();
      const state = dragState;
      const targetColumn = getColumnAtPoint(event.clientX, event.clientY) || state.currentColumn;
      const targetStatus = targetColumn?.dataset.status;

      dragState = null;
      clearDragTargets();
      restoreDraggedCard(state);

      if (!targetStatus || targetStatus === state.sourceStatus) {
        return;
      }

      moveTaskElement(state.taskId, targetStatus);
      patchTask(state.taskId, { status: targetStatus })
        .then(() => {
          moveTaskElement(state.taskId, targetStatus);
        })
        .catch(() => {
          moveTaskElement(state.taskId, state.sourceStatus);
        });
    }

    document.addEventListener("pointerup", finishPointerDrag);
    document.addEventListener("pointercancel", (event) => {
      pendingDrag = null;
      if (!dragState) {
        return;
      }
      event.preventDefault();
      const state = dragState;
      dragState = null;
      clearDragTargets();
      restoreDraggedCard(state);
    });
  }
});

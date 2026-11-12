const form = document.querySelector("#report-form");
const formMessage = document.querySelector("#form-message");
const reportsMessage = document.querySelector("#reports-message");
const reportList = document.querySelector("#report-list");
const refreshButton = document.querySelector("#refresh-button");

function showMessage(element, message, isError = false) {
  element.textContent = message;
  element.classList.toggle("error", isError);
}

async function request(url, options) {
  const response = await fetch(url, options);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Não foi possível concluir a operação.");
  }
  return payload;
}

function createReportCard(report) {
  const card = document.createElement("article");
  card.className = "report-card";

  const header = document.createElement("div");
  header.className = "report-header";

  const category = document.createElement("span");
  category.className = "category";
  category.textContent = report.category;

  const date = document.createElement("time");
  date.dateTime = report.created_at;
  date.textContent = new Date(report.created_at).toLocaleString("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  });

  const location = document.createElement("h3");
  location.textContent = report.location;

  const description = document.createElement("p");
  description.className = "report-description";
  description.textContent = report.description;

  const removeButton = document.createElement("button");
  removeButton.className = "delete-button";
  removeButton.type = "button";
  removeButton.textContent = "Excluir relato";
  removeButton.setAttribute("aria-label", `Excluir relato: ${report.location}`);
  removeButton.addEventListener("click", async () => {
    if (!window.confirm("Deseja excluir este relato?")) return;
    removeButton.disabled = true;
    try {
      await request(`/api/reports/${report.id}`, { method: "DELETE" });
      await loadReports();
    } catch (error) {
      showMessage(reportsMessage, error.message, true);
      removeButton.disabled = false;
    }
  });

  header.append(category, date);
  card.append(header, location, description, removeButton);
  return card;
}

async function loadReports() {
  showMessage(reportsMessage, "Carregando relatos...");
  reportList.replaceChildren();
  try {
    const reports = await request("/api/reports");
    if (reports.length === 0) {
      showMessage(reportsMessage, "Ainda não há relatos. Seja a primeira pessoa a contribuir!");
      return;
    }
    showMessage(reportsMessage, "");
    reportList.append(...reports.map(createReportCard));
  } catch (error) {
    showMessage(reportsMessage, error.message, true);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const submitButton = form.querySelector('button[type="submit"]');
  submitButton.disabled = true;
  showMessage(formMessage, "Publicando...");
  const formData = new FormData(form);
  try {
    await request("/api/reports", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        category: formData.get("category"),
        location: formData.get("location"),
        description: formData.get("description"),
      }),
    });
    form.reset();
    showMessage(formMessage, "Relato publicado com sucesso.");
    await loadReports();
  } catch (error) {
    showMessage(formMessage, error.message, true);
  } finally {
    submitButton.disabled = false;
  }
});

refreshButton.addEventListener("click", loadReports);
loadReports();

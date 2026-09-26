(function () {
  "use strict";

  const root = document.getElementById("api-docs");
  const search = document.getElementById("search");
  const methodFilter = document.getElementById("method-filter");
  const title = document.getElementById("api-title");
  const description = document.getElementById("api-description");

  let spec = null;

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
    }[char]));
  }

  function methodBadge(method) {
    return `<span class="method ${method}">${method}</span>`;
  }

  function render() {
    if (!spec) return;
    const needle = search.value.trim().toLowerCase();
    const method = methodFilter.value;
    const entries = [];

    Object.entries(spec.paths || {}).forEach(([path, operations]) => {
      Object.entries(operations || {}).forEach(([verb, operation]) => {
        const upperVerb = verb.toUpperCase();
        if (!["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"].includes(upperVerb)) return;
        const text = `${upperVerb} ${path} ${operation.summary || ""} ${operation.description || ""} ${(operation.tags || []).join(" ")}`.toLowerCase();
        if (method !== "ALL" && method !== upperVerb) return;
        if (needle && !text.includes(needle)) return;
        entries.push({ path, verb: upperVerb, operation });
      });
    });

    entries.sort((a, b) => `${a.path}${a.verb}`.localeCompare(`${b.path}${b.verb}`));
    root.innerHTML = entries.length ? entries.map(({ path, verb, operation }) => {
      const tags = (operation.tags || []).map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("");
      const responseCodes = Object.keys(operation.responses || {}).join(", ") || "-";
      const requestBody = operation.requestBody ? JSON.stringify(operation.requestBody, null, 2) : "Nenhum";
      const parameters = operation.parameters ? JSON.stringify(operation.parameters, null, 2) : "Nenhum";
      return `<details class="endpoint">
        <summary>${methodBadge(verb)} <span class="path">${escapeHtml(path)}</span><span class="summary-text">${escapeHtml(operation.summary || operation.description || "")}</span></summary>
        <div class="endpoint-body">
          <p>${escapeHtml(operation.description || operation.summary || "Sem descrição.")}</p>
          ${tags}
          <p><strong>Respostas:</strong> ${escapeHtml(responseCodes)}</p>
          <p><strong>Parâmetros</strong></p><pre>${escapeHtml(parameters)}</pre>
          <p><strong>Corpo da requisição</strong></p><pre>${escapeHtml(requestBody)}</pre>
        </div>
      </details>`;
    }).join("") : `<p class="muted">Nenhum endpoint corresponde ao filtro.</p>`;
  }

  search.addEventListener("input", render);
  methodFilter.addEventListener("change", render);

  fetch("/openapi.json", { headers: { "Accept": "application/json" } })
    .then((response) => {
      if (!response.ok) throw new Error(`Falha ao carregar OpenAPI: HTTP ${response.status}`);
      return response.json();
    })
    .then((data) => {
      spec = data;
      title.textContent = data.info?.title || "Documentação da API";
      description.textContent = `${data.info?.description || ""} Versão: ${data.info?.version || "não informada"}`;
      render();
    })
    .catch((error) => {
      root.innerHTML = `<div class="error">${escapeHtml(error.message)}</div>`;
    });
})();

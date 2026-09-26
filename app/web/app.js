const API_BASE = "/api/v1";
const TOKEN_KEY = "ica_access_token";
const ROLE_KEY = "ica_role";
const VALID_SCREENS = ["login", "registro", "upload", "admin", "reset"];
const SCREEN_ROUTES = {
  login: "/login",
  registro: "/registro",
  upload: "/enviar-arquivo",
  reset: "/redefinir-senha",
};
const ROUTE_SCREENS = {
  "/": "login",
  "/login": "login",
  "/registro": "registro",
  "/enviar-arquivo": "upload",
  "/upload": "upload",
  "/admin": "admin",
  "/painel-admin": "admin",
  "/redefinir-senha": "reset",
};

const registerForm = document.getElementById("form-register");
const loginForm = document.getElementById("form-login");
const uploadForm = document.getElementById("form-upload");
const navLogoutBtn = document.getElementById("nav-logout-btn");
const navAdminBtn = document.getElementById("nav-admin-btn");
const adminRefreshBtn = document.getElementById("admin-refresh-btn");
const adminStatus = document.getElementById("admin-status");
const adminMetrics = document.getElementById("admin-metrics");
const sprint3Cards = document.getElementById("sprint3-cards");
const compareBtn = document.getElementById("compare-btn");
const compareResult = document.getElementById("compare-result");
const adminUserForm = document.getElementById("form-admin-user");
const adminUserFeedback = document.getElementById("admin-user-feedback");
const adminInviteResult = document.getElementById("admin-invite-result");
const adminUsersList = document.getElementById("admin-users-list");
const resetPasswordForm = document.getElementById("form-reset-password");
const resetFeedback = document.getElementById("reset-feedback");

const registerFeedback = document.getElementById("register-feedback");
const loginFeedback = document.getElementById("login-feedback");
const uploadFeedback = document.getElementById("upload-feedback");
const resetTokenFromUrl = new URLSearchParams(window.location.search).get("token") || "";
const routeLinks = document.querySelectorAll("[data-screen-target]");
const navButtons = document.querySelectorAll(".screen-nav [data-screen-target]");
const authStateItems = document.querySelectorAll("[data-auth-state]");
const screens = document.querySelectorAll(".screen");

function tokenAtual() {
  return localStorage.getItem(TOKEN_KEY);
}

function roleAtual() {
  return localStorage.getItem(ROLE_KEY);
}

function salvarCookieSessao(token, maxAgeSeconds = null) {
  const maxAge = maxAgeSeconds ? `; max-age=${maxAgeSeconds}` : "";
  document.cookie = `${TOKEN_KEY}=${encodeURIComponent(token)}; path=/; SameSite=Lax${maxAge}`;
}

function removerCookieSessao() {
  document.cookie = `${TOKEN_KEY}=; path=/; max-age=0; SameSite=Lax`;
}

function setFeedback(el, mensagem, tipo = "ok") {
  el.textContent = mensagem;
  el.classList.remove("ok", "erro");
  el.classList.add(tipo);
}

function limparFeedbacks() {
  [registerFeedback, loginFeedback, uploadFeedback].forEach((el) => {
    el.textContent = "";
    el.classList.remove("ok", "erro");
  });
}

function atualizarStatusToken() {
  const token = tokenAtual();
  const autenticado = Boolean(token);

  if (autenticado) {
    salvarCookieSessao(token);
  } else {
    removerCookieSessao();
  }

  navButtons.forEach((button) => {
    if (button.dataset.authRequired === "true") {
      button.classList.toggle("locked", !autenticado);
      button.setAttribute("aria-disabled", String(!autenticado));
    }
  });

  authStateItems.forEach((item) => {
    const visivel =
      (item.dataset.authState === "authenticated" && autenticado) ||
      (item.dataset.authState === "guest" && !autenticado);

    item.hidden = !visivel;
  });

  if (navAdminBtn) {
    navAdminBtn.hidden = !(autenticado && roleAtual() === "admin");
  }
}

function telaDaRotaAtual() {
  return ROUTE_SCREENS[window.location.pathname] || "login";
}

function ativarTela(nomeTela, atualizarRota = true, substituirRota = false) {
  const telaValida = VALID_SCREENS.includes(nomeTela) ? nomeTela : "login";
  const autenticado = Boolean(tokenAtual());
  const telaPermitida =
    (telaValida === "upload" && autenticado) ||
    (telaValida === "admin" && autenticado && roleAtual() === "admin") ||
    (telaValida === "reset" && Boolean(resetTokenFromUrl)) ||
    (telaValida !== "upload" && telaValida !== "admin" && telaValida !== "reset");
  const telaFinal = telaPermitida ? telaValida : "login";

  screens.forEach((screen) => {
    const ativa = screen.id === `screen-${telaFinal}`;
    screen.hidden = !ativa;
    screen.classList.toggle("active", ativa);
  });

  navButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.screenTarget === telaFinal);
  });

  if (atualizarRota && SCREEN_ROUTES[telaFinal] && window.location.pathname !== SCREEN_ROUTES[telaFinal]) {
    const metodoHistorico = substituirRota ? "replaceState" : "pushState";
    history[metodoHistorico](null, "", SCREEN_ROUTES[telaFinal]);
  }

  if (!telaPermitida) {
    setFeedback(loginFeedback, telaValida === "admin" ? "Acesso exclusivo para administradores." : "Entre para liberar o envio de arquivos.", "erro");
  }

  if (telaFinal === "admin") {
    carregarPainelAdmin();
  }
}

async function postJson(url, payload, token = null) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;

  const resposta = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });

  const data = await resposta.json().catch(() => ({}));
  if (!resposta.ok) {
    throw new Error(data.detail || "Falha ao processar requisicao.");
  }
  return data;
}

routeLinks.forEach((link) => {
  link.addEventListener("click", (event) => {
    event.preventDefault();
    limparFeedbacks();
    ativarTela(link.dataset.screenTarget);
  });
});

registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setFeedback(registerFeedback, "Processando cadastro...", "ok");

  const nome = document.getElementById("register-nome").value;
  const email = document.getElementById("register-email").value;
  const password = document.getElementById("register-password").value;

  try {
    const data = await postJson(`${API_BASE}/auth/register`, { nome, email, password });
    setFeedback(registerFeedback, `Usuario ${data.email} cadastrado com sucesso.`, "ok");
    registerForm.reset();
    ativarTela("login");
    setFeedback(loginFeedback, "Cadastro concluido. Agora faca login.", "ok");
  } catch (erro) {
    setFeedback(registerFeedback, erro.message, "erro");
  }
});

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setFeedback(loginFeedback, "Validando credenciais...", "ok");

  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;

  try {
    const data = await postJson(`${API_BASE}/auth/login`, { email, password });
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(ROLE_KEY, data.role);
    salvarCookieSessao(data.access_token, data.expires_in_minutes * 60);
    setFeedback(loginFeedback, `Login realizado para ${data.email}.`, "ok");
    loginForm.reset();
    atualizarStatusToken();
    ativarTela("upload");
    setFeedback(uploadFeedback, "Login ativo. Selecione o arquivo para envio.", "ok");
  } catch (erro) {
    setFeedback(loginFeedback, erro.message, "erro");
  }
});

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setFeedback(uploadFeedback, "Enviando arquivo...", "ok");

  const token = tokenAtual();
  if (!token) {
    setFeedback(uploadFeedback, "Efetue login antes do upload.", "erro");
    ativarTela("login");
    setFeedback(loginFeedback, "Entre para liberar o envio de arquivos.", "erro");
    return;
  }

  const arquivoInput = document.getElementById("arquivo-excel");
  const arquivo = arquivoInput.files[0];
  if (!arquivo) {
    setFeedback(uploadFeedback, "Selecione um arquivo Excel.", "erro");
    return;
  }

  const formData = new FormData();
  formData.append("arquivo", arquivo);

  try {
    const resposta = await fetch(`${API_BASE}/uploads/excel`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });

    const data = await resposta.json().catch(() => ({}));
    if (!resposta.ok) {
      if (resposta.status === 401 || resposta.status === 403) {
        localStorage.removeItem(TOKEN_KEY);
        removerCookieSessao();
        atualizarStatusToken();
        ativarTela("login", true, true);
        setFeedback(loginFeedback, "Sessao expirada ou sem permissao. Faca login novamente.", "erro");
        return;
      }
      throw new Error(data.detail || "Falha no upload.");
    }

    setFeedback(uploadFeedback, `Upload concluido: ${data.nome_arquivo}`, "ok");
    uploadForm.reset();
  } catch (erro) {
    setFeedback(uploadFeedback, erro.message, "erro");
  }
});

function escaparHtml(valor) {
  return String(valor ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function moeda(valor) {
  if (valor === null || valor === undefined || valor === "") return "N/D";
  return Number(valor).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function renderizarPainelAdmin(data) {
  const u = data.usuarios;
  const c = data.catalogo;
  const a = data.auditoria;
  const cards = [
    ["Usuários ativos", u.ativos],
    ["Administradores", u.admins],
    ["Analistas", u.analistas],
    ["Veículos ativos", c.veiculos_ativos],
    ["Métricas", c.metricas],
    ["Logs de auditoria", a.logs],
    ["Login sucesso", a.login_sucesso],
    ["Login falha", a.login_falha],
  ];
  adminMetrics.innerHTML = cards.map(([titulo, valor]) => `<article class="metric-card"><span>${escaparHtml(titulo)}</span><strong>${escaparHtml(valor)}</strong></article>`).join("");

  const grupos = {
    "Pipeline DevSecOps": data.sprint3.pipeline_devsecops,
    "Segurança em código e infraestrutura": data.sprint3.seguranca_codigo_infra,
    "Observabilidade e resposta": data.sprint3.observabilidade,
    "Compliance e segurança contínua": data.sprint3.compliance,
  };
  sprint3Cards.innerHTML = Object.entries(grupos).map(([titulo, itens]) => `
    <article class="sprint3-card"><h4>${escaparHtml(titulo)}</h4>${itens.map(item => `<div class="check-row"><span>${escaparHtml(item.item)}</span><small>${escaparHtml(item.status)}${item.quantidade !== undefined ? ` · ${escaparHtml(item.quantidade)} registros` : ""}</small></div>`).join("")}</article>
  `).join("");
}

function renderizarUsuariosAdmin(usuarios) {
  if (!adminUsersList) return;
  if (!usuarios.length) {
    adminUsersList.innerHTML = '<p class="helper">Nenhum usuario cadastrado.</p>';
    return;
  }
  adminUsersList.innerHTML = `
    <div class="admin-user-table">
      ${usuarios.map((u) => `
        <div class="admin-user-row">
          <div><strong>${escaparHtml(u.nome)}</strong><small>${escaparHtml(u.email)} · ID ${escaparHtml(u.id)}</small></div>
          <select data-user-role="${u.id}">
            ${["user", "analista", "admin"].map(role => `<option value="${role}" ${u.role === role ? "selected" : ""}>${role}</option>`).join("")}
          </select>
          <span class="user-status ${u.status ? "active" : "inactive"}">${u.status ? "ativo" : "inativo"}</span>
          <button type="button" class="secondary-btn" data-reset-user="${u.id}">Gerar redefinição</button>
        </div>
      `).join("")}
    </div>`;
}

async function carregarUsuariosAdmin() {
  if (!adminUsersList || !tokenAtual() || roleAtual() !== "admin") return;
  const resposta = await fetch(`${API_BASE}/admin/usuarios`, { headers: { Authorization: `Bearer ${tokenAtual()}` } });
  const data = await resposta.json().catch(() => ({}));
  if (!resposta.ok) throw new Error(data.detail || "Não foi possível carregar os usuários.");
  renderizarUsuariosAdmin(data.usuarios || []);
}

async function criarUsuarioAdmin(event) {
  event.preventDefault();
  if (!adminUserForm) return;
  adminUserFeedback.textContent = "Criando usuario sem armazenar senha em texto puro...";
  adminInviteResult.innerHTML = "";
  try {
    const data = await postJson(`${API_BASE}/admin/usuarios`, {
      nome: document.getElementById("admin-user-nome").value,
      email: document.getElementById("admin-user-email").value,
      role: document.getElementById("admin-user-role").value,
    }, tokenAtual());
    adminUserFeedback.className = "feedback ok";
    adminUserFeedback.textContent = `Usuario ${data.usuario.email} criado.`;
    adminInviteResult.innerHTML = `<div class="invite-box"><strong>Link de configuracao (copie agora):</strong><code>${escaparHtml(data.convite.url)}</code><small>Expira em ${escaparHtml(data.convite.expira_em)} e so pode ser usado uma vez. Em producao, envie por e-mail/servico de notificacao.</small></div>`;
    adminUserForm.reset();
    await carregarUsuariosAdmin();
  } catch (erro) {
    adminUserFeedback.className = "feedback erro";
    adminUserFeedback.textContent = erro.message;
  }
}

async function alterarRoleAdmin(userId, role) {
  const resposta = await fetch(`${API_BASE}/admin/usuarios/${encodeURIComponent(userId)}/role`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${tokenAtual()}` },
    body: JSON.stringify({ role }),
  });
  const data = await resposta.json().catch(() => ({}));
  if (!resposta.ok) throw new Error(data.detail || "Falha ao alterar role.");
  adminUserFeedback.className = "feedback ok";
  adminUserFeedback.textContent = `Role atualizada para ${data.role}.`;
}

async function gerarResetAdmin(userId) {
  const resposta = await fetch(`${API_BASE}/admin/usuarios/${encodeURIComponent(userId)}/redefinir-senha`, {
    method: "POST",
    headers: { Authorization: `Bearer ${tokenAtual()}` },
  });
  const data = await resposta.json().catch(() => ({}));
  if (!resposta.ok) throw new Error(data.detail || "Falha ao gerar redefinicao.");
  adminInviteResult.innerHTML = `<div class="invite-box"><strong>Link de redefinicao para ${escaparHtml(data.email)}:</strong><code>${escaparHtml(data.reset.url)}</code><small>Expira em ${escaparHtml(data.reset.expira_em)} e invalida o token anterior. O token bruto nao fica no banco.</small></div>`;
}

async function carregarPainelAdmin() {
  if (!tokenAtual() || roleAtual() !== "admin") return;
  adminStatus.textContent = "Carregando indicadores...";
  try {
    const resposta = await fetch(`${API_BASE}/admin/dashboard`, {
      headers: { Authorization: `Bearer ${tokenAtual()}` },
    });
    const data = await resposta.json().catch(() => ({}));
    if (!resposta.ok) throw new Error(data.detail || "Não foi possível carregar o painel administrativo.");
    renderizarPainelAdmin(data);
    await carregarUsuariosAdmin();
    adminStatus.textContent = `Atualizado.`;
  } catch (erro) {
    adminStatus.textContent = erro.message;
  }
}

async function compararVeiculosAdmin() {
  const idA = document.getElementById("compare-id-a").value;
  const idB = document.getElementById("compare-id-b").value;
  compareResult.innerHTML = "";
  if (!idA || !idB) {
    compareResult.innerHTML = '<p class="feedback erro">Informe os dois IDs.</p>';
    return;
  }
  compareResult.innerHTML = '<p class="helper">Consultando o banco...</p>';
  try {
    const resposta = await fetch(`${API_BASE}/admin/comparacoes/veiculos?veiculo_id_a=${encodeURIComponent(idA)}&veiculo_id_b=${encodeURIComponent(idB)}`, {
      headers: { Authorization: `Bearer ${tokenAtual()}` },
    });
    const data = await resposta.json().catch(() => ({}));
    if (!resposta.ok) throw new Error(data.detail || "Falha na comparação.");
    const a = data.veiculo_a;
    const b = data.veiculo_b;
    const campos = [
      ["Marca / modelo / versão", `${a.marca} ${a.modelo} ${a.versao}`, `${b.marca} ${b.modelo} ${b.versao}`],
      ["Motorização", a.motorizacao, b.motorizacao],
      ["Potência (cv)", a.potencia_cv, b.potencia_cv],
      ["Transmissão", a.transmissao, b.transmissao],
      ["Tração", a.tracao, b.tracao],
      ["Preço sugerido", moeda(a.preco_sugerido), moeda(b.preco_sugerido)],
      ["Equipamentos", Object.keys(a.pacote_equipamentos || {}).length, Object.keys(b.pacote_equipamentos || {}).length],
    ];
    compareResult.innerHTML = `
      <div class="compare-title"><strong>${escaparHtml(a.marca)} ${escaparHtml(a.modelo)} #${a.id}</strong><span>vs.</span><strong>${escaparHtml(b.marca)} ${escaparHtml(b.modelo)} #${b.id}</strong></div>
      <div class="compare-table">${campos.map(([campo, va, vb]) => `<div class="compare-row"><span>${escaparHtml(campo)}</span><strong>${escaparHtml(va)}</strong><strong>${escaparHtml(vb)}</strong></div>`).join("")}</div>
      <p class="helper">Diferenças: potência ${escaparHtml(data.diferencas_numericas.potencia_cv.diferenca ?? "N/D")} cv · preço ${data.diferencas_numericas.preco_sugerido.diferenca === null ? "N/D" : moeda(data.diferencas_numericas.preco_sugerido.diferenca)}.</p>
    `;
  } catch (erro) {
    compareResult.innerHTML = `<p class="feedback erro">${escaparHtml(erro.message)}</p>`;
  }
}

if (adminRefreshBtn) adminRefreshBtn.addEventListener("click", carregarPainelAdmin);
if (compareBtn) compareBtn.addEventListener("click", compararVeiculosAdmin);

if (adminUserForm) adminUserForm.addEventListener("submit", criarUsuarioAdmin);
if (adminUsersList) adminUsersList.addEventListener("change", async (event) => {
  const select = event.target.closest("[data-user-role]");
  if (!select) return;
  try { await alterarRoleAdmin(select.dataset.userRole, select.value); }
  catch (erro) { adminUserFeedback.className = "feedback erro"; adminUserFeedback.textContent = erro.message; await carregarUsuariosAdmin(); }
});
if (adminUsersList) adminUsersList.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-reset-user]");
  if (!button) return;
  try { await gerarResetAdmin(button.dataset.resetUser); }
  catch (erro) { adminUserFeedback.className = "feedback erro"; adminUserFeedback.textContent = erro.message; }
});

if (resetPasswordForm) resetPasswordForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const password = document.getElementById("reset-password").value;
  const confirm = document.getElementById("reset-password-confirm").value;
  if (password !== confirm) {
    resetFeedback.className = "feedback erro";
    resetFeedback.textContent = "As senhas nao conferem.";
    return;
  }
  try {
    const data = await postJson(`${API_BASE}/auth/password/reset`, { token: resetTokenFromUrl, password });
    resetFeedback.className = "feedback ok";
    resetFeedback.textContent = `${data.mensagem} Redirecionando para o login...`;
    history.replaceState(null, "", "/login");
    setTimeout(() => ativarTela("login", false), 900);
  } catch (erro) {
    resetFeedback.className = "feedback erro";
    resetFeedback.textContent = erro.message;
  }
});

function efetuarLogout() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ROLE_KEY);
  removerCookieSessao();
  atualizarStatusToken();
  ativarTela("login", true, true);
}

navLogoutBtn.addEventListener("click", () => {
  limparFeedbacks();
  efetuarLogout();
});

window.addEventListener("popstate", () => {
  ativarTela(telaDaRotaAtual(), false);
});

atualizarStatusToken();
ativarTela(telaDaRotaAtual(), true, true);
document.body.classList.remove("auth-pending");

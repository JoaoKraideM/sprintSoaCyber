const API_BASE = "/api/v1";
const TOKEN_KEY = "ica_access_token";
const VALID_SCREENS = ["login", "registro", "upload"];
const SCREEN_ROUTES = {
  login: "/login",
  registro: "/registro",
  upload: "/enviar-arquivo",
};
const ROUTE_SCREENS = {
  "/": "login",
  "/login": "login",
  "/registro": "registro",
  "/enviar-arquivo": "upload",
  "/upload": "upload",
};

const registerForm = document.getElementById("form-register");
const loginForm = document.getElementById("form-login");
const uploadForm = document.getElementById("form-upload");
const navLogoutBtn = document.getElementById("nav-logout-btn");

const registerFeedback = document.getElementById("register-feedback");
const loginFeedback = document.getElementById("login-feedback");
const uploadFeedback = document.getElementById("upload-feedback");
const tokenStatus = document.getElementById("token-status");
const statusDot = document.getElementById("status-dot");
const routeLinks = document.querySelectorAll("[data-screen-target]");
const navButtons = document.querySelectorAll(".screen-nav [data-screen-target]");
const authStateItems = document.querySelectorAll("[data-auth-state]");
const screens = document.querySelectorAll(".screen");

function tokenAtual() {
  return localStorage.getItem(TOKEN_KEY);
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
  tokenStatus.textContent = token ? "Token JWT ativo." : "Sem token ativo.";
  statusDot.classList.toggle("online", autenticado);

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
}

function telaDaRotaAtual() {
  return ROUTE_SCREENS[window.location.pathname] || "login";
}

function ativarTela(nomeTela, atualizarRota = true, substituirRota = false) {
  const telaValida = VALID_SCREENS.includes(nomeTela) ? nomeTela : "login";
  const telaPermitida = telaValida !== "upload" || Boolean(tokenAtual());
  const telaFinal = telaPermitida ? telaValida : "login";

  screens.forEach((screen) => {
    const ativa = screen.id === `screen-${telaFinal}`;
    screen.hidden = !ativa;
    screen.classList.toggle("active", ativa);
  });

  navButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.screenTarget === telaFinal);
  });

  if (atualizarRota && window.location.pathname !== SCREEN_ROUTES[telaFinal]) {
    const metodoHistorico = substituirRota ? "replaceState" : "pushState";
    history[metodoHistorico](null, "", SCREEN_ROUTES[telaFinal]);
  }

  if (!telaPermitida) {
    setFeedback(loginFeedback, "Entre para liberar o envio de arquivos.", "erro");
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

function efetuarLogout() {
  localStorage.removeItem(TOKEN_KEY);
  removerCookieSessao();
  atualizarStatusToken();
  ativarTela("login", true, true);
  setFeedback(loginFeedback, "Sessao removida.", "ok");
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

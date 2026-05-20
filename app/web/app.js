const API_BASE = "/api/v1";
const TOKEN_KEY = "ica_access_token";

const registerForm = document.getElementById("form-register");
const loginForm = document.getElementById("form-login");
const uploadForm = document.getElementById("form-upload");
const logoutBtn = document.getElementById("logout-btn");

const registerFeedback = document.getElementById("register-feedback");
const loginFeedback = document.getElementById("login-feedback");
const uploadFeedback = document.getElementById("upload-feedback");
const tokenStatus = document.getElementById("token-status");

function tokenAtual() {
  return localStorage.getItem(TOKEN_KEY);
}

function setFeedback(el, mensagem, tipo = "ok") {
  el.textContent = mensagem;
  el.classList.remove("ok", "erro");
  el.classList.add(tipo);
}

function atualizarStatusToken() {
  const token = tokenAtual();
  if (!token) {
    tokenStatus.textContent = "Sem token ativo.";
    return;
  }

  tokenStatus.textContent = "Token JWT ativo na sessao do navegador.";
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
    setFeedback(loginFeedback, `Login realizado para ${data.email}.`, "ok");
    loginForm.reset();
    atualizarStatusToken();
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
      throw new Error(data.detail || "Falha no upload.");
    }

    setFeedback(uploadFeedback, `Upload concluido: ${data.nome_arquivo}`, "ok");
    uploadForm.reset();
  } catch (erro) {
    setFeedback(uploadFeedback, erro.message, "erro");
  }
});

logoutBtn.addEventListener("click", () => {
  localStorage.removeItem(TOKEN_KEY);
  atualizarStatusToken();
  setFeedback(loginFeedback, "Sessao removida.", "ok");
});

atualizarStatusToken();

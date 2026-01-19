const apiBase = "http://localhost:8000";

const domainSelect = document.getElementById("domain");
const docList = document.getElementById("doc-list");
const docTitle = document.getElementById("doc-title");
const docDesc = document.getElementById("doc-desc");
const docFrame = document.getElementById("doc-frame");
const docImage = document.getElementById("doc-image");
const docPlaceholder = document.getElementById("doc-placeholder");

const state = {
  documents: [],
};

function resetViewer() {
  docFrame.classList.add("hidden");
  docImage.classList.add("hidden");
  docPlaceholder.classList.remove("hidden");
  docTitle.textContent = "选择一篇文档";
  docDesc.textContent = "";
}

function showDocument(doc) {
  docTitle.textContent = doc.title;
  docDesc.textContent = doc.description || "";
  docPlaceholder.classList.add("hidden");

  const fileUrl = `${apiBase}/files/${doc.id}`;
  if (["png", "jpg", "jpeg", "gif", "webp"].includes(doc.file_type)) {
    docFrame.classList.add("hidden");
    docImage.src = fileUrl;
    docImage.classList.remove("hidden");
  } else {
    docImage.classList.add("hidden");
    docFrame.src = fileUrl;
    docFrame.classList.remove("hidden");
  }
}

function renderDomains(documents) {
  const domains = Array.from(new Set(documents.map((doc) => doc.domain)));
  domainSelect.innerHTML = '<option value="">全部</option>';
  domains.forEach((domain) => {
    const option = document.createElement("option");
    option.value = domain;
    option.textContent = domain;
    domainSelect.appendChild(option);
  });
}

function renderList(documents) {
  docList.innerHTML = "";
  if (!documents.length) {
    const empty = document.createElement("li");
    empty.textContent = "暂无内容";
    docList.appendChild(empty);
    resetViewer();
    return;
  }
  documents.forEach((doc) => {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = doc.title;
    button.addEventListener("click", () => showDocument(doc));
    item.appendChild(button);
    docList.appendChild(item);
  });
  showDocument(documents[0]);
}

async function fetchDocuments(domain = "") {
  const url = new URL(`${apiBase}/documents`);
  if (domain) {
    url.searchParams.set("domain", domain);
  }
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error("无法获取文档列表");
  }
  return response.json();
}

async function init() {
  try {
    state.documents = await fetchDocuments();
    renderDomains(state.documents);
    renderList(state.documents);
  } catch (error) {
    docList.innerHTML = "<li>加载失败，请检查接口</li>";
    resetViewer();
  }
}

domainSelect.addEventListener("change", async (event) => {
  const domain = event.target.value;
  const docs = await fetchDocuments(domain);
  renderList(docs);
});

init();

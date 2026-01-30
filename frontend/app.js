const apiBase = "http://localhost:8000";

const domainToggle = document.getElementById("domain-toggle");
const domainPanel = document.getElementById("domain-panel");
const domainList = document.getElementById("domain-list");
const domainCurrent = document.getElementById("domain-current");

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
  const domains = Array.from(new Set(documents.map((doc) => doc.domain))).filter(Boolean);

  // 清空列表
  domainList.innerHTML = "";

  // 先放“全部”
  const allBtn = document.createElement("button");
  allBtn.type = "button";
  allBtn.className = "domain-item active"; // 默认选中“全部”
  allBtn.dataset.value = "";
  allBtn.textContent = "全部";
  domainList.appendChild(allBtn);

  // 再放其他领域
  domains.forEach((domain) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "domain-item";
    btn.dataset.value = domain;
    btn.textContent = domain;
    domainList.appendChild(btn);
  });

  domainCurrent.textContent = "全部";
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

// 折叠开关
domainToggle.addEventListener("click", () => {
  const expanded = domainToggle.getAttribute("aria-expanded") === "true";
  domainToggle.setAttribute("aria-expanded", String(!expanded));
  domainPanel.hidden = expanded;
});

// 点击某个领域进行过滤
domainList.addEventListener("click", async (e) => {
  const btn = e.target.closest(".domain-item");
  if (!btn) return;

  const domain = btn.dataset.value || "";

  // UI 高亮
  domainList.querySelectorAll(".domain-item").forEach((el) => el.classList.remove("active"));
  btn.classList.add("active");
  domainCurrent.textContent = btn.textContent;

  // 收起面板
  domainToggle.setAttribute("aria-expanded", "false");
  domainPanel.hidden = true;

  // 拉取并渲染
  try {
    const docs = await fetchDocuments(domain);
    renderList(docs);
  } catch (err) {
    docList.innerHTML = "<li>加载失败，请检查接口</li>";
    resetViewer();
  }
});


init();


(() => {
  const content = document.querySelector(".content");
  const canvas = document.getElementById("sprout-canvas");
  if (!content || !canvas) return;

  const ctx = canvas.getContext("2d");
  let dpr = Math.max(1, window.devicePixelRatio || 1);
  let rafId = null;

  const ripples = [];

  function resize() {
    const r = content.getBoundingClientRect();
    dpr = Math.max(1, window.devicePixelRatio || 1);
    canvas.width = Math.floor(r.width * dpr);
    canvas.height = Math.floor(r.height * dpr);
    canvas.style.width = r.width + "px";
    canvas.style.height = r.height + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  resize();
  window.addEventListener("resize", resize);

  const now = () => performance.now();
  const clamp01 = (t) => Math.max(0, Math.min(1, t));
  const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);

  // 多频“伪噪声”（不用库也能像流体）
  function fbm(a, tt, seed) {
    // a: angle, tt: time(s)
    // 低频起伏 + 中频波纹 + 高频细碎
    const n1 = Math.sin(a * 2.0 + tt * 1.6 + seed) * 0.60;
    const n2 = Math.sin(a * 5.3 - tt * 2.3 + seed * 1.7) * 0.28;
    const n3 = Math.sin(a * 11.7 + tt * 4.6 - seed * 2.2) * 0.12;
    return n1 + n2 + n3; // roughly [-1,1]
  }

  function addRipple(x, y) {
    const count = 260 + (Math.random() * 160 | 0);

    const pts = Array.from({ length: count }, (_, i) => {
      const a = (i / count) * Math.PI * 2;
      return {
        a,
        // 断裂感（离散粒子线）
        skip: Math.random() < 0.08,
        // 粒子大小更细
        w: 0.55 + Math.random() * 0.65,
        // 每点的相位/随机性
        phase: Math.random() * Math.PI * 2,
        jitter: (Math.random() * 2 - 1),
        // 每点一个小“角速度”差，让圆周像在流动
        drift: (Math.random() * 2 - 1) * 0.10
      };
    });

    ripples.push({
      x, y,
      t0: now(),
      life: 3200 + Math.random() * 500,
      r0: 6 + Math.random() * 10,
      r1: 10 + Math.random() * 160,
      pts,
      rings: Math.random() < 0.55 ? 2 : 1,
      color: [31, 142, 158],

      // 流体参数（每个涟漪都不一样）
      seed: Math.random() * 1000,
      // 起伏幅度（px）
      amp0: 3 + Math.random() * 8,
      // 起伏随时间衰减速度
      ampDecay: 0.85 + Math.random() * 0.10,
      // 波纹“卷曲”强度（越大越流体）
      curl: 0.9 + Math.random() * 0.8
    });

    if (!rafId) rafId = requestAnimationFrame(tick);
  }

  function drawRipple(rp, p, tSec) {
    const e = easeOutCubic(p);
    const radius = rp.r0 + (rp.r1 - rp.r0) * e;

    // 透明度：更克制更高级（你要更明显就把 0.16 提到 0.22）
    const A = 0.16 * (1 - p);

    // 流体起伏幅度：开始大、后面衰减
    const amp = rp.amp0 * Math.pow((1 - p), rp.ampDecay);

    ctx.save();
    ctx.translate(rp.x, rp.y);

    for (let ring = 0; ring < rp.rings; ring++) {
      const ringScale = ring === 0 ? 1 : 1.24;
      const ringFade = ring === 0 ? 1 : 0.55;
      const rrBase = radius * ringScale;

      for (const pt of rp.pts) {
        if (pt.skip && ring === 0) continue;

        // 角度随时间发生轻微“漂移”，像水面流动
        const a = pt.a + (pt.drift * (1 - p)) * (tSec * 1.2);

        // 伪噪声：让圆周不规则起伏（流体感来源）
        const n = fbm(a, tSec, rp.seed);

        // 叠加“卷曲”：不同角度的起伏速度不同
        const curl = Math.sin(a * 1.7 + tSec * (1.6 + rp.curl)) * 0.35;

        // 半径扰动（单位 px）
        const wob = (n + curl) * amp;

        // 再加一点细碎“颗粒抖动”，但很小
        const micro = Math.sin(pt.phase + tSec * 9.0) * (0.8 + pt.jitter) * (1 - p) * 1.2;

        const r2 = rrBase + wob + micro;

        const x = Math.cos(a) * r2;
        const y = Math.sin(a) * r2;

        // 点透明度：沿圆周也有轻微闪烁/呼吸（粒子线更活）
        const aLocal = A * ringFade * (0.55 + 0.45 * Math.sin(pt.phase + tSec * 7.5));
        if (aLocal <= 0.002) continue;

        ctx.beginPath();
        ctx.arc(x, y, pt.w, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${rp.color[0]},${rp.color[1]},${rp.color[2]},${aLocal})`;
        ctx.fill();
      }
    }

    // 中心点（非常克制）
    const dotA = 0.07 * (1 - p);
    if (dotA > 0) {
      ctx.beginPath();
      ctx.arc(0, 0, 1.2, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${rp.color[0]},${rp.color[1]},${rp.color[2]},${dotA})`;
      ctx.fill();
    }

    ctx.restore();
  }

  function tick() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const t = now();
    const tSec = t / 1000;

    for (let i = ripples.length - 1; i >= 0; i--) {
      const rp = ripples[i];
      const p = clamp01((t - rp.t0) / rp.life);
      drawRipple(rp, p, tSec);
      if (p >= 1) ripples.splice(i, 1);
    }

    if (ripples.length) rafId = requestAnimationFrame(tick);
    else { cancelAnimationFrame(rafId); rafId = null; }
  }

  content.addEventListener("click", (e) => {
    const r = content.getBoundingClientRect();
    const x = e.clientX - r.left;
    const y = e.clientY - r.top;

    // 不想在 viewer 区域触发就取消注释：
    // if (e.target.closest(".viewer")) return;

    addRipple(x, y);
    // 第二圈稍延迟，像“二次波”
    setTimeout(() => addRipple(x, y), 85);
  });
})();




(function () {
  const fab = document.getElementById("chat-fab");
  const panel = document.getElementById("chat-panel");
  const closeBtn = document.getElementById("chat-close");
  const messages = document.getElementById("chat-messages");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const sendBtn = form.querySelector(".imsg-send-btn");
  const customerNameInput = document.getElementById("chat-customer-name");
  const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

  const CONDITION_LABELS = {
    quantity: "수량",
    budget_per_person: "1인당 예산",
    purpose: "목적",
    industry: "업종",
    preferred_products: "선호 상품",
    delivery_days: "납기",
    referenced_company: "지정 고객사",
  };

  function openPanel() {
    panel.classList.add("open");
    panel.setAttribute("aria-hidden", "false");
    input.focus();
  }

  function closePanel() {
    panel.classList.remove("open");
    panel.setAttribute("aria-hidden", "true");
  }

  fab.addEventListener("click", openPanel);
  closeBtn.addEventListener("click", closePanel);

  function updateSendState() {
    sendBtn.classList.toggle("is-active", input.value.trim().length > 0);
  }
  input.addEventListener("input", updateSendState);
  updateSendState();

  function scrollToBottom() {
    messages.scrollTop = messages.scrollHeight;
  }

  function formatTime() {
    return new Intl.DateTimeFormat("ko-KR", { hour: "numeric", minute: "2-digit", hour12: true }).format(new Date());
  }

  function addRow(bubbleEl, side) {
    const row = document.createElement("div");
    row.className = `imsg-row imsg-row--${side}`;
    row.appendChild(bubbleEl);
    const time = document.createElement("div");
    time.className = "imsg-timestamp";
    time.textContent = formatTime();
    row.appendChild(time);
    messages.appendChild(row);
    scrollToBottom();
    return row;
  }

  function addUserMessage(text) {
    const bubble = document.createElement("div");
    bubble.className = "imsg-bubble imsg-bubble--sent";
    bubble.textContent = text;
    addRow(bubble, "sent");
  }

  function addTypingIndicator() {
    const bubble = document.createElement("div");
    bubble.className = "imsg-bubble imsg-bubble--received imsg-typing";
    bubble.innerHTML = `<span class="imsg-dot"></span><span class="imsg-dot"></span><span class="imsg-dot"></span>`;
    return addRow(bubble, "received");
  }

  function addPlainMessage(text) {
    const bubble = document.createElement("div");
    bubble.className = "imsg-bubble imsg-bubble--received";
    bubble.textContent = text;
    addRow(bubble, "received");
  }

  function formatConditionValue(key, value) {
    if (Array.isArray(value)) return value.join(", ");
    if (key === "budget_per_person") return Number(value).toLocaleString() + "원";
    return value;
  }

  function buildConditionChips(conditions) {
    const wrap = document.createElement("div");
    wrap.className = "chat-conditions";
    Object.entries(conditions).forEach(([key, value]) => {
      if (!value || (Array.isArray(value) && value.length === 0)) return;
      const chip = document.createElement("span");
      chip.className = "chat-condition-chip";
      chip.textContent = `${CONDITION_LABELS[key] || key}: ${formatConditionValue(key, value)}`;
      wrap.appendChild(chip);
    });
    return wrap;
  }

  function buildHistoryCard(order) {
    const card = document.createElement("div");
    card.className = "history-card";
    const img = order.products[0] && order.products[0].image_url
      ? order.products[0].image_url
      : "/static/uploads/products/placeholder.svg";
    const logo = order.company_logo || "/static/uploads/products/placeholder.svg";
    const productNames = order.products.map((p) => p.name).join(" / ");
    card.innerHTML = `
      <img class="history-card-thumb" src="${img}" alt="">
      <div class="history-card-body">
        <div class="history-card-title">
          <span class="history-card-company">
            <img class="history-card-logo" src="${logo}" alt="">
            ${order.company_name || "-"}
          </span>
          <span class="history-similarity">${order.similarity != null ? order.similarity + "%" : ""}</span>
        </div>
        <div class="history-card-row">${order.purpose || "-"} · ${order.quantity ?? "-"}명</div>
        <div class="history-card-row">단가 ${Number(order.price_per_person || 0).toLocaleString()}원 · 만족도 ${order.satisfaction_score ?? "-"}</div>
        <div class="history-card-row">${productNames}</div>
        <a class="history-card-link" href="/admin/history/${order.id}" target="_blank">상세보기</a>
      </div>
    `;
    return card;
  }

  function buildRecommendationBlock(recommendation, context) {
    const block = document.createElement("div");
    block.className = "reco-block";

    const title = document.createElement("div");
    title.className = "reco-title";
    title.textContent = "AI 추천";
    block.appendChild(title);

    const text = document.createElement("div");
    text.className = "reco-text";
    text.textContent = recommendation.ai_text || "";
    block.appendChild(text);

    if (recommendation.products && recommendation.products.length) {
      const tags = document.createElement("div");
      tags.className = "reco-tags";
      recommendation.products.forEach((p) => {
        const tag = document.createElement("span");
        tag.className = "reco-tag";
        tag.textContent = p;
        tags.appendChild(tag);
      });
      block.appendChild(tags);
    }

    if (recommendation.suggestions && recommendation.suggestions.length) {
      const ul = document.createElement("ul");
      ul.className = "reco-suggestions";
      recommendation.suggestions.forEach((s) => {
        const li = document.createElement("li");
        li.textContent = s;
        ul.appendChild(li);
      });
      block.appendChild(ul);
    }

    if (recommendation.ai_text) {
      const actions = document.createElement("div");
      actions.className = "reco-actions";

      const editBtn = document.createElement("button");
      editBtn.type = "button";
      editBtn.textContent = "수정하기";

      const saveBtn = document.createElement("button");
      saveBtn.type = "button";
      saveBtn.className = "save-btn";
      saveBtn.textContent = "최종 제안 저장";

      const textarea = document.createElement("textarea");
      textarea.className = "reco-edit-area";
      textarea.style.display = "none";
      textarea.value = recommendation.ai_text;

      editBtn.addEventListener("click", () => {
        textarea.style.display = textarea.style.display === "none" ? "block" : "none";
      });

      const downloadLink = document.createElement("a");
      downloadLink.className = "reco-download-link";
      downloadLink.textContent = "📄 제안서 다운로드 (.docx)";
      downloadLink.style.display = "none";
      downloadLink.target = "_blank";

      saveBtn.addEventListener("click", async () => {
        saveBtn.disabled = true;
        saveBtn.textContent = "저장 중...";
        try {
          const res = await fetch("/api/proposals", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
            body: JSON.stringify({
              request_text: context.message,
              ai_proposal: recommendation.ai_text,
              final_proposal: textarea.value || recommendation.ai_text,
              customer_name: customerNameInput.value.trim(),
              products: recommendation.products || [],
              expected_price: recommendation.expected_price || "",
              references: (context.similarHistories || []).map((o) => ({
                company_name: o.company_name,
                quantity: o.quantity,
                price_per_person: o.price_per_person,
                satisfaction_score: o.satisfaction_score,
                similarity: o.similarity,
              })),
            }),
          });
          if (!res.ok) throw new Error("save failed");
          const data = await res.json();
          saveBtn.textContent = "저장됨 ✓";
          if (data.download_url) {
            downloadLink.href = data.download_url;
            downloadLink.style.display = "inline-block";
          }
        } catch (e) {
          saveBtn.textContent = "저장 실패, 다시 시도";
          saveBtn.disabled = false;
        }
      });

      actions.appendChild(editBtn);
      actions.appendChild(saveBtn);
      actions.appendChild(downloadLink);
      block.appendChild(actions);
      block.appendChild(textarea);
    }

    return block;
  }

  function addAssistantResult(data, contextMessage) {
    const card = document.createElement("div");
    card.className = "imsg-card";

    const analysisTitle = document.createElement("div");
    analysisTitle.className = "imsg-card-title";
    analysisTitle.textContent = "고객 요청 분석";
    card.appendChild(analysisTitle);

    card.appendChild(buildConditionChips(data.parsed_conditions || {}));

    if (data.similar_histories && data.similar_histories.length) {
      const p = document.createElement("p");
      p.className = "imsg-card-note";
      p.textContent = `유사 사례 ${data.similar_histories.length}건을 찾았습니다.`;
      card.appendChild(p);
      data.similar_histories.forEach((order) => card.appendChild(buildHistoryCard(order)));
    } else {
      const p = document.createElement("p");
      p.className = "imsg-card-note";
      p.textContent = "조건에 맞는 과거 사례를 찾지 못했습니다.";
      card.appendChild(p);
    }

    if (data.recommendation) {
      card.appendChild(
        buildRecommendationBlock(data.recommendation, {
          message: contextMessage,
          similarHistories: data.similar_histories || [],
        })
      );
    }

    addRow(card, "received");
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (!message) return;

    addUserMessage(message);
    input.value = "";
    updateSendState();
    const loadingRow = addTypingIndicator();

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
        body: JSON.stringify({ message }),
      });
      loadingRow.remove();
      if (!res.ok) {
        addPlainMessage("요청 처리 중 오류가 발생했습니다. 다시 시도해주세요.");
        return;
      }
      const data = await res.json();
      addAssistantResult(data, message);
    } catch (err) {
      loadingRow.remove();
      addPlainMessage("서버에 연결할 수 없습니다.");
    }
  });
})();

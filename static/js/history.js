(function () {
  document.querySelectorAll("tbody tr[data-href]").forEach((row) => {
    row.style.cursor = "pointer";
    row.addEventListener("click", (e) => {
      if (e.target.closest("a, button")) return;
      window.location.href = row.dataset.href;
    });
  });
})();

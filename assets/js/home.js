(() => {
  const root = document.documentElement;
  const toggle = document.querySelector(".theme-toggle");
  const toggleMark = document.querySelector(".theme-toggle-mark");
  const toggleLabel = document.querySelector(".theme-toggle-label");
  const searchInput = document.querySelector(".blog-search-input");
  const clearButton = document.querySelector(".search-clear");
  const posts = Array.from(document.querySelectorAll(".post-card"));
  const emptyState = document.querySelector(".search-empty");
  const storageKey = "equ-blog-theme";
  const progress = document.querySelector(".reading-progress");

  const readStoredTheme = () => {
    try {
      return localStorage.getItem(storageKey);
    } catch {
      return null;
    }
  };

  const storeTheme = (theme) => {
    try {
      localStorage.setItem(storageKey, theme);
    } catch {
      // Theme switching should still work if storage is unavailable.
    }
  };

  const paintThemeButton = (theme) => {
    const isDark = theme === "dark";
    toggle?.setAttribute("aria-pressed", String(isDark));
    if (toggleMark) {
      toggleMark.textContent = isDark ? "日" : "夜";
    }
    if (toggleLabel) {
      toggleLabel.textContent = isDark ? "日间" : "夜间";
    }
  };

  const setTheme = (theme) => {
    root.dataset.theme = theme;
    storeTheme(theme);
    paintThemeButton(theme);
  };

  const preferredTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  setTheme(readStoredTheme() || preferredTheme);

  toggle?.addEventListener("click", () => {
    setTheme(root.dataset.theme === "dark" ? "light" : "dark");
  });

  const applySearch = () => {
    const query = (searchInput?.value || "").trim().toLowerCase();
    let visibleCount = 0;

    posts.forEach((post) => {
      const haystack = `${post.dataset.search || ""} ${post.textContent || ""}`.toLowerCase();
      const isVisible = !query || haystack.includes(query);
      post.hidden = !isVisible;
      if (isVisible) {
        visibleCount += 1;
      }
    });

    if (clearButton) {
      clearButton.hidden = !query;
    }
    if (emptyState) {
      emptyState.hidden = !query || visibleCount > 0;
    }
  };

  searchInput?.addEventListener("input", applySearch);
  clearButton?.addEventListener("click", () => {
    if (searchInput) {
      searchInput.value = "";
      searchInput.focus();
    }
    applySearch();
  });

  const updateReadingProgress = () => {
    if (!progress || !document.querySelector(".reading-article")) {
      return;
    }
    const scrollable = document.documentElement.scrollHeight - window.innerHeight;
    const ratio = scrollable > 0 ? window.scrollY / scrollable : 0;
    progress.style.transform = `scaleX(${Math.max(0, Math.min(1, ratio))})`;
  };

  updateReadingProgress();
  window.addEventListener("scroll", updateReadingProgress, { passive: true });
  window.addEventListener("resize", updateReadingProgress);
})();

(() => {
  const storageKey = "equ-blog-theme";
  const root = document.documentElement;
  const toggle = document.querySelector(".theme-toggle");
  const toggleText = document.querySelector(".theme-toggle-text");
  const searchInput = document.querySelector("#post-search");
  const chips = Array.from(document.querySelectorAll("[data-filter]"));
  const filterLinks = Array.from(document.querySelectorAll("[data-filter-link]"));
  const posts = Array.from(document.querySelectorAll(".post-card"));
  const emptyState = document.querySelector("[data-empty-state]");

  const setTheme = (theme) => {
    root.dataset.theme = theme;
    localStorage.setItem(storageKey, theme);
    if (toggle) {
      const isDark = theme === "dark";
      toggle.setAttribute("aria-pressed", String(isDark));
      if (toggleText) {
        toggleText.textContent = isDark ? "日间" : "夜间";
      }
    }
  };

  const savedTheme = localStorage.getItem(storageKey);
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  setTheme(savedTheme || (prefersDark ? "dark" : "light"));

  toggle?.addEventListener("click", () => {
    setTheme(root.dataset.theme === "dark" ? "light" : "dark");
  });

  let activeFilter = "all";

  const clearSearch = () => {
    if (searchInput) {
      searchInput.value = "";
    }
  };

  const applyFilters = () => {
    const query = (searchInput?.value || "").trim().toLowerCase();
    let visibleCount = 0;

    posts.forEach((post) => {
      const tags = post.dataset.tags || "";
      const haystack = `${post.dataset.search || ""} ${post.textContent || ""}`.toLowerCase();
      const matchesFilter = activeFilter === "all" || tags.includes(activeFilter);
      const matchesQuery = !query || haystack.includes(query);
      const shouldShow = matchesFilter && matchesQuery;

      post.hidden = !shouldShow;
      if (shouldShow) {
        visibleCount += 1;
      }
    });

    if (emptyState) {
      emptyState.hidden = visibleCount !== 0;
    }
  };

  const setFilter = (filter) => {
    activeFilter = filter;
    chips.forEach((chip) => {
      chip.classList.toggle("is-active", chip.dataset.filter === filter);
    });
    applyFilters();
  };

  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      clearSearch();
      setFilter(chip.dataset.filter || "all");
    });
  });

  filterLinks.forEach((link) => {
    link.addEventListener("click", () => {
      clearSearch();
      setFilter(link.dataset.filterLink || "all");
    });
  });

  searchInput?.addEventListener("input", applyFilters);
})();

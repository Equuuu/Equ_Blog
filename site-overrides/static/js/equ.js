(() => {
  const root = document.documentElement;
  const toggle = document.querySelector(".theme-toggle");
  const toggleMark = document.querySelector(".theme-toggle-mark");
  const toggleLabel = document.querySelector(".theme-toggle-label");
  const searchInput = document.querySelector(".blog-search-input");
  const clearButton = document.querySelector(".search-clear");
  const posts = Array.from(document.querySelectorAll(".post-card"));
  const postGroups = Array.from(document.querySelectorAll(".post-group"));
  const emptyState = document.querySelector(".search-empty");
  const storageKey = "equ-blog-theme";
  const progress = document.querySelector(".reading-progress");
  const musicToggle = document.querySelector(".music-toggle");
  const musicStorageKey = "equ-blog-music";
  let musicAudio = null;

  postGroups.forEach((group) => {
    group.dataset.defaultOpen = String(group.open);
  });

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

  const setMusicState = (isPlaying) => {
    musicToggle?.setAttribute("aria-pressed", String(isPlaying));
    musicToggle?.setAttribute("aria-label", isPlaying ? "暂停巴赫音乐" : "播放巴赫音乐");
  };

  const storeMusicState = (isPlaying) => {
    try {
      localStorage.setItem(musicStorageKey, isPlaying ? "playing" : "paused");
    } catch {
      // Music playback should still work if storage is unavailable.
    }
  };

  const readStoredMusicState = () => {
    try {
      return localStorage.getItem(musicStorageKey);
    } catch {
      return null;
    }
  };

  const getMusicAudio = () => {
    const source = musicToggle?.dataset.musicSrc;
    if (!source) {
      return null;
    }
    if (!musicAudio) {
      musicAudio = new Audio(source);
      musicAudio.loop = true;
      musicAudio.preload = "none";
      musicAudio.volume = 0.26;
      musicAudio.addEventListener("play", () => setMusicState(true));
      musicAudio.addEventListener("pause", () => setMusicState(false));
      musicAudio.addEventListener("error", () => {
        setMusicState(false);
        storeMusicState(false);
      });
    }
    return musicAudio;
  };

  const playMusic = async (remember = true) => {
    const audio = getMusicAudio();
    if (!audio) {
      return;
    }
    try {
      setMusicState(true);
      await audio.play();
      setMusicState(true);
      if (remember) {
        storeMusicState(true);
      }
    } catch {
      setMusicState(false);
      if (remember) {
        storeMusicState(false);
      }
    }
  };

  const pauseMusic = () => {
    const audio = getMusicAudio();
    if (!audio) {
      return;
    }
    audio.pause();
    setMusicState(false);
    storeMusicState(false);
  };

  setMusicState(false);
  musicToggle?.addEventListener("click", () => {
    const audio = getMusicAudio();
    if (!audio) {
      return;
    }
    if (audio.paused) {
      playMusic(true);
    } else {
      pauseMusic();
    }
  });

  if (readStoredMusicState() === "playing") {
    playMusic(false);
  }

  const applySearch = () => {
    const query = (searchInput?.value || "").trim().toLowerCase();
    let visibleCount = 0;

    if (!query) {
      posts.forEach((post) => {
        post.hidden = false;
      });
      postGroups.forEach((group) => {
        group.hidden = false;
        group.open = group.dataset.defaultOpen === "true";
      });
      visibleCount = posts.length;
    } else if (postGroups.length) {
      postGroups.forEach((group) => {
        const groupPosts = Array.from(group.querySelectorAll(".post-card"));
        const groupHaystack = `${group.dataset.groupSearch || ""} ${
          group.querySelector(".post-group-summary")?.textContent || ""
        }`.toLowerCase();
        const groupMatches = groupHaystack.includes(query);
        let groupVisibleCount = 0;

        groupPosts.forEach((post) => {
          const haystack = `${post.dataset.search || ""} ${post.textContent || ""}`.toLowerCase();
          const isVisible = groupMatches || haystack.includes(query);
          post.hidden = !isVisible;
          if (isVisible) {
            groupVisibleCount += 1;
            visibleCount += 1;
          }
        });

        group.hidden = groupVisibleCount === 0;
        if (groupVisibleCount > 0) {
          group.open = true;
        }
      });
    } else {
      posts.forEach((post) => {
        const haystack = `${post.dataset.search || ""} ${post.textContent || ""}`.toLowerCase();
        const isVisible = haystack.includes(query);
        post.hidden = !isVisible;
        if (isVisible) {
          visibleCount += 1;
        }
      });
    }

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

(() => {
  const root = document.documentElement;
  const toggle = document.querySelector(".theme-toggle");
  const toggleLabel = document.querySelector(".theme-toggle-label");
  const searchInput = document.querySelector(".blog-search-input");
  const clearButton = document.querySelector(".search-clear");
  const posts = Array.from(document.querySelectorAll(".post-card"));
  const postGroups = Array.from(document.querySelectorAll(".post-group"));
  const emptyState = document.querySelector(".search-empty");
  const storageKey = "equ-blog-theme";
  const progress = document.querySelector(".reading-progress");
  const musicToggle = document.querySelector(".music-toggle");
  const musicLabel = document.querySelector(".music-toggle-label");
  const musicStorageKey = "equ-blog-music";
  const header = document.querySelector(".site-header");
  const backTop = document.querySelector(".back-top");
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
    if (toggle) {
      const label = isDark ? "切换到日间主题" : "切换到夜间主题";
      toggle.setAttribute("aria-label", label);
      toggle.setAttribute("title", label);
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

  // The biosphere night theme is designed dark-first.
  const themeOverride = new URLSearchParams(location.search).get("theme");
  setTheme(
    themeOverride === "light" || themeOverride === "dark"
      ? themeOverride
      : readStoredTheme() || "dark"
  );

  toggle?.addEventListener("click", () => {
    setTheme(root.dataset.theme === "dark" ? "light" : "dark");
  });

  const setMusicState = (isPlaying) => {
    const label = isPlaying ? "暂停巴赫音乐" : "播放巴赫音乐";
    musicToggle?.setAttribute("aria-pressed", String(isPlaying));
    musicToggle?.setAttribute("aria-label", label);
    musicToggle?.setAttribute("title", label);
    if (musicLabel) {
      musicLabel.textContent = label;
    }
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

  window.addEventListener("keydown", (event) => {
    if (
      event.key === "/" &&
      document.activeElement?.tagName !== "INPUT" &&
      document.activeElement?.tagName !== "TEXTAREA"
    ) {
      event.preventDefault();
      searchInput?.focus();
    }
  });

  /* Scroll-in reveal for the frosted panels */
  const sections = Array.from(document.querySelectorAll(".section-block"));
  sections.forEach((section, index) => {
    section.style.transitionDelay = `${Math.min(index * 90, 270)}ms`;
  });
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.08 }
    );
    sections.forEach((section) => observer.observe(section));
  } else {
    sections.forEach((section) => section.classList.add("is-visible"));
  }

  const updateReadingProgress = () => {
    if (!progress || !document.querySelector(".reading-article")) {
      return;
    }
    const scrollable = document.documentElement.scrollHeight - window.innerHeight;
    const ratio = scrollable > 0 ? window.scrollY / scrollable : 0;
    progress.style.transform = `scaleX(${Math.max(0, Math.min(1, ratio))})`;
  };

  /* Keep the photo zone aligned with the header bottom (homepage backdrop) */
  const syncBackdropTop = () => {
    if (!header || !document.querySelector(".depth")) {
      return;
    }
    const bottom = Math.max(0, Math.round(header.getBoundingClientRect().bottom));
    root.style.setProperty("--backdrop-top", `${bottom}px`);
  };

  let ticking = false;
  const paintScroll = () => {
    const y = window.scrollY;
    header?.classList.toggle("is-scrolled", y > 16);
    backTop?.classList.toggle("is-visible", y > 420);
    syncBackdropTop();
    updateReadingProgress();
    ticking = false;
  };

  const onScroll = () => {
    if (ticking) {
      return;
    }
    ticking = true;
    window.requestAnimationFrame(paintScroll);
  };

  paintScroll();
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", () => window.requestAnimationFrame(paintScroll), {
    passive: true,
  });
  backTop?.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  /* ------------------------------------------------------------
     Heavy rain + occasional distant lightning (canvas 2D)
     - three depth layers of chunky slanted droplets
     - fades out toward the lower part of the frame
     - pauses when the tab is hidden; skipped entirely for
       prefers-reduced-motion users
     ------------------------------------------------------------ */
  const rainCanvas = document.querySelector(".rain-layer");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (rainCanvas && !reduceMotion) {
    const ctx = rainCanvas.getContext("2d");
    const SLANT = Math.tan((6.5 * Math.PI) / 180); // gentle ~6.5° rain slant
    const LAYERS = [
      // far → near: chunky short droplets, wider and brighter up close
      { share: 0.45, speed: 215, length: 7, width: 1.0, alpha: 0.14 },
      { share: 0.35, speed: 330, length: 10, width: 1.7, alpha: 0.2 },
      { share: 0.2, speed: 460, length: 13, width: 2.7, alpha: 0.3 },
    ];
    let dpr = 1;
    let vw = 0;
    let vh = 0;
    let drops = [];
    let rafId = 0;
    let lastTs = 0;

    // ---- lightning: irregular rhythm, mixed weak/strong strikes ----
    let flashAt = 0; // timestamp of next strike
    let flash = null; // active strike descriptor
    const flashDebug = new URLSearchParams(location.search).get("flash");

    const scheduleFlash = (now, isFirst) => {
      if (isFirst && flashDebug) {
        flashAt = now + 1200; // debug: force an early strike
        return;
      }
      if (!isFirst && Math.random() < 0.35) {
        // occasional tight cluster of two or three strikes
        flashAt = now + 1200 + Math.random() * 2800;
        return;
      }
      // skewed 6–40 s: mostly shorter gaps, sometimes a long quiet spell
      flashAt = now + 6000 + Math.pow(Math.random(), 2.2) * 34000;
    };

    const buildFlash = (now) => {
      // 1 in 4 strikes is a strong one that briefly lights the sky
      const strong = flashDebug === "strong" && flash === null
        ? true
        : Math.random() < 0.25;
      const basePeak = strong
        ? 0.3 + Math.random() * 0.15
        : 0.07 + Math.random() * 0.07;
      const pulseCount = 1 + Math.floor(Math.random() * 3); // 1–3 pulses
      const pulses = [];
      let t0 = 0;
      for (let i = 0; i < pulseCount; i += 1) {
        pulses.push({
          t0,
          peak: basePeak * (i === 0 ? 1 : 0.35 + Math.random() * 0.35),
          rise: 30 + Math.random() * 30,
          fall: 90 + Math.random() * 110,
        });
        t0 += 180 + Math.random() * 420;
      }
      const last = pulses[pulses.length - 1];
      return {
        start: now,
        x: 0.15 + Math.random() * 0.7,
        strong,
        pulses,
        dur: last.t0 + last.rise + last.fall * 5,
      };
    };

    const spawnDrop = (layer, anywhere) => ({
      layer,
      x: Math.random() * (vw + vh * SLANT),
      y: anywhere ? Math.random() * vh : -LAYERS[layer].length - Math.random() * vh * 0.3,
      speed: LAYERS[layer].speed * (0.85 + Math.random() * 0.3),
      slant: SLANT * (0.85 + Math.random() * 0.3),
      len: LAYERS[layer].length * (0.85 + Math.random() * 0.3),
      phase: Math.random() * Math.PI * 2,
    });

    const rebuild = () => {
      vw = window.innerWidth;
      vh = window.innerHeight;
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      rainCanvas.width = Math.round(vw * dpr);
      rainCanvas.height = Math.round(vh * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.lineCap = "round";

      // fewer but chunkier drops: each one carries more presence
      const total = Math.min(560, Math.round((vw * vh) / 2900));
      drops = [];
      LAYERS.forEach((cfg, i) => {
        const count = Math.round(total * cfg.share);
        for (let k = 0; k < count; k += 1) {
          drops.push(spawnDrop(i, true));
        }
      });
    };

    // rain fades away below this band so the grass / panels stay calm
    const fadeFor = (y) => {
      const start = vh * 0.55;
      const end = vh * 0.92;
      if (y <= start) return 1;
      if (y >= end) return 0;
      return 1 - (y - start) / (end - start);
    };

    const pulseValue = (t, p) => {
      const local = t - p.t0;
      if (local < 0) return 0;
      if (local < p.rise) return (local / p.rise) * p.peak;
      return p.peak * Math.exp(-(local - p.rise) / p.fall);
    };

    const drawLightning = (now) => {
      if (!flash && now >= flashAt) {
        flash = buildFlash(now);
      }
      if (!flash) return;
      const elapsed = now - flash.start;
      if (elapsed > flash.dur) {
        flash = null;
        scheduleFlash(now, false);
        return;
      }
      let strength = 0;
      for (let i = 0; i < flash.pulses.length; i += 1) {
        strength += pulseValue(elapsed, flash.pulses[i]);
      }
      strength = Math.min(strength, 0.5);
      if (strength <= 0.002) return;

      const cx = vw * flash.x;
      const glow = ctx.createRadialGradient(cx, 0, 0, cx, 0, vh * (flash.strong ? 0.95 : 0.75));
      glow.addColorStop(0, `rgba(210, 227, 255, ${strength})`);
      glow.addColorStop(0.45, `rgba(195, 217, 250, ${strength * 0.45})`);
      glow.addColorStop(1, "rgba(195, 217, 250, 0)");
      ctx.fillStyle = glow;
      ctx.fillRect(0, 0, vw, vh * (flash.strong ? 0.9 : 0.8));

      // strong strikes also lift the whole frame, capped well below glare
      if (flash.strong) {
        const lift = Math.min(strength * 0.2, 0.09);
        if (lift > 0.003) {
          ctx.fillStyle = `rgba(205, 222, 250, ${lift})`;
          ctx.fillRect(0, 0, vw, vh);
        }
      }
    };

    const frame = (ts) => {
      rafId = window.requestAnimationFrame(frame);
      const dt = Math.min((ts - lastTs) / 1000 || 0.016, 0.05);
      lastTs = ts;
      ctx.clearRect(0, 0, vw, vh);

      for (let i = 0; i < drops.length; i += 1) {
        const d = drops[i];
        const cfg = LAYERS[d.layer];
        d.y += d.speed * dt;
        d.x -= d.speed * d.slant * dt;
        if (d.y - d.len > vh || d.x < -d.len) {
          drops[i] = spawnDrop(d.layer, false);
          continue;
        }
        // faint per-drop shimmer keeps the sheet of rain alive without sparkle
        const flicker = 0.85 + 0.15 * Math.sin(ts * 0.004 + d.phase);
        const a = cfg.alpha * flicker * fadeFor(d.y);
        if (a <= 0.004) continue;

        // droplet shape: thin trailing tail + heavier round leading head,
        // so each particle reads as a falling drop instead of a line
        const tipX = d.x;
        const tipY = d.y; // leading (bottom) end
        const tailX = d.x + d.len * d.slant;
        const tailY = d.y - d.len;
        const midX = tipX + (tailX - tipX) * 0.55;
        const midY = tipY + (tailY - tipY) * 0.55;

        ctx.strokeStyle = `rgba(190, 215, 245, ${a * 0.6})`;
        ctx.lineWidth = cfg.width * 0.5;
        ctx.beginPath();
        ctx.moveTo(midX, midY);
        ctx.lineTo(tailX, tailY);
        ctx.stroke();

        ctx.strokeStyle = `rgba(198, 221, 248, ${a})`;
        ctx.lineWidth = cfg.width;
        ctx.beginPath();
        ctx.moveTo(tipX, tipY);
        ctx.lineTo(midX, midY);
        ctx.stroke();
      }

      drawLightning(ts);
    };

    const start = () => {
      if (rafId) return;
      lastTs = performance.now();
      if (!flashAt) scheduleFlash(lastTs, true);
      rafId = window.requestAnimationFrame(frame);
    };

    const stop = () => {
      if (!rafId) return;
      window.cancelAnimationFrame(rafId);
      rafId = 0;
    };

    rebuild();
    start();
    window.addEventListener("resize", rebuild, { passive: true });
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        stop();
      } else {
        start();
      }
    });
  }
})();

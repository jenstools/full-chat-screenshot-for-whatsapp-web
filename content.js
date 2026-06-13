// Runs inside web.whatsapp.com. Drives the scroll-and-capture loop:
//  1. Find the scrollable message list inside the open chat.
//  2. Scroll to the very top, forcing WhatsApp to lazy-load the oldest messages.
//  3. Step downward, asking the background worker to capture + stitch the
//     newly revealed strip after each step (strip height == scroll delta,
//     so there is no overlap and no gap).
//  4. Tell background to finalize + download.

(() => {
  if (window.__waCapInit) return;
  window.__waCapInit = true;

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  let running = false;
  let cancelFlag = false;
  let overlayEl = null; // hidden during each capture so it isn't baked in

  // ---- on-page progress overlay -------------------------------------------
  function makeOverlay() {
    const wrap = document.createElement("div");
    wrap.style.cssText =
      "position:fixed;z-index:2147483647;right:16px;bottom:16px;width:300px;" +
      "background:#111b21;color:#e9edef;font:13px/1.4 system-ui,Segoe UI,Roboto,sans-serif;" +
      "border:1px solid #2a3942;border-radius:10px;box-shadow:0 8px 30px rgba(0,0,0,.5);padding:14px;";
    const title = document.createElement("div");
    title.textContent = "WhatsApp full-chat screenshot";
    title.style.cssText = "font-weight:600;margin-bottom:6px;color:#25d366;";
    const status = document.createElement("div");
    status.textContent = "Starting…";
    status.style.cssText = "margin-bottom:10px;white-space:pre-wrap;word-break:break-word;";
    const btn = document.createElement("button");
    btn.textContent = "Cancel";
    btn.style.cssText =
      "background:#2a3942;color:#e9edef;border:0;border-radius:6px;padding:6px 12px;cursor:pointer;";
    btn.onclick = () => {
      cancelFlag = true;
      status.textContent = "Cancelling…";
    };
    wrap.appendChild(title);
    wrap.appendChild(status);
    wrap.appendChild(btn);
    document.body.appendChild(wrap);
    overlayEl = wrap;

    return {
      set: (t) => {
        status.textContent = t;
      },
      done: (parts) => {
        status.textContent =
          "Done — saved " + parts + (parts > 1 ? " image parts." : " image.") + " Check your downloads.";
        btn.textContent = "Close";
        btn.onclick = () => wrap.remove();
        setTimeout(() => wrap.remove(), 8000);
      },
      fail: (msg) => {
        status.textContent = "Failed: " + msg;
        title.style.color = "#f15c6d";
        btn.textContent = "Close";
        btn.onclick = () => wrap.remove();
      },
    };
  }

  // ---- locate the scrollable message list ---------------------------------
  function findScroller(main) {
    let best = null;
    let bestScore = -1;
    // Prefer the scrollable element that contains the most message rows.
    main.querySelectorAll("div").forEach((el) => {
      if (el.scrollHeight > el.clientHeight + 100 && el.clientHeight > 150) {
        const n = el.querySelectorAll(".message-in,.message-out,[data-id]").length;
        if (n > bestScore) {
          bestScore = n;
          best = el;
        }
      }
    });
    if (best && bestScore > 0) return best;

    // Fallback: largest scrollable region.
    bestScore = -1;
    main.querySelectorAll("div").forEach((el) => {
      if (el.scrollHeight > el.clientHeight + 100 && el.clientHeight > 150) {
        const area = el.clientHeight * el.clientWidth;
        if (area > bestScore) {
          bestScore = area;
          best = el;
        }
      }
    });
    return best;
  }

  async function scrollToTop(s, ui) {
    let last = -1;
    let stable = 0;
    for (let i = 0; i < 600 && !cancelFlag; i++) {
      s.scrollTop = 0;
      await sleep(450);
      const h = s.scrollHeight;
      ui.set("Loading earlier messages…  (pass " + (i + 1) + ", height " + h + "px)");
      if (Math.abs(h - last) < 2) {
        if (++stable >= 3) break;
      } else {
        stable = 0;
      }
      last = h;
    }
    s.scrollTop = 0;
    await sleep(300);
  }

  async function append(rect) {
    // Hide the progress overlay so it isn't captured into the screenshot.
    if (overlayEl) overlayEl.style.visibility = "hidden";
    await new Promise((res) => requestAnimationFrame(() => requestAnimationFrame(res)));
    try {
      const r = await chrome.runtime.sendMessage({
        type: "APPEND",
        sx: rect.x,
        sy: rect.y,
        sw: rect.w,
        sh: rect.h,
      });
      if (!r || !r.ok) throw new Error(r ? r.error : "capture failed");
    } finally {
      if (overlayEl) overlayEl.style.visibility = "visible";
    }
  }

  async function run() {
    if (running) return;
    running = true;
    cancelFlag = false;
    const ui = makeOverlay();
    try {
      const main = document.querySelector("#main");
      if (!main) throw new Error("Open a chat first (no conversation is currently open).");
      const scroller = findScroller(main);
      if (!scroller) throw new Error("Could not find the message list. WhatsApp's layout may have changed.");

      ui.set("Scrolling to the start of the conversation…");
      await scrollToTop(scroller, ui);
      if (cancelFlag) throw new Error("Cancelled");

      const header = main.querySelector("header");
      const chatName = (header ? header.innerText : "chat").split("\n")[0].trim().slice(0, 60);

      const begin = await chrome.runtime.sendMessage({
        type: "BEGIN",
        innerWidth: window.innerWidth,
        innerHeight: window.innerHeight,
        chatName,
      });
      if (!begin || !begin.ok) throw new Error("Could not start capture session.");

      // First frame: capture the whole visible message viewport at top.
      scroller.scrollTop = 0;
      await sleep(350);
      const r0 = scroller.getBoundingClientRect();
      await append({ x: r0.left, y: r0.top, w: r0.width, h: r0.height });
      let frames = 1;

      const step = Math.max(60, Math.floor(r0.height * 0.85));
      while (!cancelFlag) {
        const before = scroller.scrollTop;
        scroller.scrollTop = before + step;
        await sleep(360); // settle paint + stay under capture rate limit
        const after = scroller.scrollTop;
        const delta = after - before;
        if (delta <= 1) break; // reached the bottom

        const r = scroller.getBoundingClientRect();
        // Newly revealed content = bottom `delta` CSS px of the viewport.
        await append({ x: r.left, y: r.top + r.height - delta, w: r.width, h: delta });
        frames++;

        const denom = Math.max(1, scroller.scrollHeight - r.height);
        const pct = Math.min(100, Math.round((after / denom) * 100));
        ui.set("Capturing…  " + frames + " frames  (" + pct + "%)");

        if (after + r.height >= scroller.scrollHeight - 1) break; // at bottom
      }
      if (cancelFlag) throw new Error("Cancelled");

      ui.set("Building image…");
      const res = await chrome.runtime.sendMessage({ type: "END" });
      if (!res || !res.ok) throw new Error(res ? res.error : "finalize failed");
      ui.done(res.parts || 1);
    } catch (e) {
      try {
        await chrome.runtime.sendMessage({ type: "ABORT" });
      } catch (_) {}
      ui.fail(String(e && e.message ? e.message : e));
    } finally {
      running = false;
    }
  }

  chrome.runtime.onMessage.addListener((msg, _sender, reply) => {
    if (msg.type === "START_CAPTURE") {
      if (running) {
        reply({ ok: false, error: "already running" });
      } else {
        run();
        reply({ ok: true });
      }
      return; // synchronous reply
    }
    if (msg.type === "PING") {
      reply({ ok: true, hasChat: !!document.querySelector("#main") });
      return;
    }
  });
})();

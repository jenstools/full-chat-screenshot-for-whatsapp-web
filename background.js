// Service worker: captures the visible tab on demand, stitches the
// newly-revealed strip of each scroll step onto an OffscreenCanvas,
// splits into multiple PNG "parts" when a segment hits the canvas size
// limit, and downloads the result.

const MAX_SEG = 12000; // device px height per output part (under Chrome's canvas limit)

let S = null; // active stitching session

function sanitizeName(s) {
  return (s || "chat").replace(/[^\w\-]+/g, "_").replace(/^_+|_+$/g, "").slice(0, 40) || "chat";
}

function newCanvas(w, h) {
  return new OffscreenCanvas(w, h);
}

function beginSegment() {
  S.seg = newCanvas(S.W, MAX_SEG);
  S.ctx = S.seg.getContext("2d", { alpha: false });
  S.y = 0;
}

// Service workers have no URL.createObjectURL, so encode the PNG as a
// data: URL for chrome.downloads (btoa is available in the worker).
async function blobToDataUrl(blob) {
  const buf = new Uint8Array(await blob.arrayBuffer());
  let bin = "";
  const chunk = 0x8000;
  for (let i = 0; i < buf.length; i += chunk) {
    bin += String.fromCharCode.apply(null, buf.subarray(i, i + chunk));
  }
  return "data:image/png;base64," + btoa(bin);
}

async function flushSegment() {
  if (!S.ctx || S.y <= 0) {
    S.ctx = null;
    S.seg = null;
    S.y = 0;
    return;
  }
  const out = newCanvas(S.W, S.y);
  out.getContext("2d", { alpha: false }).drawImage(S.seg, 0, 0);
  const blob = await out.convertToBlob({ type: "image/png" });
  S.blobs.push(blob);
  S.ctx = null;
  S.seg = null;
  S.y = 0;
}

async function captureBitmap(windowId) {
  let lastErr;
  for (let attempt = 0; attempt < 8; attempt++) {
    try {
      const dataUrl = await chrome.tabs.captureVisibleTab(windowId, { format: "png" });
      const blob = await (await fetch(dataUrl)).blob();
      return await createImageBitmap(blob);
    } catch (e) {
      lastErr = e;
      // Most common cause: MAX_CAPTURE_VISIBLE_TAB_CALLS_PER_SECOND rate limit.
      await new Promise((r) => setTimeout(r, 650));
    }
  }
  throw new Error("captureVisibleTab failed: " + (lastErr && lastErr.message ? lastErr.message : lastErr));
}

chrome.runtime.onMessage.addListener((msg, sender, reply) => {
  (async () => {
    try {
      switch (msg.type) {
        case "BEGIN": {
          S = {
            windowId: sender.tab.windowId,
            innerWidth: msg.innerWidth,
            innerHeight: msg.innerHeight,
            chatName: sanitizeName(msg.chatName),
            W: 0,
            blobs: [],
            seg: null,
            ctx: null,
            y: 0,
          };
          reply({ ok: true });
          break;
        }

        case "APPEND": {
          if (!S) throw new Error("no active session");
          const bmp = await captureBitmap(S.windowId);
          // Map CSS-px crop rect to the captured bitmap's pixel space.
          // This is dpr-proof: we derive scale from the actual bitmap size.
          const scaleX = bmp.width / S.innerWidth;
          const scaleY = bmp.height / S.innerHeight;

          let sx = Math.round(msg.sx * scaleX);
          let sy = Math.round(msg.sy * scaleY);
          let sw = Math.round(msg.sw * scaleX);
          let sh = Math.round(msg.sh * scaleY);

          if (!S.W) {
            S.W = sw;
            beginSegment();
          }

          // Clamp source rect inside the bitmap.
          sx = Math.max(0, Math.min(sx, bmp.width));
          sy = Math.max(0, Math.min(sy, bmp.height));
          sw = Math.min(sw, bmp.width - sx);
          sh = Math.min(sh, bmp.height - sy);

          if (sw > 0 && sh > 0) {
            if (S.y + sh > MAX_SEG) {
              await flushSegment();
              beginSegment();
            }
            // Draw to fixed segment width S.W; scale width to absorb rounding.
            S.ctx.drawImage(bmp, sx, sy, sw, sh, 0, S.y, S.W, sh);
            S.y += sh;
          }
          if (bmp.close) bmp.close();
          reply({ ok: true });
          break;
        }

        case "END": {
          if (!S) throw new Error("no active session");
          await flushSegment();
          const n = S.blobs.length;
          for (let i = 0; i < n; i++) {
            const url = await blobToDataUrl(S.blobs[i]);
            const name =
              n > 1
                ? `whatsapp-${S.chatName}-part${String(i + 1).padStart(2, "0")}.png`
                : `whatsapp-${S.chatName}.png`;
            await chrome.downloads.download({
              url,
              filename: name,
              conflictAction: "uniquify",
              saveAs: false,
            });
          }
          S = null;
          reply({ ok: true, parts: n });
          break;
        }

        case "ABORT": {
          S = null;
          reply({ ok: true });
          break;
        }

        default:
          reply({ ok: false, error: "unknown message type" });
      }
    } catch (e) {
      S = null;
      reply({ ok: false, error: String(e && e.message ? e.message : e) });
    }
  })();
  return true; // keep the message channel open for async reply
});

const go = document.getElementById("go");
const status = document.getElementById("status");

function setStatus(t) {
  status.textContent = t;
}

go.addEventListener("click", async () => {
  go.disabled = true;
  setStatus("");
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !/^https:\/\/web\.whatsapp\.com\//.test(tab.url || "")) {
      setStatus("Open web.whatsapp.com (and a chat) in this tab first.");
      go.disabled = false;
      return;
    }

    // Make sure the content script is present, then check a chat is open.
    let ping;
    try {
      ping = await chrome.tabs.sendMessage(tab.id, { type: "PING" });
    } catch (_) {
      await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content.js"] });
      ping = await chrome.tabs.sendMessage(tab.id, { type: "PING" });
    }
    if (!ping || !ping.hasChat) {
      setStatus("No chat is open. Open a conversation, then try again.");
      go.disabled = false;
      return;
    }

    const res = await chrome.tabs.sendMessage(tab.id, { type: "START_CAPTURE" });
    if (res && res.ok) {
      setStatus("Started. Watch the progress box on the page. You can close this popup.");
      setTimeout(() => window.close(), 1200);
    } else {
      setStatus("Could not start: " + (res ? res.error : "no response"));
      go.disabled = false;
    }
  } catch (e) {
    setStatus("Error: " + (e && e.message ? e.message : e));
    go.disabled = false;
  }
});

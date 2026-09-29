const button = document.getElementById("import");
const status = document.getElementById("status");

function showStatus(message, kind) {
  status.textContent = message;
  status.className = kind;
}

button.addEventListener("click", async () => {
  button.disabled = true;
  showStatus("Reading the word list...", "");

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.url?.startsWith("https://www.sbsolver.com/")) {
      throw new Error("Open the SB Solver page in this tab first.");
    }

    const [{ result: words }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => [...document.querySelectorAll("table.bee-set td.bee-hover a")]
        .map((element) => element.textContent.trim().toUpperCase())
        .filter(Boolean),
    });

    if (!words?.length) {
      throw new Error("No words are visible. Finish loading the page first.");
    }

    const response = await fetch("http://127.0.0.1:8765/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ words, url: tab.url }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "The app rejected the list.");

    showStatus(`Imported ${payload.imported} words. Return to the app.`, "success");
  } catch (error) {
    showStatus(error.message, "error");
  } finally {
    button.disabled = false;
  }
});

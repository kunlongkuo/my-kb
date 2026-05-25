function injectButton() {
  const actionsSelector = "#top-level-buttons-computed, #top-row #actions";
  const actionsRow = document.querySelector(actionsSelector);
  
  if (actionsRow && !document.querySelector(".yt-obsidian-btn")) {
    const btn = document.createElement("button");
    btn.className = "yt-obsidian-btn";
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg>
      Obsidian Notes
    `;
    
    btn.onclick = async () => {
      if (btn.classList.contains("loading")) return;
      
      btn.classList.add("loading");
      btn.innerText = "Processing...";
      
      try {
        const response = await fetch("http://127.0.0.1:8000/summarize", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: window.location.href })
        });
        
        const data = await response.json();
        
        if (data.status === "success") {
          // Trigger download
          downloadMarkdown(data.content, "video_summary.md");
          btn.innerText = "Done!";
          setTimeout(() => {
            btn.innerHTML = `...`; // Restore SVG and text
            injectButton(); // Lazy way to restore original innerHTML
          }, 3000);
        } else {
          alert("Error: " + data.detail);
          btn.innerText = "Failed";
        }
      } catch (err) {
        alert("Server not running. Please start yt_notes_server.py");
        btn.innerText = "Error";
      } finally {
        btn.classList.remove("loading");
      }
    };
    
    actionsRow.appendChild(btn);
  }
}

function downloadMarkdown(content, filename) {
  const blob = new Blob([content], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// Watch for page changes (YouTube uses SPA navigation)
const observer = new MutationObserver(injectButton);
observer.observe(document.body, { childList: true, subtree: true });

injectButton();

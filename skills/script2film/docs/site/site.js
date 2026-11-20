// Script2Film 網站共用程式：GitHub 連結與計數、複製鈕、完整影片的播放器。每一頁都讀這一份。
(function () {
  // 倉庫改名或搬家時只改這一行：頁面上所有 GitHub 連結與計數都從這裡來
  var REPO = "notoriouslab/script2film";
  var base = "https://github.com/" + REPO;
  function set(id, href) { var el = document.getElementById(id); if (el) el.href = href; }
  set("gh-main", base); set("gh-zip", base + "/archive/refs/heads/main.zip");
  set("gh-star-link", base); set("gh-fork-link", base + "/fork"); set("gh-watch-link", base + "/subscription");
  document.querySelectorAll("a.gh-doc").forEach(function (a) {
    var p = a.getAttribute("data-path"); a.href = p ? base + "/blob/main/" + p : base;
  });
  var clone = document.getElementById("clone-cmd");
  if (clone) clone.textContent = "git clone " + base + ".git";
  // 完整影片：按了才把無聲片段換成 YouTube 播放器，沒按之前這一頁不連 YouTube；沒有 JS 時這顆鈕就是一般連結。
  // 影片 ID 與標題寫在按鈕的 data-yt、data-title，每一頁各放各的片
  var play = document.getElementById("play-full");
  if (play && play.getAttribute("data-yt")) play.addEventListener("click", function (e) {
    // YouTube 的嵌入播放器要看得到來源網址才肯播（否則錯誤 153）；直接從硬碟開這一頁（file://）沒有來源可給，
    // 這時不攔截，讓連結照常另開分頁到 YouTube
    if (location.protocol !== "http:" && location.protocol !== "https:") return;
    e.preventDefault();
    var box = document.querySelector(".hero-media"), f = document.createElement("iframe");
    f.src = "https://www.youtube-nocookie.com/embed/" + encodeURIComponent(play.getAttribute("data-yt")) + "?autoplay=1&rel=0";
    f.title = play.getAttribute("data-title") || ""; f.allow = "autoplay; encrypted-media; picture-in-picture"; f.allowFullscreen = true;
    f.referrerPolicy = "strict-origin-when-cross-origin";
    box.innerHTML = ""; box.appendChild(f); play.style.display = "none";
  });
  // 展示頁的小格：捲到畫面裡才載入並播放，離開就停（27 支不會一次全載）
  var tiles = document.querySelectorAll(".tile video");
  if (tiles.length && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) { var p = e.target.play(); if (p && p.catch) p.catch(function () {}); } else e.target.pause();
      });
    }, { threshold: 0.35 });
    tiles.forEach(function (v) { io.observe(v); });
  }
  // 複製鈕
  document.querySelectorAll("button.copy").forEach(function (b) {
    b.addEventListener("click", function () {
      var src = document.getElementById(b.getAttribute("data-copy")); if (!src || !navigator.clipboard) return;
      navigator.clipboard.writeText(src.textContent).then(function () {
        var old = b.textContent; b.textContent = b.getAttribute("data-done"); setTimeout(function () { b.textContent = old; }, 1400);
      }).catch(function () {});
    });
  });
  // 計數在開頁時向 GitHub 取；取不到（離線、限流、倉庫還沒公開）就只留按鈕，不顯示數字
  function put(id, n) {
    var el = document.getElementById(id);
    if (el && typeof n === "number") el.textContent = n.toLocaleString();
  }
  fetch("https://api.github.com/repos/" + REPO)
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (repo) {
      if (!repo) return;
      put("gh-stars", repo.stargazers_count);
      put("gh-forks", repo.forks_count);
      put("gh-watch", repo.subscribers_count);   // watchers_count 其實等於星標數，關注數是這一個
    })
    .catch(function () {});
})();

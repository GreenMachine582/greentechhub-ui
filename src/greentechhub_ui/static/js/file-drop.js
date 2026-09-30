// gth-file-drop — see components/file_drop.html (v0.11).
// Drag-and-drop onto the zone fills the real file input (via DataTransfer)
// and fires a bubbling `change`. Every change is checked against
// data-accept / data-max-size in the capture phase — before an enclosing
// hx-trigger="change" form sees it — and rejected files are removed from
// the input and listed, one error each. The upload progress bar follows the
// enclosing form's htmx:xhr:progress; htmx 1.9 fires that event for the
// download too, so once the upload reaches 100% the bar switches to an
// indeterminate "Processing…" and ignores the rest until the response.
(function () {
  function root(el) { return el && el.closest ? el.closest("[data-gth-file-drop]") : null; }
  function input(r) { return r.querySelector(".gth-file-drop-input"); }

  function size(n) {
    if (n >= 1048576) return +(n / 1048576).toFixed(1) + " MB";
    if (n >= 1024) return +(n / 1024).toFixed(1) + " KB";
    return n + " B";
  }

  function accepts(tokens, file) {
    if (!tokens.length) return true;
    var name = file.name.toLowerCase();
    var type = (file.type || "").toLowerCase();
    return tokens.some(function (t) {
      if (t.charAt(0) === ".") return name.slice(-t.length) === t;
      if (t.slice(-2) === "/*") return type.indexOf(t.slice(0, -1)) === 0;
      return type === t;
    });
  }

  function item(text, cls) {
    var li = document.createElement("li");
    li.textContent = text;  // file names are user data: never innerHTML
    if (cls) li.className = cls;
    return li;
  }

  function validate(r) {
    var inp = input(r);
    var tokens = (r.getAttribute("data-accept") || "").split(",")
      .map(function (t) { return t.trim().toLowerCase(); }).filter(Boolean);
    var max = parseInt(r.getAttribute("data-max-size"), 10) || 0;
    var maxLabel = r.getAttribute("data-max-label") || size(max);
    var kept = new DataTransfer();
    var errors = [];
    Array.prototype.forEach.call(inp.files, function (f) {
      if (!inp.multiple && kept.files.length) errors.push(f.name + " — only one file can be uploaded");
      else if (!accepts(tokens, f)) errors.push(f.name + " — not an accepted file type");
      else if (max && f.size > max) errors.push(f.name + " — larger than " + maxLabel);
      else kept.items.add(f);
    });
    if (errors.length) inp.files = kept.files;

    var list = r.querySelector(".gth-file-drop-files");
    list.replaceChildren();
    Array.prototype.forEach.call(inp.files, function (f) {
      var li = item(f.name, "gth-file-drop-file");
      var s = document.createElement("span");
      s.className = "gth-file-drop-size";
      s.textContent = size(f.size);
      li.appendChild(s);
      list.appendChild(li);
    });
    list.hidden = !inp.files.length;

    // A new pick replaces every earlier message, server ones included.
    var errList = r.querySelector(".gth-file-drop-errors");
    errList.replaceChildren.apply(errList, errors.map(function (e) { return item(e); }));
    var invalid = errors.length > 0;
    inp.classList.toggle("is-invalid", invalid);
    r.querySelector(".gth-file-drop-zone").classList.toggle("is-invalid", invalid);
    if (invalid) inp.setAttribute("aria-invalid", "true");
    else inp.removeAttribute("aria-invalid");
  }

  document.addEventListener("change", function (evt) {
    var r = root(evt.target);
    if (r && evt.target === input(r)) validate(r);
  }, true);

  // ── drag and drop ──
  function zone(evt) {
    var z = evt.target.closest && evt.target.closest(".gth-file-drop-zone");
    return z && root(z) ? z : null;
  }
  function hasFiles(evt) {
    return evt.dataTransfer && Array.prototype.indexOf.call(evt.dataTransfer.types || [], "Files") !== -1;
  }
  ["dragenter", "dragover"].forEach(function (type) {
    document.addEventListener(type, function (evt) {
      var z = zone(evt);
      if (!z || !hasFiles(evt) || input(root(z)).disabled) return;
      evt.preventDefault();
      evt.dataTransfer.dropEffect = "copy";
      z.classList.add("is-dragover");
    });
  });
  document.addEventListener("dragleave", function (evt) {
    var z = zone(evt);
    if (z && !z.contains(evt.relatedTarget)) z.classList.remove("is-dragover");
  });
  document.addEventListener("drop", function (evt) {
    var z = zone(evt);
    if (!z || !hasFiles(evt)) return;
    evt.preventDefault();
    z.classList.remove("is-dragover");
    var inp = input(root(z));
    if (inp.disabled) return;
    var dt = new DataTransfer();
    Array.prototype.forEach.call(evt.dataTransfer.files, function (f) { dt.items.add(f); });
    inp.files = dt.files;
    inp.dispatchEvent(new Event("change", { bubbles: true }));
  });

  // ── upload progress ──
  function uploading(elt) {
    var scope = (elt.closest && elt.closest("form")) || elt;
    var roots = scope.querySelectorAll ? scope.querySelectorAll("[data-gth-file-drop]") : [];
    return Array.prototype.filter.call(roots, function (r) { return input(r).files.length > 0; });
  }
  function setBar(r, state, pct) {
    var p = r.querySelector(".gth-file-drop-progress");
    var bar = p.firstElementChild;
    p.hidden = state === "idle";
    p.setAttribute("data-state", state);
    var processing = state === "processing";
    bar.classList.toggle("progress-bar-striped", processing);
    bar.classList.toggle("progress-bar-animated", processing);
    bar.style.width = (processing ? 100 : pct) + "%";
    bar.textContent = processing ? "Processing…" : "";
    if (processing) {
      p.removeAttribute("aria-valuenow");
      p.setAttribute("aria-valuetext", "Processing…");
    } else {
      p.setAttribute("aria-valuenow", String(pct));
      p.removeAttribute("aria-valuetext");
    }
  }

  document.addEventListener("htmx:beforeRequest", function (evt) {
    uploading(evt.detail.elt).forEach(function (r) { setBar(r, "uploading", 0); });
  });
  document.addEventListener("htmx:xhr:progress", function (evt) {
    var d = evt.detail;
    if (!d.lengthComputable || !d.total) return;
    uploading(evt.target).forEach(function (r) {
      var p = r.querySelector(".gth-file-drop-progress");
      if (p.getAttribute("data-state") !== "uploading") return;
      if (d.loaded >= d.total) setBar(r, "processing");
      else setBar(r, "uploading", Math.floor((d.loaded / d.total) * 100));
    });
  });
  document.addEventListener("htmx:afterRequest", function (evt) {
    var elt = evt.detail.elt;
    var scope = (elt.closest && elt.closest("form")) || elt;
    if (!scope.querySelectorAll) return;
    scope.querySelectorAll("[data-gth-file-drop]").forEach(function (r) { setBar(r, "idle", 0); });
  });
})();

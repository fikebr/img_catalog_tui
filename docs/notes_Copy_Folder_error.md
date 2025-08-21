You’re super close—the main gotcha is the Windows path you pass inline:

```html
onclick="copyWindowsPath('E:\fooocus\images\new\2025-08-03_tmp', 'aardvark_...')"
```

Inside a JavaScript string, `\f`, `\n`, and `\t` are escape sequences (form feed, newline, tab). So the browser is actually seeing something like:

```
E:⟂ooocus\images\
2025-08-03_tmp
```

…which explains the weird result.

## Two clean fixes

### Option A — keep inline onclick (escape backslashes)

Double the backslashes in the attribute:

```html
<button class="btn"
  onclick="copyWindowsPath('E:\\fooocus\\images\\new\\2025-08-03_tmp','aardvark_fike_1920s_prohibition_era_photograph_black_and_whit_bc61cf96-45c3-4c65-9740-f61756ffcbd9_3')">
  Copy Folder
</button>
```

Your function can stay almost the same:

```html
<script>
function copyWindowsPath(folderPath, imagesetName) {
  // Ensure a trailing backslash, then append imageset
  let path = folderPath.endsWith('\\') ? folderPath : folderPath + '\\';
  path += imagesetName;

  navigator.clipboard.writeText(path).then(() => {
    alert('Copied to clipboard: ' + path);
  }).catch(err => {
    console.error('Failed to copy: ', err);
    alert('Copy failed. This only works over HTTPS/localhost and on user gesture.');
  });
}
</script>
```

### Option B — avoid inline JS entirely (more robust)

Use data- attributes so you don’t have to escape anything, then attach listeners:

```html
<div class="card-buttons">
  <button class="btn"
          data-imageset="aardvark_fike_1920s_prohibition_era_photograph_black_and_whit_bc61cf96-45c3-4c65-9740-f61756ffcbd9_3"
          onclick="copyToClipboard(this.dataset.imageset)">
    Copy Imageset
  </button>

  <button class="btn copy-folder"
          data-folder="E:\fooocus\images\new\2025-08-03_tmp"
          data-imageset="aardvark_fike_1920s_prohibition_era_photograph_black_and_whit_bc61cf96-45c3-4c65-9740-f61756ffcbd9_3">
    Copy Folder
  </button>

  <button class="btn open-report"
          data-folder="E:\fooocus\images\new\2025-08-03_tmp"
          data-imageset="aardvark_fike_1920s_prohibition_era_photograph_black_and_whit_bc61cf96-45c3-4c65-9740-f61756ffcbd9_3">
    Open
  </button>
</div>

<script>
function joinWinPath(dir, name) {
  let p = dir.replace(/\//g, '\\');
  if (!p.endsWith('\\')) p += '\\';
  return p + name;
}

function copyWindowsPath(folderPath, imagesetName) {
  const path = joinWinPath(folderPath, imagesetName);
  navigator.clipboard.writeText(path).then(() => {
    alert('Copied to clipboard: ' + path);
  }).catch(err => {
    console.error('Failed to copy: ', err);
    alert('Copy failed. This only works over HTTPS/localhost and on user gesture.');
  });
}

// Attach once, no escaping issues
document.querySelectorAll('.copy-folder').forEach(btn => {
  btn.addEventListener('click', () => {
    copyWindowsPath(btn.dataset.folder, btn.dataset.imageset);
  });
});

// Example openReport hook (you didn’t include the impl)
document.querySelectorAll('.open-report').forEach(btn => {
  btn.addEventListener('click', () => {
    const fullPath = joinWinPath(btn.dataset.folder, btn.dataset.imageset);
    openReport(btn.dataset.folder, btn.dataset.imageset); // your function
    // or window.open(...) depending on what “Open” should do
  });
});
</script>
```

## Quick checklist

* ✅ Escape backslashes if you keep inline JS (`\\`).
* ✅ Clipboard API only works on secure contexts (HTTPS or `localhost`) and requires a user gesture (click). Your buttons provide the gesture; make sure you’re not on `file://`.
* ✅ If the folder already uses backslashes, you don’t need `replace(/\//g, '\\')`, but it doesn’t hurt.

If you want, paste the console error (if any) and I’ll zero in further.

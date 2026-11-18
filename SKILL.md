---
name: devin-desktop-zh
description: Build and maintain a Simplified Chinese localization for Devin Desktop (the Windsurf-based macOS app from Cognition). Use when the user wants Devin's interface in Chinese, reports that Devin has no Chinese option, asks to translate/harden/repair the Chinese language pack, or needs to re-apply the localization after a Devin update. Covers both halves of the app: the React agent UI (i18next dictionary injection) and the editor/IDE half (hard-coded literals in workbench / sessions / windsurf-chat-client bundles), plus the signature and VS Code integrity-check fix that keeps macOS from reporting the app as damaged.
---

# Devin Desktop 简体中文

Two halves, two mechanisms:

| Half | Text source | Method |
|---|---|---|
| Agent UI (`devin-webapp-host`, React + i18next) | i18next resource bundles, only `en/ja/pt/es/de` are registered | add a `zh` dictionary chunk, register the locale, force `changeLanguage("zh")` |
| Editor / IDE half (VS Code fork) | mostly hard-coded literals + a few backtick label maps | literal replacement inside the bundles, then fix checksums |

Do not try `PUT /users/ui-language` or a server flag first: the server rejects `zh`, and the client has no `zh` entry in its language array, so the switch is unreachable.

## 0. Facts you need before touching anything

* App: `/Applications/Devin.app` — Electron, `CFBundleName=Devin`, product `com.exafunction.windsurf`.
* Bundles: `Contents/Resources/app/out/vs/workbench/devin-webapp-host/assets/` (~3.2k chunks, 125 MB), plus `workbench/workbench.desktop.main.js` (~23 MB), `sessions/sessions.desktop.main.js` (~58 MB), `workbench/windsurf-chat-client/index.js` (~35 MB).
* UI language entry chunk: `assets/chunk-entry-host-editor-mode-menu-*.js` (hash changes per build). It holds the language array and the i18next `init`.
* Start-up effect: `assets/chunk-entry-host-index-*.js`, inside the effect that calls `if(!X){Y(\`en\`);return}`.
* `Contents/Resources/app/product.json` has a `checksums` map (base64 SHA-256, padding stripped). Editing a bundle listed there without updating the hash makes VS Code show **“安装似乎损坏。请重新安装。”**.

Respect the user's choice of *which* app bundle to modify: patching `/Applications/Devin.app` in place may fail with `EPERM` under TCC. Cloning to `Devin 中文版.app` and patching the clone is the reliable path.

## 1. Extract the English dictionary

```bash
cp assets/chunk-entry-host-editor-mode-menu-*.js /tmp/w/
cp assets/chunk-rolldown-runtime-*.js /tmp/w/
printf '\nexport{cu as __cu,lu as __lu};\n' >> /tmp/w/chunk-entry-host-editor-mode-menu-*.js
node -e 'import("/tmp/w/chunk-entry-host-editor-mode-menu.js").then(m=>{
  require("fs").writeFileSync("/tmp/w/en.json", JSON.stringify(m.__cu));
  require("fs").writeFileSync("/tmp/w/en.review.json", JSON.stringify(m.__lu));})'
```

The exported names (`cu`, `lu`) are build-specific: read the `init({resources:{en:{translation:…,review:…}}})` call in the chunk to find them.

## 2. Translate

Any MT is fine; the reference implementation in this repo used Bing's web translator (`ttranslatev3`), 12 threads, ~2.2k characters per request, with a JSON cache file so a run can resume. Translate line-by-line: the dictionary values contain `\n`, and the key set must stay identical (missing keys silently fall back to English, which is acceptable; extra keys are dead weight).

Afterwards do a terminology pass — machine translation mangles product terms. Reference fixes: `Wiki → 知识库` (never 维基/wiki), `Devin` must stay `Devin` (MT turns it into 德文/德温), `Cascade`, `Windsurf` stay English, `Review → 评审`, `Sessions → 会话`, `Customizations → 自定义`.

## 3. Inject the locale

1. Write the dictionary as `assets/chunk-zh-hans-zhcn.js` with `export default {…}` (and the review one likewise).
2. In the language-array chunk, append to the array:
   `{code:"zh",label:"中文（简体）",translation:()=>import("./chunk-zh-hans-zhcn.js"),review:()=>import("./chunk-zh-review-zhcn.js")}`
3. In the start-up chunk, insert before the existing `if(!X){Y("en");return}`:
   `if(!window.__devinZhOnce){window.__devinZhOnce=1;Y("zh")}return;` — take `Y` from that anchor with a regex rather than hard-coding it.
4. `Info.plist`: set **only** `CFBundleDisplayName`. Changing `CFBundleName` makes Electron look for `Devin 中文版 Helper.app` and abort with `Unable to find helper app`.

## 4. Editor half: hard-coded literals

Candidate extraction must cover **both** quoting styles and **both** key forms:

* `"…"` and `` `…` `` literals,
* bare `label:`, quoted `"label":`, and JSX `children:["…"]`.

A global “pair the quotes” regex is unreliable on 58 MB minified files — an odd quote earlier in the file desynchronises everything after it. Prefer `"[^"\\]{2,99}"` / `` `[^`\\$]{2,99}` ``, which only ever matches clean, escape-free literals.

Skip: locale chunks `chunk-{de,ja,pt,es,fr,it,ko,ru,nl,pl,tr,zh}-*`, URLs, CSS, mime types, font stacks, base64, component names, and demo/sample data.

Curated label maps live in dicts such as `An={sidechatUnavailable:\`Not available in side chats yet\`,…,effortPro:\`Pro\`}` — translate those explicitly (`reasoningEffort → 推理强度`, `effortLow → 低`, …), because single words never pass the "looks like UI copy" filter.

After replacing, run `node --check` on each bundle — minified bundles still parse as classic scripts.

## 5. Keep the app launchable

```bash
# 1. recompute checksums for every modified file listed in product.json
python3 - <<'PY'
import json,hashlib,base64,os
app='/Applications/Devin 中文版.app/Contents/Resources/app'
d=json.load(open(app+'/product.json'))
for k in d['checksums']:
    p=os.path.join(app,'out',k)
    if os.path.exists(p):
        h=base64.b64encode(hashlib.sha256(open(p,'rb').read()).digest()).decode().rstrip('=')
        if h!=d['checksums'][k]: d['checksums'][k]=h; print('updated',k)
json.dump(d,open(app+'/product.json','w'),ensure_ascii=False,indent=2)
PY
# 2. clear Electron caches, re-sign ad-hoc, relaunch
rm -rf ~/Library/Application\ Support/Devin/"Code Cache" ~/Library/Application\ Support/Devin/GPUCache
codesign --force --sign - "/Applications/Devin 中文版.app"
open "/Applications/Devin 中文版.app"
```

Pitfalls:

* Unsigned bundles are moved to the Trash on launch.
* Original and clone share one `userData` and one single-instance lock: quit the original first, otherwise the clone forwards its launch and exits.
* Every re-sign is a new identity, so macOS re-asks for the `Devin Safe Storage` keychain item. The user must enter the login password and pick **Always Allow** once per signature change.
* The window remembers the last view. If it opens in `IDE 视图`, the user sees the editor; switch with the title-bar popup (`代理` ⇄ `IDE`) to `代理视图`.

## 6. Verify

`screencapture -x` + look at the image, and/or read the AX tree (`general_computer_use`): `文本/按钮` nodes should be Chinese, and `损坏` must not appear (that string means the checksum step was skipped). Logs: `~/Library/Application Support/Devin/logs/<timestamp>/window*/renderer.log`.

Expected leftovers that cannot be fixed locally: server/ACP payloads (model labels `Default`/`High`, status-bar plan badge `Free - Upgrade Now`), brand names, and other languages' dictionaries.

## 7. After a Devin update

Re-run `install_devin_zh.py` (agent UI), then repeat §4–§5 for the editor half. Keep the pre-patch bundles; restoring them is the fastest rollback.

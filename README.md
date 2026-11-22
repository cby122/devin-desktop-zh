Early translation of Devin Desktop's UI into Simplified Chinese.

Devin Desktop ships its own React front-end and only bundles `en / ja / pt / es / de` dictionaries, so there is no in-app switch for Chinese. This repo contains a hand-built Chinese dictionary plus the injection script that loads it at start-up, together with a hard-coded-string patcher for the editor (Windsurf) half of the app.

## What is inside

| File | Purpose |
|---|---|
| `SKILL.md` | Agent Skill that walks an AI agent through the whole workflow (extract → translate → inject → patch IDE → re-sign). |
| `install_devin_zh.py` | One-shot installer: clones `/Applications/Devin.app` to `Devin 中文版.app`, injects both dictionaries, registers the `zh` locale, forces it on start-up, re-applies the editor half from `ide_cache.json`, injects the render-layer option labels, recomputes the `product.json` checksums, re-signs ad-hoc and self-checks the result. `--no-ide` skips the editor half. |
| `ide_cache.json` | EN → ZH literal pairs used by the installer to restore the editor half after an app update. |
| `zh-Hans.translation.json` | Main dictionary — 423 namespaces / 33,457 strings, key-set identical to the built-in English one. |
| `chunk-zh-hans-zhcn.js` | The same dictionary as an ES module chunk, which is what the app actually imports. |
| `zh-Hans.review.json` / `chunk-zh-review-zhcn.js` | Dictionary for the PR-review screen (50 namespaces / 1,447 strings). The same file also feeds the dictionary embedded inside `sessions.desktop.main.js` and `windsurf-chat-client/index.js`. |
| `tool-option-labels.py` | Maps the ACP-provided option labels (Default / Low / Medium / High / Xhigh / Max / Normal …) to Chinese in the local select renderer — the model, reasoning-effort and collaboration-mode drop-downs. |
| `tool-inline-dict.py` | Dumps / re-patches the dictionaries embedded in the two big editor bundles (`JSON.parse('…')` literal) — the layer behind the Review, merge-manager and reviewer-sidebar screens. |
| `tool-ide-translate.py` | Extracts hard-coded UI literals from the three big bundles and translates them (Bing, resumable cache). |
| `tool-ide-patch.py` / `tool-pass2-patch.py` | Replace those literals in `workbench.desktop.main.js`, `sessions.desktop.main.js` and `windsurf-chat-client/index.js`, plus the web-app assets. |
| `tool-bing-translate.py` | Minimal Bing translator client (cookie jar + token refresh) used by the two batch drivers below; no API key needed. |
| `tool-translate-all.py` | First pass: walks the English dictionary, translates every string with a resumable cache, prints a progress log. |
| `tool-pass2-extract.py` | Second pass, extract: pulls the strings that never reached a React text node out of the big bundles (`JSON.parse('…')` literals, template strings) into a candidate list. |
| `tool-pass2-translate.py` | Second pass, translate: translates that candidate list with its own cache, split across worker threads. |
| `tool-assemble.py` / `tool-assemble2.py` | Assemble: merges the two translation caches back into the dictionaries and regenerates `zh-Hans.translation.json` / the ES module chunk. |
| `tool-translate-review.py` | Review-screen dictionary pipeline: flattens the English review dictionary, translates the gaps, writes `zh-Hans.review.json`. |
| `tool-scan-hard.py` | Audit: collects every remaining ASCII-only string across the bundles so the leftovers can be triaged into “hard-coded, patch it” vs “comes from the server”. |
| `tool-patch-app.py` | Applies the web-app (`devin-webapp-host/assets`) patches to an already built bundle — the manual counterpart of `install_devin_zh.py --no-ide`. |
| `tool-normalize-terms.py` / `tool-term-pass2.py` | Terminology pass: rewrites 审查/审核/审阅 → 评审, 拉取请求 → PR, adds spacing between CJK and Latin, protects `{{placeholders}}` and `<tags>`; the second pass fixes the sentences the first pass made awkward. |
| `devin-desktop-zh.zip` | Ready-to-use archive of the whole pack (two dictionaries, `ide_cache.json`, installer, docs) — download this if you just want to install. |

`screenshot-ide.png` shows the editor view after patching.

## Pipeline

```
extract    tool-pass2-extract.py / tool-ide-translate.py
translate  tool-bing-translate.py + tool-translate-all.py · tool-pass2-translate.py · tool-translate-review.py
assemble   tool-assemble.py → tool-assemble2.py
terminology tool-normalize-terms.py → tool-term-pass2.py
patch      install_devin_zh.py   (or tool-patch-app.py + tool-ide-patch.py + tool-option-labels.py + tool-inline-dict.py)
finish     checksums + ad-hoc re-sign + self-check, all inside install_devin_zh.py
```

Everything except the installer is a re-runnable helper: each stage reads a cache and is safe to stop and resume.

## Install

```bash
python3 install_devin_zh.py            # default: /Applications/Devin.app → /Applications/Devin 中文版.app
open "/Applications/Devin 中文版.app"
```

The original `Devin.app` is never touched; the result is a second bundle that you can delete at any time.

First launch may ask for keychain access (“Devin Safe Storage”). Enter your macOS login password and choose **Always Allow** once; the login state is preserved afterwards.

## Known limits

* Strings that the Devin server or an ACP agent sends at runtime (session titles such as `New session kenny`, automation templates, session content, model capability labels such as `Normal` / `Default` / `High`, the status-bar plan badge `Free - Upgrade Now` and `Devin - Settings`) cannot be localised locally.
* Agent and skill descriptions in the picker are author-written content (`~/.claude/agents/*.md`); they stay in whatever language their author used.
* Screens rendered by the remote web app (`app.devin.ai/...`) bring their own server-side copy.
* Brand names stay as-is: Devin, Windsurf, Codex, Claude, DeepWiki, MiniMax.
* Devin auto-updates overwrite the bundle; re-run the installer afterwards.

## 中文规范（2026-11-19 起）

| English | 统一译法 | 不再使用 |
|---|---|---|
| Review（功能、页签、Devin Review） | 评审 | 德文 / 审查 / 审核 / 审阅 |
| Pull request | PR | 拉取请求 |
| Sessions | 会话 | 会议 |
| Wiki | 知识库 | 维基 / wiki |
| 管理员审批（席位、用量申请） | 审核 | — |

两套词典都按此整理过，并补了中英之间空格（`PR 评论`、`Devin 会话`）。
同日修复：评审词典 9 处把 Devin 误译成「德文」；代理下拉里按关键词把作者自述改写成
「推理更深，适合复杂问题」/「推理更少，速度更快」的启发式逻辑已移除。

## Using it as an Agent Skill

Copy `SKILL.md` (and the files it references) into `.user_skills/devin-desktop-zh/`, or just point your agent at this repository and let it read `SKILL.md`.

## License

MIT — see `LICENSE`. Not affiliated with Cognition / Windsurf. Use at your own risk; patching a signed macOS bundle invalidates its signature, which is why the installer re-signs it ad-hoc.

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

`screenshot-ide.png` shows the editor view after patching.

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

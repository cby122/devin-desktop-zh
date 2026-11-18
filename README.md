Early translation of Devin Desktop's UI into Simplified Chinese.

Devin Desktop ships its own React front-end and only bundles `en / ja / pt / es / de` dictionaries, so there is no in-app switch for Chinese. This repo contains a hand-built Chinese dictionary plus the injection script that loads it at start-up, together with a hard-coded-string patcher for the editor (Windsurf) half of the app.

## What is inside

| File | Purpose |
|---|---|
| `SKILL.md` | Agent Skill that walks an AI agent through the whole workflow (extract → translate → inject → patch IDE → re-sign). |
| `install_devin_zh.py` | One-shot installer: clones `/Applications/Devin.app` to `Devin 中文版.app`, injects the dictionary, registers the `zh` locale, forces it on start-up, re-signs. |
| `zh-Hans.translation.json` | Main dictionary — 423 namespaces / 33,457 strings, key-set identical to the built-in English one. |
| `chunk-zh-hans-zhcn.js` | The same dictionary as an ES module chunk, which is what the app actually imports. |
| `zh-Hans.review.json` / `chunk-zh-review-zhcn.js` | Dictionary for the PR-review screen (50 namespaces / 1,283 strings). |
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

* Strings that the Devin server or an ACP agent sends at runtime (automation templates, session content, model capability labels such as `Default` / `High`, the status-bar plan badge) cannot be localised locally.
* Brand names stay as-is: Devin, Windsurf, Codex, Claude, DeepWiki, MiniMax.
* Devin auto-updates overwrite the bundle; re-run the installer afterwards.

## Using it as an Agent Skill

Copy `SKILL.md` (and the files it references) into `.user_skills/devin-desktop-zh/`, or just point your agent at this repository and let it read `SKILL.md`.

## License

MIT — see `LICENSE`. Not affiliated with Cognition / Windsurf. Use at your own risk; patching a signed macOS bundle invalidates its signature, which is why the installer re-signs it ad-hoc.

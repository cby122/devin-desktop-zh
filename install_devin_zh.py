#!/usr/bin/env python3
"""
给 Devin Desktop（Windsurf 内核）注入简体中文语言包，并生成一个可直接运行的中文版 App。

用法：
    python3 install_devin_zh.py                 # 默认：/Applications/Devin.app -> /Applications/Devin 中文版.app
    python3 install_devin_zh.py --source /Applications/Devin.app --target "/Applications/Devin 中文版.app"

原理：
    1. Devin 的界面（devin-webapp-host）是本地打包的 React 应用，使用 i18next。
       它自带 en / ja / pt / es / de 五种语言，每种语言是一个懒加载的分片 chunk。
    2. 本脚本把 zh-Hans 词典作为新的 chunk 放进 assets 目录，
       并在语言列表 uu 数组里注册 {code:'zh'}，然后在启动时强制切到 zh。
    3. 因为改动了 app 包内容，原签名失效，需要用 ad-hoc 重新签名（codesign -f -s -）。
    注意：重签名后首次启动，macOS 会弹「钥匙串 Safe Storage」授权框，
         点「始终允许」并输入登录密码即可（只此一次）；拒绝也能用，但要重新登录 Devin。
"""
import argparse, json, os, re, shutil, subprocess, sys

PACK_DIR = os.path.dirname(os.path.abspath(__file__))
ZH_CHUNK = 'chunk-zh-hans-zhcn.js'
ZH_REVIEW = 'chunk-zh-review-zhcn.js'


def sh(cmd, **kw):
    return subprocess.run(cmd, shell=isinstance(cmd, str), check=True,
                          capture_output=True, text=True, **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', default='/Applications/Devin.app')
    ap.add_argument('--target', default='/Applications/Devin 中文版.app')
    a = ap.parse_args()

    src, dst = a.source, a.target
    if not os.path.isdir(src):
        sys.exit(f'找不到源 App：{src}')

    if os.path.exists(dst):
        print(f'目标已存在，直接在其上打补丁：{dst}')
    else:
        print(f'克隆 {src} -> {dst}')
        # APFS 写时复制，秒级完成、几乎不占额外空间
        sh(['cp', '-cR', src, dst])
        sh(['xattr', '-d', 'com.apple.quarantine', dst], check=False)

    base = os.path.join(dst, 'Contents/Resources/app/out/vs/workbench/devin-webapp-host')
    assets = os.path.join(base, 'assets')
    if not os.path.isdir(assets):
        sys.exit('这个 App 不像 Devin Desktop（找不到 devin-webapp-host/assets）')

    entry = next((os.path.join(assets, f) for f in os.listdir(assets)
                  if f.startswith('chunk-entry-host-editor-mode-menu-')), None)
    hostidx = next((os.path.join(assets, f) for f in os.listdir(assets)
                    if f.startswith('chunk-entry-host-index-')), None)
    if not entry or not hostidx:
        sys.exit('找不到入口 chunk，版本可能变化较大，需要手工适配')

    # 1) 放语言包分片
    for f in (ZH_CHUNK, ZH_REVIEW):
        shutil.copyfile(os.path.join(PACK_DIR, f), os.path.join(assets, f))
    print('语言包分片写入完成')

    # 2) 注册 zh 语言
    s = open(entry, encoding='utf-8').read()
    if ZH_CHUNK in s:
        print('语言列表已注册 zh，跳过')
    else:
        m = re.search(r'\{code:`en`,label:`English`\},', s)
        if not m:
            sys.exit('找不到语言列表锚点，版本可能变化较大，需要手工适配')
        ins = (f'{{code:`zh`,label:`中文（简体）`,'
               f'translation:()=>import(`./{ZH_CHUNK}`).then(e=>e.default),'
               f'review:()=>import(`./{ZH_REVIEW}`).then(e=>e.default)}},')
        s = s[:m.end()] + ins + s[m.end():]
        open(entry, 'w', encoding='utf-8').write(s)
        print('已注册 中文（简体）')

    # 3) 启动时强制 zh（绕过服务端开关与账号里的语言设置）
    h = open(hostidx, encoding='utf-8').read()
    if '__devinZhOnce' in h:
        print('启动切换已存在，跳过')
    else:
        m = re.search(r'if\(!(\w+)\)\{(\w+)\(`en`\);return\}', h)
        if not m:
            sys.exit('找不到语言初始化锚点，版本可能变化较大，需要手工适配')
        changer = m.group(2)                       # 就是 changeLanguage 的封装
        anchor = re.search(r'\(\s*\(\)\s*=>\s*\{\s*let\s+\w+\s*=\s*\w+\([^)]*\);\s*if\(\w+\)return;', h)
        if not anchor:
            sys.exit('找不到启动 effect 锚点，需要手工适配')
        ins = f'if(!window.__devinZhOnce){{window.__devinZhOnce=1,{changer}(`zh`)}}return;'
        h = h[:anchor.end()] + ins + h[anchor.end():]
        open(hostidx, 'w', encoding='utf-8').write(h)
        print('已加入启动强制切换 zh')

    # 4) 重新签名（ad-hoc），否则 macOS 认为应用被篡改
    print('重新签名…')
    sh(['codesign', '--force', '--sign', '-', dst])
    print('签名完成')

    print(f'''
完成：{dst}

首次启动：
  · 会弹「Devin 想要使用你储存在钥匙串的 “Devin Safe Storage” 中的机密信息」
    → 输入登录密码并点「始终允许」（只弹一次）；若点拒绝，则需要重新登录 Devin。
  · 之后界面即为简体中文。

说明：
  · 会话内容、自动化模板等由 Devin 服务器下发的文本仍是英文，本地无法翻译。
  · Devin 自动更新可能会覆盖本改动；更新后重新运行本脚本即可。
''')


if __name__ == '__main__':
    main()

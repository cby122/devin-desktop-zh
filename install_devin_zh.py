#!/usr/bin/env python3
"""
给 Devin Desktop（Windsurf 内核）注入简体中文语言包，并生成可直接运行的中文版 App。

用法：
    python3 install_devin_zh.py
    python3 install_devin_zh.py --source /Applications/Devin.app --target "/Applications/Devin 中文版.app"
    python3 install_devin_zh.py --no-ide          # 只做代理界面，跳过编辑器半区

做的事（四步，全部可重复执行）：
    1. 克隆原版 App（APFS 写时复制，秒级），把 zh-Hans 词典分片放进 assets，注册 zh 并强制启动切中文。
    2. 用 ide_cache.json 里的词条对照，把编辑器半区三个主包里的英文硬编码替换成中文（可跳过）。
    3. 重算 product.json 的 checksums —— 不做这步 VS Code 完整性校验会弹「安装似乎损坏」。
    4. ad-hoc 重签名，并做一次自检（分片、注册、校验和、签名）。

首次启动会弹「Devin 想使用你储存在钥匙串中的机密信息」，输密码点「始终允许」即可（只一次）。
Devin 自动更新会覆盖这些文件；更新后重跑本脚本即可恢复到同样的中文界面。
"""
import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

PACK_DIR = os.path.dirname(os.path.abspath(__file__))
ZH_CHUNK = 'chunk-zh-hans-zhcn.js'
ZH_REVIEW = 'chunk-zh-review-zhcn.js'
IDE_CACHE = 'ide_cache.json'
IDE_FILES = [
    'workbench/workbench.desktop.main.js',
    'sessions/sessions.desktop.main.js',
    'workbench/windsurf-chat-client/index.js',
]


def sh(cmd, check=False):
    return subprocess.run(cmd, shell=isinstance(cmd, str), check=check,
                          capture_output=True, text=True)


def checksum(path):
    digest = hashlib.sha256(open(path, 'rb').read()).digest()
    return base64.b64encode(digest).decode().rstrip('=')


def apply_ide(app):
    """把编辑器半区的英文硬编码按词条表替换成中文，返回替换总数。"""
    cache_path = os.path.join(PACK_DIR, IDE_CACHE)
    if not os.path.exists(cache_path):
        print('· 没有 ide_cache.json，跳过编辑器半区')
        return 0

    cache = json.load(open(cache_path, encoding='utf-8'))

    def usable(zh):
        if not zh or not re.search(r'[\u4e00-\u9fff]', zh):
            return False
        if any(ch in zh for ch in ['"', '\\', '\n', '\r', '\t', '$']):
            return False
        return True

    pairs = {en: zh for en, zh in cache.items() if usable(zh)}
    if not pairs:
        print('· 词条表不可用，跳过编辑器半区')
        return 0

    literal = re.compile(r'"((?:[^"\\]|\\.)*)"')
    total = 0
    for rel in IDE_FILES:
        path = os.path.join(app, 'Contents/Resources/app/out/vs', rel)
        if not os.path.exists(path):
            print(f'· 缺少 {rel}，跳过')
            continue
        src = open(path, encoding='utf-8').read()
        out, last, count = [], 0, 0
        for m in literal.finditer(src):
            zh = pairs.get(m.group(1))
            if zh is None:
                continue
            out.append(src[last:m.start()])
            out.append('"' + zh + '"')
            last, count = m.end(), count + 1
        out.append(src[last:])
        open(path, 'w', encoding='utf-8').write(''.join(out))
        print(f'· {rel}: {count} 处')
        total += count
    return total


OPTION_MAP = {
    'default': '默认', 'none': '无', 'minimal': '极小', 'low': '低', 'medium': '中',
    'high': '高', 'xhigh': '极高', 'max': '最高', 'ultra': '极强', 'pro': '专业',
    'normal': '标准', 'fast': '快速', 'lite': '轻量', 'standard': '标准', 'auto': '自动',
    'balanced': '均衡', 'creative': '创意', 'precise': '精确', 'deep': '深入',
    'extended': '增强', 'verbose': '详细', 'concise': '简洁', 'thinking': '思考',
    'plan': '计划', 'code': '代码', 'ask': '询问', 'bypass': '跳过',
    'autonomous': '自主', 'build': '构建', 'review': '评审',
}

HARDCODED = [
    ('children:`No repositories found.`', 'children:`未找到代码仓库。`'),
    ('No repositories found for this enterprise', '该企业下未找到代码仓库'),
]


def apply_webapp(app):
    """渲染层补丁：ACP 下发的档位标签 + 少量硬编码文案。返回替换数。"""
    assets = os.path.join(
        app, 'Contents/Resources/app/out/vs/workbench/devin-webapp-host/assets')
    count = 0

    for name in os.listdir(assets):
        if not name.startswith('chunk-app-initial-') or not name.endswith('.js'):
            continue
        path = os.path.join(assets, name)
        src = open(path, encoding='utf-8').read()
        if 'label:c?.name??r' not in src:
            continue
        if '__devinZhOpts' in src:
            break
        helper = (
            'function __devinZhOpt(e,t){let k=typeof t==`string`?t.toLowerCase():``;'
            'let m=__devinZhOpts[k]||__devinZhOpts[(typeof e==`string`?e.toLowerCase():``)];'
            'return m||e}var __devinZhOpts={' +
            ','.join('%s:`%s`' % (k, v) for k, v in OPTION_MAP.items()) + '};\n')
        src = src.replace('function El({config:e,value:t', helper + 'function El({config:e,value:t', 1)
        src = src.replace('label:c?.name??r', 'label:__devinZhOpt(c?.name,c?.value)??r', 1)
        src = src.replace('children:[e.name,', 'children:[__devinZhOpt(e.name,e.value),', 1)
        open(path, 'w', encoding='utf-8').write(src)
        print(f'· 档位标签已注入：{name}')
        count += 1
        break

    for name in os.listdir(assets):
        if not name.endswith('.js') or name.startswith('chunk-zh'):
            continue
        path = os.path.join(assets, name)
        src = open(path, encoding='utf-8').read()
        new = src
        for old, zh in HARDCODED:
            new = new.replace(old, zh)
        if new != src:
            open(path, 'w', encoding='utf-8').write(new)
            count += 1
    return count


def fix_checksums(app):
    """重算 product.json 里所有 checksums，返回更新数量。"""
    product = os.path.join(app, 'Contents/Resources/app/product.json')
    data = json.load(open(product, encoding='utf-8'))
    app_root = os.path.join(app, 'Contents/Resources/app')
    updated = []
    for key in list(data.get('checksums', {})):
        target = os.path.join(app_root, 'out', key)
        if not os.path.exists(target):
            continue
        value = checksum(target)
        if data['checksums'][key] != value:
            data['checksums'][key] = value
            updated.append(key)
    if updated:
        json.dump(data, open(product, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=2)
    return updated


def register_locale(assets):
    entry = next((f for f in os.listdir(assets)
                  if f.startswith('chunk-entry-host-editor-mode-menu-')), None)
    hostidx = next((f for f in os.listdir(assets)
                    if f.startswith('chunk-entry-host-index-')), None)
    if not entry or not hostidx:
        sys.exit('找不到入口 chunk，版本可能变化较大，需要手工适配')

    entry_path = os.path.join(assets, entry)
    src = open(entry_path, encoding='utf-8').read()
    if ZH_CHUNK in src:
        print('· 语言列表已注册 zh，跳过')
    else:
        m = re.search(r'\{code:`en`,label:`English`\},', src)
        if not m:
            sys.exit('找不到语言列表锚点，版本可能变化较大，需要手工适配')
        ins = (f'{{code:`zh`,label:`中文（简体）`,'
               f'translation:()=>import(`./{ZH_CHUNK}`).then(e=>e.default),'
               f'review:()=>import(`./{ZH_REVIEW}`).then(e=>e.default)}},')
        open(entry_path, 'w', encoding='utf-8').write(
            src[:m.end()] + ins + src[m.end():])
        print('· 已注册 中文（简体）')

    host_path = os.path.join(assets, hostidx)
    src = open(host_path, encoding='utf-8').read()
    if '__devinZhOnce' in src:
        print('· 启动切换已存在，跳过')
        return
    m = re.search(r'if\(!(\w+)\)\{(\w+)\(`en`\);return\}', src)
    if not m:
        sys.exit('找不到语言初始化锚点，版本可能变化较大，需要手工适配')
    changer = m.group(2)
    anchor = re.search(r'\(\s*\(\)\s*=>\s*\{\s*let\s+\w+\s*=\s*\w+\([^)]*\);\s*if\(\w+\)return;', src)
    if not anchor:
        sys.exit('找不到启动 effect 锚点，需要手工适配')
    ins = f'if(!window.__devinZhOnce){{window.__devinZhOnce=1,{changer}(`zh`)}}return;'
    open(host_path, 'w', encoding='utf-8').write(
        src[:anchor.end()] + ins + src[anchor.end():])
    print('· 已加入启动强制切换 zh')


def self_check(app, assets):
    problems = []
    for name in (ZH_CHUNK, ZH_REVIEW):
        if not os.path.exists(os.path.join(assets, name)):
            problems.append(f'缺少语言分片 {name}')

    entries = [f for f in os.listdir(assets)
               if f.startswith('chunk-entry-host-editor-mode-menu-')]
    if not entries or '中文（简体）' not in open(
            os.path.join(assets, entries[0]), encoding='utf-8').read():
        problems.append('zh 语言未注册')

    data = json.load(open(os.path.join(app, 'Contents/Resources/app/product.json'),
                          encoding='utf-8'))
    for key, value in data.get('checksums', {}).items():
        target = os.path.join(app, 'Contents/Resources/app/out', key)
        if os.path.exists(target) and checksum(target) != value:
            problems.append(f'checksum 不一致：{key}')

    if sh(['codesign', '--verify', app]).returncode != 0:
        problems.append('签名校验未通过')
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', default='/Applications/Devin.app')
    ap.add_argument('--target', default='/Applications/Devin 中文版.app')
    ap.add_argument('--no-ide', action='store_true', help='跳过编辑器半区')
    args = ap.parse_args()

    src, dst = args.source, args.target
    if not os.path.isdir(src):
        sys.exit(f'找不到源 App：{src}')

    if os.path.exists(dst):
        print(f'目标已存在，直接在其上打补丁：{dst}')
    else:
        print(f'克隆 {src} -> {dst}')
        sh(['cp', '-cR', src, dst], check=True)
        sh(['xattr', '-d', 'com.apple.quarantine', dst])

    assets = os.path.join(
        dst, 'Contents/Resources/app/out/vs/workbench/devin-webapp-host/assets')
    if not os.path.isdir(assets):
        sys.exit('这个 App 不像 Devin Desktop（找不到 devin-webapp-host/assets）')

    print('1/5 写入语言分片与注册')
    for name in (ZH_CHUNK, ZH_REVIEW):
        shutil.copyfile(os.path.join(PACK_DIR, name), os.path.join(assets, name))
    print('· 语言包分片写入完成')
    register_locale(assets)

    print('2/5 编辑器半区')
    replaced = 0 if args.no_ide else apply_ide(dst)
    print(f'· 编辑器半区替换 {replaced} 处' if not args.no_ide else '· 已跳过')

    print('3/5 界面渲染层')
    webapp = apply_webapp(dst)
    print(f'· 渲染层补丁 {webapp} 项' if webapp else '· 无需处理')

    print('4/5 重算完整性校验')
    updated = fix_checksums(dst)
    print(f'· 更新 {len(updated)} 项 checksum' if updated else '· checksum 已一致')

    print('5/5 重新签名与自检')
    sh(['codesign', '--force', '--sign', '-', dst], check=True)
    print('· 签名完成')
    problems = self_check(dst, assets)
    if problems:
        print('自检发现问题：')
        for p in problems:
            print('  -', p)
        sys.exit(1)
    print('· 自检通过')

    print(f'''
完成：{dst}

首次启动：
  · 会弹「Devin 想要使用你储存在钥匙串的 “Devin Safe Storage” 中的机密信息」
    → 输入登录密码并点「始终允许」（只弹一次）；若点拒绝，则需要重新登录 Devin。
  · 之后界面即为简体中文。

说明：
  · 会话内容、会话标题、自动化模板等由 Devin 服务器下发的文本仍是英文，本地无法翻译。
  · Devin 自动更新可能会覆盖本改动；更新后重新运行本脚本即可。
''')


if __name__ == '__main__':
    main()

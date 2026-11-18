"""Patch the *embedded* i18next dictionaries that live inside the big editor bundles.

`out/vs/sessions/sessions.desktop.main.js` and
`out/vs/workbench/windsurf-chat-client/index.js` each carry their own complete
English dictionary as a JS literal next to `init({resources:{en:{translation:..,review:..}}})`:

    JSON.parse('{"guide":{"step":"Part {{number}} of {{total}}"...}')
    JSON.parse(`{"guide":...}`)          # sessions bundle uses a template literal

That layer is what keeps deep screens (Review / 评审 panel, merge manager,
reviewer sidebar, diff viewer) English no matter how many literals you translate
elsewhere. Usage:

    python3 tool-inline-dict.py dump  <bundle.js> <out.json>
    python3 tool-inline-dict.py patch <bundle.js> <zh.json> [--dry]

The anchor is `"openFullPr"` (present in every build so far): walk back to the
preceding `JSON.parse`, read its quote character, then scan to the matching
unescaped quote and JS-unescape the body before json.loads.
"""
import json, re, sys, os, shutil

ANCHOR = '"openFullPr"'

_ESC = {'n': '\n', 't': '\t', 'r': '\r', 'b': '\b', 'f': '\f', 'v': '\v', '0': '\0'}


def _unescape(raw: str) -> str:
    out, i, n = [], 0, len(raw)
    while i < n:
        c = raw[i]
        if c != '\\' or i + 1 >= n:
            out.append(c); i += 1; continue
        nxt = raw[i + 1]
        if nxt == 'x':
            out.append(chr(int(raw[i + 2:i + 4], 16))); i += 4
        elif nxt == 'u':
            if raw[i + 2] == '{':
                j = raw.index('}', i); out.append(chr(int(raw[i + 3:j], 16))); i = j + 1
            else:
                out.append(chr(int(raw[i + 2:i + 6], 16))); i += 6
        elif nxt in _ESC:
            out.append(_ESC[nxt]); i += 2
        elif nxt in '\\\'"`/$':
            out.append(nxt); i += 2
        elif nxt == '\n':
            i += 2
        else:
            out.append(nxt); i += 2
    return ''.join(out)


def locate(src: str):
    """-> (start, end, quote, body_start) of the JSON.parse literal body."""
    anchor = src.find(ANCHOR)
    if anchor < 0:
        raise SystemExit('anchor %s not found' % ANCHOR)
    p = src.rfind('JSON.parse', 0, anchor)
    if p < 0:
        raise SystemExit('JSON.parse before anchor not found')
    q = p + len('JSON.parse(')
    while q < len(src) and src[q] not in '\'"`':
        q += 1
    quote = src[q]
    i = q + 1
    while i < len(src):
        if src[i] == '\\':
            i += 2; continue
        if src[i] == quote:
            break
        i += 1
    return p, i + 1, quote, q + 1


def dump(path, out):
    src = open(path, encoding='utf-8').read()
    _, _, _, body = locate(src)
    end = locate(src)[1] - 1
    obj = json.loads(_unescape(src[body:end]))
    open(out, 'w', encoding='utf-8').write(json.dumps(obj, ensure_ascii=False, indent=1))
    print('%s: %d namespaces, %d strings -> %s' % (os.path.basename(path), len(obj), sum(len(v) for v in obj.values()), out))


def escape(text, quote):
    text = text.replace('\\', '\\\\')
    if quote == "'":
        text = text.replace("'", "\\'")
    elif quote == '`':
        text = text.replace('`', '\\`').replace('${', '\\${')
    return text.replace('\n', '\\n')


def patch(path, zh_path, dry=False):
    src = open(path, encoding='utf-8').read()
    start, end, quote, body = locate(src)
    old = json.loads(_unescape(src[body:end - 1]))
    new = json.load(open(zh_path, encoding='utf-8'))
    if set(new) != set(old):
        raise SystemExit('%s: namespace mismatch' % path)
    payload = escape(json.dumps(new, ensure_ascii=False, separators=(',', ':')), quote)
    out = src[:body] + payload + src[end - 1:]
    print('%s: %d -> %d chars' % (os.path.basename(path), len(src), len(out)))
    if dry:
        return
    shutil.copyfile(path, path + '.bak')
    open(path, 'w', encoding='utf-8').write(out)


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'dump':
        dump(sys.argv[2], sys.argv[3])
    elif cmd == 'patch':
        patch(sys.argv[2], sys.argv[3], '--dry' in sys.argv)
    else:
        raise SystemExit(__doc__)

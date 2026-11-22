"""Localize the ACP option labels (Default / Low / Medium / High / Xhigh / Max / Normal …).

Those labels are not in any dictionary — the Devin server or the ACP agent sends
`configOptions: [{id, name, options:[{value, name}]}]` at runtime, and the local
React select renders `option.name` verbatim:

    function El({config:e,value:t,onSelect:n,label:r,align:i,disabled:a,renderIcon:o}){
      let s=ea(e.options), c=s.find(e=>e.value===t);
      return jsx(vr,{ ... label: c?.name ?? r, children: s.map(e=>jsx(oi,{
        ... children:[e.name, …] })) })
    }

So the fix belongs at the render layer: map `value` (and the exact label text) to
Chinese inside that component. This is what turns the model / effort / mode
drop-downs (and the badge next to the send button) into 默认 / 低 / 中 / 高 / 极高 /
最高 / 标准 / 快速.

    python3 tool-option-labels.py <chunk-app-initial-*.js> [--dry]

The chunk name changes every build; pick the one that contains `label:c?.name??r`
(only one does). `node --check` after patching, then recompute product.json
checksums and re-sign the app.
"""
import sys, shutil

ANCHOR = 'function El({config:e,value:t'
MAP = {
    'default': '默认', 'none': '无', 'minimal': '极小', 'low': '低', 'medium': '中',
    'high': '高', 'xhigh': '极高', 'max': '最高', 'ultra': '极强', 'pro': '专业',
    'normal': '标准', 'fast': '快速', 'lite': '轻量', 'standard': '标准', 'auto': '自动',
    'balanced': '均衡', 'creative': '创意', 'precise': '精确', 'deep': '深入',
    'extended': '增强', 'verbose': '详细', 'concise': '简洁', 'thinking': '思考',
    'plan': '计划', 'code': '代码', 'ask': '询问', 'bypass': '跳过',
    'autonomous': '自主', 'build': '构建', 'review': '评审',
}

HELPER = (
    'function __devinZhOpt(e,t){let k=typeof t==`string`?t.toLowerCase():``;'
    'let m=__devinZhOpts[k]||__devinZhOpts[(typeof e==`string`?e.toLowerCase():``)];'
    'return m||e}var __devinZhOpts={' +
    ','.join('%s:`%s`' % (k, v) for k, v in MAP.items()) + '};\n'
)


def patch(path, dry=False):
    s = open(path, encoding='utf-8').read()
    if '__devinZhOpts' in s:
        print('already patched:', path); return
    if ANCHOR not in s or 'label:c?.name??r' not in s:
        raise SystemExit('not the option-render chunk: ' + path)
    s = s.replace(ANCHOR, HELPER + ANCHOR, 1)
    s = s.replace('label:c?.name??r', 'label:__devinZhOpt(e,c?.name)??r', 1)
    # keep the helper signature simple: (option, name)
    s = s.replace('__devinZhOpt(e,c?.name)', '__devinZhOpt(c?.name,c?.value)')
    s = s.replace('children:[e.name,', 'children:[__devinZhOpt(e.name,e.value),', 1)
    s = s.replace('function __devinZhOpt(e,t)', 'function __devinZhOpt(e,t)', 1)
    print('patched %s: %d -> %d chars' % (path.split('/')[-1], len(open(path, encoding='utf-8').read()), len(s)))
    if dry:
        return
    shutil.copyfile(path, path + '.bak')
    open(path, 'w', encoding='utf-8').write(s)


if __name__ == '__main__':
    patch(sys.argv[1], '--dry' in sys.argv)

import json, re, sys

FIX = {
    'accountTerms.title': '查看您的账户条款',
    'gitPermissions.mirroring.reviewAccess': '查看对 {{repo}} 的访问权限',
    'guardrails.items.deployment.example1': '将此应用直接部署到互联网，无需评审',
    'securityConfigure.skillNamePlaceholder': '认证评审',
}

def load(path):
    s = open(path, encoding='utf-8').read()
    return json.loads(s[s.find('{'):s.rfind('}') + 1])

def dump(path, obj):
    open(path, 'w', encoding='utf-8').write('export default ' + json.dumps(obj, ensure_ascii=False, separators=(',', ':')) + ';')

def fix_str(v):
    v = v.replace('管理员审核', '@@ADMIN@@')
    v = v.replace('审核', '评审')
    v = v.replace('@@ADMIN@@', '管理员审核')
    v = re.sub(r'([A-Za-z0-9])(?=[\u4e00-\u9fff])', r'\1 ', v)
    v = re.sub(r'([\u4e00-\u9fff])(?=[A-Za-z0-9])', r'\1 ', v)
    v = re.sub(r' {2,}', ' ', v)
    return v

for path in sys.argv[1:]:
    obj = load(path)
    ch = 0
    def walk(o, p=()):
        global ch
        if isinstance(o, dict):
            for k in list(o.keys()):
                key = '.'.join(p + (k,))
                if isinstance(o[k], str):
                    nv = FIX.get(key, fix_str(o[k]))
                    if nv != o[k]:
                        o[k] = nv; ch += 1
                else:
                    walk(o[k], p + (k,))
        elif isinstance(o, list):
            for i, x in enumerate(o):
                if isinstance(x, str):
                    o[i] = fix_str(x)
                    ch += 1
                else:
                    walk(x, p + (str(i),))
    walk(obj)
    dump(path, obj)
    print(path, 'changed', ch)
    items = {}
    def leaves(o, p=()):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, str): yield '.'.join(p + (k,)), v
                else: yield from leaves(v, p + (k,))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                if isinstance(v, str): yield '.'.join(p + (str(i),)), v
    import collections
    c = collections.Counter()
    for v in items.values() if items else []:
        pass
    for _, v in leaves(obj):
        for t in ['评审', '审核', '审查', '拉取请求']:
            if t in v: c[t] += 1
    print('  terms:', dict(c))
    print('  samples:', [v[:50] for _, v in list(leaves(obj))[:3]])

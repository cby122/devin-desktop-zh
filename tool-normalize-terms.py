import json, re, sys, collections

def load(path):
    s = open(path, encoding='utf-8').read()
    body = s[s.find('{'):s.rfind('}') + 1]
    return json.loads(body)

def dump(path, obj):
    open(path, 'w', encoding='utf-8').write('export default ' + json.dumps(obj, ensure_ascii=False, separators=(',', ':')) + ';')

def transform(v):
    v = v.replace('审核日志', '审计日志')
    for a, b in [('审查员', '评审员'), ('审查者', '评审者'), ('待审核', '待评审'),
                 ('审核者', '评审者'), ('审核员', '评审员'), ('审核人', '评审人'),
                 ('审核意见', '评审意见'), ('审核通过', '评审通过'), ('审核中', '评审中'),
                 ('等待审核', '等待评审'), ('重新审核', '重新评审'), ('请求审核', '请求评审'),
                 ('审查', '评审'), ('审阅', '评审'), ('拉取请求', 'PR')]:
        v = v.replace(a, b)
    v = re.sub('评审评审', '评审', v)
    v = re.sub(r'([A-Za-z0-9])(?=[\u4e00-\u9fff])', r'\1 ', v)
    return v

def walk(o, fn):
    if isinstance(o, dict):
        return {k: walk(v, fn) for k, v in o.items()}
    if isinstance(o, list):
        return [walk(v, fn) for v in o]
    if isinstance(o, str):
        return fn(o)
    return o

for path in sys.argv[1:]:
    obj = load(path)
    before = {}
    def collect(o, p=()):
        if isinstance(o, dict):
            for k, v in o.items():
                collect(v, p + (k,))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                collect(v, p + (str(i),))
        elif isinstance(o, str):
            before['.'.join(p)] = o
    collect(obj)
    new = walk(obj, transform)
    after = {}
    def collect2(o, p=()):
        if isinstance(o, dict):
            for k, v in o.items():
                collect2(v, p + (k,))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                collect2(v, p + (str(i),))
        elif isinstance(o, str):
            after['.'.join(p)] = o
    collect2(new)
    changed = [(k, before[k], after[k]) for k in before if before[k] != after[k]]
    dump(path, new)
    print(f'{path}: {len(before)} entries, changed {len(changed)}')
    for k, a, b in changed[:10]:
        print('  ', k, '\n     -', a[:90], '\n     +', b[:90])

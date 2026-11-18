import json,os,re

base='/Applications/Devin 中文版.app/Contents/Resources/app/out/vs/'
files=['workbench/workbench.desktop.main.js','sessions/sessions.desktop.main.js','workbench/windsurf-chat-client/index.js']
cache=json.load(open('ide_cache.json'))

def ok(en,zh):
    if not zh or zh==en: return False
    if any(ch in zh for ch in ['"','\\','\n','\r','\t','$']): return False
    if not re.search(r'[\u4e00-\u9fff]', zh): return False
    if len(zh)>len(en)*3+40: return False
    return True

pairs={en:zh for en,zh in cache.items() if ok(en,zh)}
print('usable pairs',len(pairs),flush=True)

lit=re.compile(r'"((?:[^"\\]|\\.)*)"')
total=0
for f in files:
    p=base+f
    s=open(p,encoding='utf-8').read()
    out=[]; last=0; n=0
    for m in lit.finditer(s):
        v=m.group(1)
        zh=pairs.get(v)
        if zh is None: continue
        out.append(s[last:m.start()])
        out.append('"'+zh+'"')
        last=m.end(); n+=1
    out.append(s[last:])
    new=''.join(out)
    open(p,'w',encoding='utf-8').write(new)
    print(f'{f}: {n} replacements',flush=True)
    total+=n
print('total',total)

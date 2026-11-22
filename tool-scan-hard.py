import json,re,os,sys,collections

def vals(o, out):
    if isinstance(o,dict):
        for v in o.values(): vals(v,out)
    elif isinstance(o,str): out.add(o.strip())

EN=set()
for f in ['en.json','en.review.json']:
    d=json.load(open(f)); s=set(); vals(d,s); EN|=s
print('en values', len(EN))

lit_re = re.compile(r'"((?:[^"\\\n]|\\.){2,120})"')
bad = re.compile(r'(https?:|\\\\|\$\{|function|return |=>|\.js|\.css|\.json|www\.|@|\\u[0-9a-f]{4})')
wordish = re.compile(r'[A-Za-z]{2,}')
skip_ext={'.map','.png','.svg','.wasm','.ttf','.woff','.woff2','.json','.css','.html','.md','.ogg','.mp3'}

roots=['out/vs/workbench/workbench.desktop.main.js','out/vs/sessions/sessions.desktop.main.js',
       'out/vs/workbench/windsurf-chat-client/index.js','out/vs/workbench/devin-webapp-host/index.js']
import glob
assets=glob.glob('out/vs/workbench/devin-webapp-host/assets/*.js')
files=roots+assets
cnt=collections.Counter(); where=collections.defaultdict(set)
for f in files:
    try:
        if os.path.getsize(f)>70*1024*1024: continue
        s=open(f,encoding='utf-8',errors='ignore').read()
    except Exception: continue
    if len(s)<10: continue
    for m in lit_re.finditer(s):
        t=m.group(1)
        if len(t)<3 or len(t)>90: continue
        if t.strip()!=t: continue
        if not wordish.search(t): continue
        if bad.search(t): continue
        if not re.search(r'[A-Z][a-z]{2,}| [A-Za-z]{2,}', t): continue
        if t in EN: continue
        # skip code-ish
        if re.fullmatch(r'[a-z0-9._-]+', t): continue
        if t.count(' ')==0 and len(t)<4: continue
        cnt[t]+=1; where[t].add(os.path.basename(f))
print('candidates', len(cnt))
json.dump({'counts':cnt.most_common(),'files':{k:list(v)[:3] for k,v in where.items()}}, open('hard_cand.json','w'), ensure_ascii=False)
for t,c in cnt.most_common(60):
    print(c, t[:80])

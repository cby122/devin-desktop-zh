import glob,re,os,json

D='workbench/devin-webapp-host/assets'
loc=re.compile(r'chunk-(de|ja|pt|es|fr|it|ko|ru|nl|pl|tr|zh)[-_]')
files=[f for f in glob.glob(D+'/*.js') if not loc.match(os.path.basename(f))]
files+=['workbench/workbench.desktop.main.js','sessions/sessions.desktop.main.js','workbench/windsurf-chat-client/index.js']

base=json.load(open(os.path.expanduser('~/DoubaoWork/chats/2026-11-17/new-chat-1/devin-zh/work/ide_cache.json')))
extra=json.load(open(os.path.expanduser('~/DoubaoWork/chats/2026-11-17/new-chat-1/devin-zh/work/pass2_cache.json'))) if os.path.exists(os.path.expanduser('~/DoubaoWork/chats/2026-11-17/new-chat-1/devin-zh/work/pass2_cache.json')) else {}
merged=dict(base); merged.update(extra)

def ok(en,zh):
    if not zh or zh==en: return False
    if any(c in zh for c in ['"','\\','`','$','\n','\r','\t']): return False
    if not re.search(r'[\u4e00-\u9fff]', zh): return False
    if len(zh)>len(en)*3+30: return False
    return True
M={k:v for k,v in merged.items() if ok(k,v)}
print('usable',len(M))

props="label|title|placeholder|aria-label|ariaLabel|tooltip|content|text|description|message|alt|confirmText|cancelText|emptyText|subtitle|caption|header|summary|hint|detail|statusText|unit|name"
A=re.compile(r'(?:"?'+props+r'"?)\s*:\s*("|`)([^"\'`\\$]{2,99})\1')
B=re.compile(r'children\s*:\s*\[\s*"([^"\\]{2,99})"')
C=re.compile(r'children\s*:\s*\[\s*`([^`\\$]{2,99})`')

total=0
for f in files:
    try: s=open(f,encoding='utf-8').read()
    except Exception: continue
    cnt=0
    def replA(m):
        global cnt
        q,v=m.group(1),m.group(2)
        zh=M.get(v.strip())
        if zh: cnt+=1; return m.group(0).replace(q+v+q, q+zh+q)
        return m.group(0)
    def replB(m):
        global cnt
        v=m.group(1); zh=M.get(v.strip())
        if zh: cnt+=1; return 'children:["'+zh+'"'
        return m.group(0)
    def replC(m):
        global cnt
        v=m.group(1); zh=M.get(v.strip())
        if zh: cnt+=1; return 'children:[`'+zh+'`'
        return m.group(0)
    newA,nA=A.subn(replA,s)
    newB,nB=B.subn(replB,newA)
    newC,nC=C.subn(replC,newB)
    if cnt:
        open(f,'w',encoding='utf-8').write(newC)
        print(f, cnt)
        total+=cnt
print('TOTAL', total)

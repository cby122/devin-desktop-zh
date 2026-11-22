import glob,re,os,json

D='workbench/devin-webapp-host/assets'
loc=re.compile(r'chunk-(de|ja|pt|es|fr|it|ko|ru|nl|pl|tr|zh)[-_]')
files=[f for f in glob.glob(D+'/*.js') if not loc.match(os.path.basename(f))]
files+=['workbench/workbench.desktop.main.js','sessions/sessions.desktop.main.js','workbench/windsurf-chat-client/index.js']

props="label|title|placeholder|aria-label|ariaLabel|tooltip|content|text|description|message|alt|confirmText|cancelText|emptyText|subtitle|caption|header|summary|hint|detail|statusText|unit|name"
# allows both bare key: "..." and quoted "key": "..."
A=re.compile(r'(?:"?'+props+r'"?)\s*:\s*("|`)([^"\'`\\$]{2,99})\1')
# JSX text children at start of array
B=re.compile(r'children\s*:\s*\[\s*"([^"\\]{2,99})"')
C=re.compile(r'children\s*:\s*\[\s*`([^`\\$]{2,99})`')

keep={}
for f in files:
    try: s=open(f,encoding='utf-8').read()
    except Exception: continue
    for rx in (A,B,C):
        for m in rx.finditer(s):
            v=(m.group(2) if rx is A else m.group(1)).strip()
            if not re.search(r'[A-Za-z]{3}',v): continue
            if not re.fullmatch(r"[A-Za-z0-9 ,.'!?()/&:+%\-–—#@*/=]{2,99}", v): continue
            if not re.match(r'^[A-Z(]', v): continue
            keep[v]=keep.get(v,0)+1
out=sorted(keep)
json.dump(out,open('/Users/kenny/DoubaoWork/chats/2026-11-17/new-chat-1/devin-zh/work/pass2_cand.json','w'),ensure_ascii=False)
print('candidates',len(out))
for t in ['Start a New Conversation','Close conversation','Past Conversations','Session','Actions','No conversation history','Close Devin panel']:
    print(t, t in keep)

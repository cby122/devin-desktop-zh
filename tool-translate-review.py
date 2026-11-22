import json,threading,time,urllib.request,urllib.parse,sys
def flat(o,p=''):
    d={}
    if isinstance(o,dict):
        for k,v in o.items(): d.update(flat(v,p+('.' if p else '')+k))
    elif isinstance(o,str): d[p]=o
    return d
en=flat(json.load(open('en.json')))
zh=flat(json.load(open('zh.json')))
vals={}
for k,v in en.items():
    if k in zh: vals.setdefault(v.strip(), zh[k])
rev=flat(json.load(open('/tmp/wcc_dict.json')))
try: cache=json.load(open('rev_cache.json'))
except: cache={}
for k,v in rev.items():
    if v.strip() in vals and k not in cache: cache[k]=vals[v.strip()]
todo=[(k,v) for k,v in rev.items() if k not in cache and v.strip()]
print('prefilled',len(cache),'todo',len(todo),flush=True)
lock=threading.Lock(); state={'done':0,'stop':False}
def tr(q):
    u='https://api.mymemory.translated.net/get?'+urllib.parse.urlencode({'q':q,'langpair':'en|zh-CN'})
    for a in range(4):
        try:
            r=json.loads(urllib.request.urlopen(u,timeout=25).read().decode('utf-8','ignore'))
        except Exception:
            time.sleep(4*(a+1)); continue
        if r.get('quotaFinished'): return None
        t=(r.get('responseData') or {}).get('translatedText')
        if t and 'MYMEMORY WARNING' not in t: return t
        time.sleep(4*(a+1))
    return None
def work(chunk):
    for k,v in chunk:
        if state['stop']: return
        try: t=tr(v)
        except Exception: t=None
        time.sleep(0.4)
        if t is None: state['stop']=True; return
        with lock:
            cache[k]=t; state['done']+=1
            if state['done']%40==0:
                json.dump(cache,open('rev_cache.json','w'),ensure_ascii=False)
                print(state['done'],'/',len(todo),flush=True)
n=2; size=(len(todo)+n-1)//n
ts=[threading.Thread(target=work,args=(todo[i*size:(i+1)*size],)) for i in range(n)]
[t.start() for t in ts]; [t.join() for t in ts]
json.dump(cache,open('rev_cache.json','w'),ensure_ascii=False)
print('cached',len(cache),flush=True)

import json,os,re,sys,threading,time,queue
sys.path.insert(0,'.')
from bing import Bing

CACHE='cache.json'
lock=threading.Lock()
cache={}
if os.path.exists(CACHE):
    cache=json.load(open(CACHE))

en=json.load(open('en.json')); rv=json.load(open('en.review.json'))
def leaves(o,path=()):
    for k,v in o.items():
        if isinstance(v,dict): yield from leaves(v,path+(k,))
        elif isinstance(v,str): yield path+(k,), v
lines=[]
pat=re.compile(r'[A-Za-z]')
for p,v in list(leaves(en))+[(('__review__',)+p,v) for p,v in leaves(rv)]:
    for line in v.split('\n'):
        if line.strip() and pat.search(line): lines.append(line)
uniq=sorted(set(lines))
todo=[l for l in uniq if l not in cache]
print('unique',len(uniq),'todo',len(todo),flush=True)

# build batches by char budget
batches=[]; cur=[]; clen=0
for l in todo:
    if cur and (clen+len(l)>2400 or len(cur)>=50):
        batches.append(cur); cur=[]; clen=0
    cur.append(l); clen+=len(l)+1
if cur: batches.append(cur)
print('batches',len(batches),flush=True)

q=queue.Queue()
for b in batches: q.put(b)

def save():
    tmp=CACHE+'.tmp'
    json.dump(cache,open(tmp,'w'),ensure_ascii=False)
    os.replace(tmp,CACHE)

done=[0]; errs=[0]
def worker():
    b=None
    try: b=Bing()
    except Exception as e: print('init fail',e,flush=True); return
    while True:
        try: batch=q.get_nowait()
        except queue.Empty: return
        try:
            out=b.tr('\n'.join(batch))
            ol=out.split('\n')
            if len(ol)!=len(batch):
                # bisect
                if len(batch)==1:
                    raise RuntimeError('line-count mismatch single')
                mid=len(batch)//2
                q.put(batch[:mid]); q.put(batch[mid:]); continue
            with lock:
                for s,t in zip(batch,ol):
                    cache[s]=t if t.strip() else s
                done[0]+=len(batch)
                if done[0]%500<50: save(); print('progress',done[0],'/',len(todo),flush=True)
        except Exception as e:
            with lock:
                errs[0]+=1
                if len(batch)==1 and errs[0]<200:
                    cache[batch[0]]=batch[0]  # keep english
                elif len(batch)==1:
                    cache[batch[0]]=batch[0]
                else:
                    mid=len(batch)//2
                    q.put(batch[:mid]); q.put(batch[mid:])
    # end

threads=[threading.Thread(target=worker,daemon=True) for _ in range(12)]
for t in threads: t.start()
for t in threads: t.join()
save()
print('DONE translated',done[0],'errors',errs[0],'cache',len(cache),flush=True)

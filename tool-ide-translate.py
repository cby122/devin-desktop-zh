import json,os,sys,threading,time,queue
sys.path.insert(0,'.')
from bing import Bing

CACHE='ide_cache.json'
lock=threading.Lock()
cache=json.load(open(CACHE)) if os.path.exists(CACHE) else {}

cand=json.load(open('ide_cand2.json'))
todo=[c for c in cand if c not in cache]
print('total',len(cand),'todo',len(todo),flush=True)

batches=[]; cur=[]; clen=0
for l in todo:
    if cur and (clen+len(l)>2200 or len(cur)>=40):
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
    try: b=Bing()
    except Exception as e:
        print('init fail',e,flush=True); return
    while True:
        try: batch=q.get_nowait()
        except queue.Empty: return
        try:
            out=b.tr('\n'.join(batch))
            ol=[x for x in out.split('\n')]
            if len(ol)!=len(batch):
                if len(batch)==1:
                    raise RuntimeError('mismatch single')
                mid=len(batch)//2
                q.put(batch[:mid]); q.put(batch[mid:]); continue
            with lock:
                for s,t in zip(batch,ol):
                    cache[s]=t.strip()
                done[0]+=len(batch)
                if done[0]%200<len(batch): save()
        except Exception as e:
            with lock: errs[0]+=1
            q.put(batch)
            time.sleep(1)

ts=[threading.Thread(target=worker,daemon=True) for _ in range(12)]
t0=time.time()
for t in ts: t.start()
for t in ts: t.join()
save()
print(f'DONE translated {len(cache)} errors {errs[0]} in {int(time.time()-t0)}s',flush=True)

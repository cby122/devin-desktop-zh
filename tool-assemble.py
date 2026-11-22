import json,re,os

en=json.load(open('en.json')); rv=json.load(open('en.review.json'))
cache=json.load(open('cache.json'))

def tr_line(line):
    if not line.strip(): return line
    if not re.search(r'[A-Za-z]', line): return line
    return cache.get(line, line)

def tr_text(v):
    return '\n'.join(tr_line(l) for l in v.split('\n'))

def walk(o):
    out={}
    for k,v in o.items():
        if isinstance(v,dict): out[k]=walk(v)
        elif isinstance(v,str): out[k]=tr_text(v)
        else: out[k]=v
    return out

zh=walk(en); zh_rev=walk(rv)

# glossary normalization pass on translated values
TERM=[
 ('現有', '现有'),
]
at = [('Devin 的计算机','Devin 的电脑')]

def fix(s):
    s=s.replace('布卢普林特','蓝图').replace('藍圖','蓝图').replace('蓝屏','蓝图')
    s=s.replace('劇本','剧本').replace('脚本册','剧本')
    s=s.replace('会話','会话').replace('交谈','会话')
    s=s.replace('工作空間','工作区').replace('工作空間','工作区')
    s=s.replace('快照','快照')
    return s

def fixwalk(o):
    for k,v in o.items():
        if isinstance(v,dict): fixwalk(v)
        elif isinstance(v,str): o[k]=fix(v)
    return o
fixwalk(zh); fixwalk(zh_rev)

json.dump(zh,open('zh.json','w'),ensure_ascii=False)
json.dump(zh_rev,open('zh.review.json','w'),ensure_ascii=False)
print('zh ns',len(zh),'rev ns',len(zh_rev))
print('translated ratio', round(sum(1 for l in cache if cache[l]!=l)/max(1,len(cache)),3))

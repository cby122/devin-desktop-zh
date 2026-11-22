import json,os,re,sys,shutil

APP=sys.argv[1] if len(sys.argv)>1 else '/Applications/Devin 中文版.app'
BASE=os.path.join(APP,'Contents/Resources/app/out/vs/workbench/devin-webapp-host')
ASSETS=os.path.join(BASE,'assets')
ENTRY=os.path.join(ASSETS,'chunk-entry-host-editor-mode-menu-BgZaFq8_.js')
HOSTIDX=os.path.join(ASSETS,'chunk-entry-host-index-BGc-OCn8.js')
ZHFILE='chunk-zh-hans-zhcn.js'
ZHREVIEW='chunk-zh-review-zhcn.js'

zh=json.load(open('zh.json')); zhr=json.load(open('zh.review.json'))
for name,data in ((ZHFILE,zh),(ZHREVIEW,zhr)):
    with open(os.path.join(ASSETS,name),'w',encoding='utf-8') as f:
        f.write('export default '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
print('chunks written', os.path.getsize(os.path.join(ASSETS,ZHFILE)), os.path.getsize(os.path.join(ASSETS,ZHREVIEW)))

# 1) register language in uu array
s=open(ENTRY,encoding='utf-8').read()
if 'chunk-zh-hans-zhcn' not in s:
    old='uu=[{code:`en`,label:`English`},'
    assert old in s, 'language array anchor not found'
    ext=('uu=[{code:`en`,label:`English`},'
         '{code:`zh`,label:`中文（简体）`,'
         f'translation:()=>import(`./{ZHFILE}`).then(e=>e.default),'
         f'review:()=>import(`./{ZHREVIEW}`).then(e=>e.default)}},')
    s=s.replace(old,ext,1)
    open(ENTRY,'w',encoding='utf-8').write(s)
    print('language entry added')
else:
    print('language entry already present')

# 2) force zh at startup
h=open(HOSTIDX,encoding='utf-8').read()
if '__devinZhOnce' not in h:
    anchor='W(()=>{let e=Kg(s);if(c)return;'
    assert anchor in h, 'host effect anchor not found'
    h=h.replace(anchor, anchor+'if(!window.__devinZhOnce){window.__devinZhOnce=1,Al(`zh`)}return;',1)
    open(HOSTIDX,'w',encoding='utf-8').write(h)
    print('startup locale force added')
else:
    print('locale force already present')

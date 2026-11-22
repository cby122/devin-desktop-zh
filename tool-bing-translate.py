import re,json,urllib.request,urllib.parse,http.cookiejar,time,sys
_UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36'
class Bing:
    def __init__(self):
        self.cj=http.cookiejar.CookieJar()
        self.op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
        self.op.addheaders=[('User-Agent',_UA)]
        self.refresh()
    def refresh(self):
        html=self.op.open('https://cn.bing.com/translator',timeout=20).read().decode('utf-8','ignore')
        m=re.search(r'params_AbusePreventionHelper\s*=\s*\[([^\]]+)\]',html)
        parts=[p.strip().strip('"') for p in m.group(1).split(',')]
        self.key,self.token=parts[0],parts[1]
        self.ig=re.search(r'IG:"([^"]+)"',html).group(1)
    def tr(self,text,frm='en',to='zh-Hans'):
        for attempt in range(3):
            try:
                data=urllib.parse.urlencode({'fromLang':frm,'to':to,'text':text,'token':self.token,'key':self.key}).encode()
                req=urllib.request.Request(f'https://cn.bing.com/ttranslatev3?isVertical=1&IG={self.ig}&IID=translator.5023',data=data,headers={'Content-Type':'application/x-www-form-urlencoded','Referer':'https://cn.bing.com/translator'})
                r=json.loads(self.op.open(req,timeout=25).read().decode('utf-8','ignore'))
                if isinstance(r,dict): self.refresh(); time.sleep(1); continue
                return r[0]['translations'][0]['text']
            except Exception as e:
                self.refresh(); time.sleep(1)
        raise RuntimeError('translate failed')

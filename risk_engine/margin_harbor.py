# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
from dataclasses import dataclass
import hashlib,json
def c(v,n=900):return str(v).strip()[:n]
def kid(v):
 x=c(v,72).upper()
 if not x:raise gl.vm.UserError('[EXPECTED] position id required')
 return x
def url(v):
 s=c(v,500);r=s[8:] if s.startswith('https://') else '';h=r.split('/')[0].lower();p=r[len(h):]
 if not h or '.' not in h or '@' in h or not p.startswith('/'):raise gl.vm.UserError('[EXPECTED] valid HTTPS source')
 return s,h
def obj(v):
 if isinstance(v,dict):return v
 s=str(v);a=s.find('{');b=s.rfind('}')
 if a<0 or b<=a:raise gl.vm.UserError('[LLM_ERROR] invalid JSON')
 return json.loads(s[a:b+1])
@allow_storage
@dataclass
class Position:owner:Address;terms:str;sources:str;epoch:u256;state:str;health:u256;signals:str;digests:str
class MarginHarbor(gl.Contract):
 positions:TreeMap[str,Position]
 def __init__(self):pass
 def _get(self,i):
  k=kid(i)
  if k not in self.positions:raise gl.vm.UserError('[EXPECTED] position not found')
  return k,self.positions[k]
 @gl.public.write
 def watch(self,i:str,terms:str,sources:list[str])->None:
  k=kid(i)
  if k in self.positions:raise gl.vm.UserError('[EXPECTED] duplicate position id')
  p=[url(x) for x in sources]
  if len(p)!=3 or len(set(x[1] for x in p))!=3:raise gl.vm.UserError('[EXPECTED] terms and two independent market hosts required')
  self.positions[k]=Position(gl.message.sender_address,c(terms,800),json.dumps([x[0] for x in p]),u256(0),'WATCHING',u256(0),'[]','[]')
 def _check(self,p,epoch):
  urls=json.loads(p.sources)
  def run():
   docs=[];dig=[]
   for ix,u in enumerate(urls):
    raw=gl.nondet.web.get(u).body[:14000];b=raw if isinstance(raw,bytes) else str(raw).encode();dig.append(hashlib.sha256(b).hexdigest());docs.append({'role':('terms','market_a','market_b')[ix],'body':b.decode(errors='replace')})
   q='Calculate bounded collateral health from terms and two market observations. JSON only {"health":0,"state":"WATCHING|WARNING|ACTIONABLE","signal_codes":[]}. Exact health is 0..200 and every field must follow the records. EPOCH:'+str(epoch)+' DOCS:'+json.dumps(docs)
   x=obj(gl.nondet.exec_prompt(q,response_format='json'));health=max(0,min(200,int(x.get('health',0))));state=c(x.get('state'),20).upper()
   if state not in ('WATCHING','WARNING','ACTIONABLE'):state='WARNING'
   return {'health':health,'state':state,'signals':sorted(set(c(x,80).upper() for x in x.get('signal_codes',[])[:20] if c(x,80))),'digests':dig}
  def valid(x):
   if not isinstance(x,gl.vm.Return):return False
   try:
    g=x.calldata;docs=[];dig=[]
    for ix,u in enumerate(urls):
     raw=gl.nondet.web.get(u).body[:14000];b=raw if isinstance(raw,bytes) else str(raw).encode();dig.append(hashlib.sha256(b).hexdigest());docs.append({'role':ix,'body':b.decode(errors='replace')})
    if g['digests']!=dig or not 0<=g['health']<=200:return False
    q='Verify exact health, state and every signal code. JSON only {"valid":true}. PROPOSAL:'+json.dumps(g)+' DOCS:'+json.dumps(docs)
    return bool(obj(gl.nondet.exec_prompt(q,response_format='json')).get('valid',False))
   except:return False
  return gl.vm.run_nondet_unsafe(run,valid)
 @gl.public.write
 def refresh(self,i:str,epoch:u256)->None:
  _,p=self._get(i)
  if int(epoch)<=int(p.epoch) or p.state=='ACTIONABLE':raise gl.vm.UserError('[EXPECTED] fresh active epoch required')
  x=self._check(p,int(epoch));p.epoch=epoch;p.health=u256(x['health']);p.state=x['state'];p.signals=json.dumps(x['signals']);p.digests=json.dumps(x['digests'])
 @gl.public.write
 def acknowledge_recovery(self,i:str)->None:
  _,p=self._get(i)
  if p.owner!=gl.message.sender_address or p.state!='WATCHING' or int(p.epoch)==0:raise gl.vm.UserError('[EXPECTED] owner healthy position required')
  p.state='RECOVERED'
 @gl.public.view
 def get_position(self,i:str)->dict:
  k,p=self._get(i);return {'id':k,'owner':p.owner.as_hex,'terms':p.terms,'sources':json.loads(p.sources),'epoch':int(p.epoch),'state':p.state,'health':int(p.health),'signalCodes':json.loads(p.signals),'digests':json.loads(p.digests)}

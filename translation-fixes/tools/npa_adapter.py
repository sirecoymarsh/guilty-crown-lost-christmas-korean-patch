from pathlib import Path
import ast,struct,zlib,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(r'F:\DOWN\Guilty-Crown-Lost-Christmas_Win_EN_Full-rip\GUILTY CROWN LOST XMAS')
ref=ast.parse((Path(__file__).resolve().parent/'npa_reference.py.txt').read_text(encoding='utf-8'))
KEY=ast.literal_eval(next(n.value for n in ref.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='key_table' for t in n.targets)))['LostX']
assert len(KEY)==256 and len(set(KEY))==256
INV=bytes(KEY.index(x) for x in range(256))
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
class NPA:
 def __init__(self,path):
  self.path=Path(path);self.blob=self.path.read_bytes();assert self.blob[:4]==b'NPA\1'
  self.k1,self.k2,self.comp,self.enc,self.n,self.nd,self.nf,self.table=struct.unpack_from('<ii??III8xI',self.blob,7)
  self.base=41+self.table;self.entries=[];pos=41;prod=self.k1*self.k2
  for idx in range(self.n):
   length,=struct.unpack_from('<I',self.blob,pos);pos+=4;raw=self.blob[pos:pos+length];pos+=length
   key=-sum(prod>>s for s in (24,16,8,0))-sum(idx>>s for s in (24,16,8,0))
   name=bytes((b+0xfc*j+key)&255 for j,b in enumerate(raw))
   typ,fid,off,stored,size=struct.unpack_from('<BIIII',self.blob,pos)
   self.entries.append({'idx':idx,'name':name.decode('cp932'),'name_bytes':name,'type':typ,'fid':fid,'off':off,'stored':stored,'size':size,'table_meta':pos});pos+=17
  assert pos==self.base
  assert len({e['name'] for e in self.entries})==self.n
 def raw(self,e):return self.blob[self.base+e['off']:self.base+e['off']+e['stored']]
 def crypt_key(self,e,size):return (((0x20101118-sum(e['name_bytes']))*len(e['name_bytes'])+self.k1*self.k2)*size)&255
 def read(self,e):
  data=bytearray(self.raw(e))
  if self.enc:
   k=self.crypt_key(e,e['size'])
   for j in range(min(len(data),0x1000+len(e['name_bytes']))):data[j]=(KEY[data[j]]-k-j)&255
  if self.comp:data=zlib.decompress(data)
  data=bytes(data);assert len(data)==e['size'];return data
 def pack(self,overrides):
  names={e['name'] for e in self.entries if e['type']==2};assert set(overrides)<=names
  prefix=bytearray(self.blob[:self.base]);payload=bytearray();last_end=0
  for e in self.entries:
   if e['type']!=2:continue
   assert e['off']>=last_end,('entry overlap/order',e['name'])
   gap=self.blob[self.base+last_end:self.base+e['off']];payload.extend(gap)
   off=len(payload);size=e['size'];raw=self.raw(e)
   if e['name'] in overrides:
    data=overrides[e['name']];size=len(data);raw=bytearray(zlib.compress(data,9) if self.comp else data)
    if self.enc:
     k=self.crypt_key(e,size)
     for j in range(min(len(raw),0x1000+len(e['name_bytes']))):raw[j]=INV[(raw[j]+k+j)&255]
   struct.pack_into('<III',prefix,e['table_meta']+5,off,len(raw),size)
   payload.extend(raw);last_end=e['off']+e['stored']
  payload.extend(self.blob[self.base+last_end:]);return bytes(prefix+payload)
if __name__=='__main__':
 out=ROOT/'engine';out.mkdir(exist_ok=True)
 arc=NPA(SOURCE/'nss.npa');assert sha(arc.blob)=='172ee59c5dfb9fc48a8eb8611b78a3c8564fe68f86168cbaa6191321962d6d02'
 nochange=arc.pack({});assert nochange==arc.blob
 p=out/'nss-nochange-172ee59c.npa';p.write_bytes(nochange);roundtrip=NPA(p)
 rows=[];opaque=[]
 for e,er in zip(arc.entries,roundtrip.entries):
  assert e==er
  if e['type']!=2:continue
  try:d=arc.read(e)
  except zlib.error:
   assert e['size']==2 and e['stored']==2 and e['name']=='function_lc_wam.nss' and arc.raw(e).hex()=='888a'
   assert arc.raw(e)==roundtrip.raw(er);opaque.append({'name':e['name'],'reason':'pre-existing two-byte entry decodes only to zlib header 789c without a stream body; retained opaque','raw_sha256':sha(arc.raw(e))});continue
  assert d==roundtrip.read(er);rows.append({'name':e['name'],'sha256':sha(d)})
 test=next(e for e in arc.entries if e['name'].endswith('lx0010.nss'))
 ov={test['name']:arc.read(test)};rebuilt=arc.pack(ov);assert rebuilt==arc.pack(ov)
 q=out/('nss-recompressed-'+sha(rebuilt)[:8]+'.npa');q.write_bytes(rebuilt);new=NPA(q)
 for e,en in zip(arc.entries,new.entries):
  assert e['name']==en['name'] and e['type']==en['type'] and e['fid']==en['fid']
  if e['type']!=2:continue
  if any(x['name']==e['name'] for x in opaque):assert arc.raw(e)==new.raw(en)
  else:assert arc.read(e)==new.read(en)
 report={'status':'pass','source_sha256':sha(arc.blob),'nochange_byte_identical':True,'entry_count':arc.n,'file_count':arc.nf,'folder_count':arc.nd,'compressed':arc.comp,'encrypted':arc.enc,'decoded_entries_verified':len(rows),'opaque_original_entries_preserved':opaque,'recompression_pilot':test['name'],'recompressed_archive_sha256':sha(rebuilt),'deterministic_recompression':True,'same_logical_payloads':True,'payloads':rows,'runtime':'not tested yet'}
 dump(out/'npa_roundtrip.json',report);print(json.dumps({k:v for k,v in report.items() if k!='payloads'},ensure_ascii=False,indent=2))
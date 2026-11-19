"""Bounded PE/COFF readers for relocation proof. No writes or reference-tree materialisation."""
import struct,hashlib
from pathlib import Path
U=lambda b,o=0:struct.unpack_from('<I',b,o)[0]
class PE:
 def __init__(self,path):
  self.path=Path(path);self.data=self.path.read_bytes();self.sha256=hashlib.sha256(self.data).hexdigest();pe=U(self.data,0x3c);opt=pe+24
  if self.data[pe:pe+4]!=b'PE\0\0' or struct.unpack_from('<H',self.data,opt)[0]!=0x10b:raise ValueError('not PE32')
  self.base=U(self.data,opt+28);self.sections=[]
  for i in range(struct.unpack_from('<H',self.data,pe+6)[0]):
   off=opt+struct.unpack_from('<H',self.data,pe+20)[0]+40*i
   self.sections.append({'name':self.data[off:off+8].split(b'\0')[0].decode(),'rva':U(self.data,off+12),'vsize':U(self.data,off+8),'raw_size':U(self.data,off+16),'raw':U(self.data,off+20),'flags':U(self.data,off+36)})
  self.imports={};rva,size=struct.unpack_from('<II',self.data,opt+104)
  if rva:
   for k in range(min(size//20+1,4096)):
    entry=self.read(rva+k*20,20);oft,stamp,chain,name,iat=struct.unpack('<5I',entry)
    if not any((oft,stamp,chain,name,iat)):break
    dll=self.cstring(name).decode('ascii');lookup=oft or iat
    for j in range(65536):
     val=U(self.read(lookup+j*4,4))
     if not val:break
     function=('#%d'%(val&0xffff)) if val&0x80000000 else self.cstring(val+2).decode('ascii')
     self.imports[iat+j*4]={'dll':dll,'name':function}
 def section(self,rva,n=1):
  for s in self.sections:
   if s['rva']<=rva and rva+n<=s['rva']+max(s['vsize'],s['raw_size']):return s
  raise ValueError('retail range outside image: 0x%X+%d'%(rva,n))
 def read(self,rva,n):
  if n<0 or n>16*1024*1024:raise ValueError('unbounded retail read')
  s=self.section(rva,n);off=rva-s['rva'];raw=min(n,max(0,s['raw_size']-off))
  return self.data[s['raw']+off:s['raw']+off+raw]+bytes(n-raw)
 def cstring(self,rva):
  out=bytearray()
  for i in range(65536):
   c=self.read(rva+i,1)
   if c==b'\0':return bytes(out)
   out+=c
  raise ValueError('unterminated retail string')
class COFF:
 def __init__(self,path):
  self.path=Path(path);self.data,self.sections,self.symbols=_read_object_layout(str(path));self.names={};self.assoc={};self.comdat={};self.weak={};table=U(self.data,8)
  for i,s in enumerate(self.symbols):
   if s.get('name'):self.names.setdefault(s['name'],[]).append(i)
   if s.get('storage')==105 and s.get('aux')==1:
    weak=self.data[table+(i+1)*18:table+(i+2)*18];self.weak[i]=(U(weak),U(weak,4))
   if s.get('aux') and s.get('section',0)>0 and s['name']==self.sections[s['section']-1]['name']:
    aux=self.data[table+(i+1)*18:table+(i+2)*18]
    if len(aux)==18:
     self.comdat[s['section']]=aux[14]
     if aux[14]==5:self.assoc[s['section']]=struct.unpack_from('<h',aux,12)[0]
 def root(self,section):
  seen=set()
  while section in self.assoc:
   if section in seen:raise ValueError('cyclic associative COMDAT')
   seen.add(section);section=self.assoc[section]
  return section
 def index(self,name):
  found=[i for i in self.names.get(name,[]) if self.symbols[i]['section']>0]
  if len(found)!=1:raise ValueError('ambiguous/undefined COFF symbol '+name)
  return found[0]
 def loc(self,index,add=0):
  s=self.symbols[index]
  if s['section']<=0:raise ValueError('undefined COFF symbol '+s['name'])
  return s['section'],s['value']+add
 def bytes(self,loc,n):
  sec,off=loc;s=self.sections[sec-1]
  if off<0 or n<0 or off+n>s['raw_size']:raise ValueError('COFF extent exceeds section')
  if s['raw_pointer']==0 and s['characteristics']&0x80:return bytes(n)
  return self.data[s['raw_pointer']+off:s['raw_pointer']+off+n]
 def relocs(self,loc,n):
  sec,start=loc;s=self.sections[sec-1];out=[]
  for k in range(s['reloc_count']):
   off,index,kind=struct.unpack_from('<IIH',self.data,s['reloc_pointer']+10*k)
   if start<=off<start+n:out.append((off-start,kind,index))
  return out
 def extent(self,index,code=False):
  s=self.symbols[index];sec=self.sections[s['section']-1];end=sec['raw_size']
  candidates=[x['value'] for x in self.symbols if x.get('section')==s['section'] and x.get('name') and x['value']>s['value'] and (not code or x.get('type',0)&32)
              and not (code and self.catch_label(x) and not s['name'].startswith('$L'))]
  if candidates:end=min(candidates)
  return end-s['value']
 def body(self,name,detail=False):
  i=self.index(name);s=self.symbols[i];n=self.extent(i,code=True);loc=self.loc(i);rels=self.relocs(loc,n)
  basic=(self.bytes(loc,n),[(o,k,self.symbols[j]['name']) for o,k,j in rels])
  return basic+({'section':loc[0],'value':loc[1],'symbols':self.symbols,'section_size':self.sections[loc[0]-1]['raw_size'],'reloc_symbols':[j for o,k,j in rels]},) if detail else basic
 def code_symbols(self):
  return list(dict.fromkeys(s['name'] for s in self.symbols if s.get('section',0)>0 and self.sections[s['section']-1]['characteristics']&32 and s.get('type',0)&32 and s.get('storage') in (2,3) and not s['name'].startswith('.') and not self.catch_label(s)))
 def catch_label(self,s):
  """gen5 b10_2: a $L symbol of a plain .text section that also defines a real function at a lower offset: a catch block
  or local label of that function, compared as part of it (MSVC 7.1; unwind funclets live in .text$x)."""
  if not s.get('name','').startswith('$L') or s.get('section',0)<=0 or self.sections[s['section']-1]['name']!='.text':return False
  first=getattr(self,'_first_function',None)
  if first is None:
   first=self._first_function={}
   for x in self.symbols:
    if x.get('name') and x.get('section',0)>0 and x.get('type',0)&32 and not x['name'].startswith(('$L','.')):
     first[x['section']]=min(first.get(x['section'],x['value']),x['value'])
  return s['section'] in first and first[s['section']]<=s['value']


# Stateless PE/COFF parsing excerpt from the pinned project tools/build.py.

def u16(data, offset):
    return struct.unpack_from("<H", data, offset)[0]

def u32(data, offset):
    return struct.unpack_from("<I", data, offset)[0]

def coff_name(data, symbol_offset, string_table):
    short_name = data[symbol_offset : symbol_offset + 8]
    if short_name[:4] == b"\0\0\0\0":
        string_offset = u32(short_name, 4)
        end = string_table.index(b"\0", string_offset)
        return string_table[string_offset:end].decode("ascii", errors="replace")
    return short_name.rstrip(b"\0").decode("ascii", errors="replace")

def read_object_symbols(data):
    symbol_table = u32(data, 8)
    symbol_count = u32(data, 12)
    string_table = data[symbol_table + symbol_count * 18 :]
    symbols = []
    index = 0
    while index < symbol_count:
        offset = symbol_table + index * 18
        name = coff_name(data, offset, string_table)
        value = u32(data, offset + 8)
        section_number = struct.unpack_from("<h", data, offset + 12)[0]
        aux_count = data[offset + 17]
        symbols.append({"name": name, "value": value, "section": section_number,
                        "storage": data[offset + 16], "aux": aux_count,
                        "type": u16(data, offset + 14)})
        for _ in range(aux_count):
            index += 1
            offset = symbol_table + index * 18
            symbols.append({"name": "", "value": 0, "section": 0, "aux": 0})
        index += 1
    return symbols

def defined_coff_indices(symbols):
    indices = {}
    for index, symbol in enumerate(symbols):
        if symbol["section"] > 0:
            indices.setdefault(symbol["name"], index)
    return indices

class IndexedCoffSymbols(list):
    """COFF records and their first definitions, owned by one parsed layout (and, once
    _function_starts asks, its function starts)."""

    def __init__(self, symbols):
        super().__init__(symbols)
        self.defined_indices = defined_coff_indices(self)
        self.function_starts = None

def _read_object_layout(path_str, mtime_ns=None, size=None, *, data=None):
    """The COFF layout (bytes, sections, IndexedCoffSymbols) of `data`, else of the file at `path_str`; no memo."""
    data = Path(path_str).read_bytes() if data is None else data
    section_count = u16(data, 2)
    section_table = 20

    sections = []
    for index in range(section_count):
        offset = section_table + index * 40
        sections.append(
            {
                "name": data[offset : offset + 8].rstrip(b"\0").decode("ascii", errors="replace"),
                "raw_size": u32(data, offset + 16),
                "raw_pointer": u32(data, offset + 20),
                "reloc_count": u16(data, offset + 32),
                "reloc_pointer": u32(data, offset + 24),
                "characteristics": u32(data, offset + 36),
            }
        )

    return data, sections, IndexedCoffSymbols(read_object_symbols(data))

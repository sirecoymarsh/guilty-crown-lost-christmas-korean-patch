from pathlib import Path
src = Path(r'F:\AI\gclx-4k\engine\src')
p = src / 'backlog_jump.inc'; s = p.read_text('utf-8')
old = 'static void drainAll(){'
assert s.count(old) == 1
s = s.replace(old, 'static void drainAll(){N2HD_Trace(116);struct DrainEnd{~DrainEnd(){N2HD_Trace(117);}}drainEnd;')
old2 = 'static int __cdecl jumpNormalSave(int id){'
assert s.count(old2) == 1
s = s.replace(old2, 'static int __cdecl jumpNormalSave(int id){N2HD_Trace(114);struct SaveEnd{~SaveEnd(){N2HD_Trace(115);}}saveEnd;')
# N2HD_Trace 선언이 drainAll 보다 앞에 있어야 함
decl = 'extern "C" void __cdecl N2HD_Trace(int);\n'
s = s.replace(decl, '')
s = s.replace('namespace Jump {', decl + 'namespace Jump {', 1)
p.write_text(s, 'utf-8')
q = src / 'hires_art.inc'; t = q.read_text('utf-8')
old3 = 'static const char* jn[]={"jump-begin","jump-saved","jump-archived","jump-end"};const char* nm=e.id==100?"loadbegin":e.id>=110&&e.id<114?jn[e.id-110]:'
assert t.count(old3) == 1
t = t.replace(old3, 'static const char* jn[]={"jump-begin","jump-saved","jump-archived","jump-end","normal-save-in","normal-save-out","drain-in","drain-out"};const char* nm=e.id==100?"loadbegin":e.id>=110&&e.id<118?jn[e.id-110]:')
q.write_text(t, 'utf-8')
print('ok')

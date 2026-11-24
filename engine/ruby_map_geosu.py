"""backlog_ruby_map.h 의 巨獣 두 줄(루비 「덩치 큰 놈이」·「괴물을」)을 「거대한 짐승」 대본에 맞춘다.
행: {단위 번호, 평문(공백 없앤 화면 글), 구간표, 구간 수}, 구간: {시작, 길이, 루비}. 평문의 「거수가/거수를」을 바꾸고
그 루비 구간 길이와 뒤 구간 시작을 옮긴다. merge_codex_1101.py 가 부른다; 따로 돌리면 보기만 한다.
"""
import re

SWAPS = {'거수가': '거대한짐승이', '거수를': '거대한짐승을'}   # 평문은 공백을 뺀다(코덱스 build_review.plain)
UNIT = re.compile(r'\{(\d+),L"((?:\\x[0-9a-f]{4})*)",rubySpans(\d+),(\d+)\}')
SPAN = re.compile(r'\{(\d+),(\d+),L"((?:\\x[0-9a-f]{4})*)"\}')


def dec(s):
    return re.sub(r'\\x([0-9a-f]{4})', lambda m: chr(int(m.group(1), 16)), s)


def enc(s):
    return ''.join('\\x%04x' % ord(c) for c in s)


def apply(h):
    changed = []
    for m in list(UNIT.finditer(h)):
        plain = dec(m.group(2))
        hit = [k for k in SWAPS if k in plain]
        if not hit:
            continue
        assert len(hit) == 1 and plain.count(hit[0]) == 1, plain
        old, new = hit[0], SWAPS[hit[0]]
        at, grow = plain.index(old), len(new) - len(old)
        idx = m.group(3)
        decl = re.search(r'static const RubySpanDef rubySpans%s\[\]=\{(.*?)\};' % idx, h)
        spans = [(int(a), int(b), r) for a, b, r in SPAN.findall(decl.group(1))]
        assert len(spans) == int(m.group(4))
        out, hits = [], 0
        for s, n, r in spans:
            if s == at and n == len(old):
                n += grow; hits += 1
            elif s > at:
                s += grow
            out.append((s, n, r))
        assert hits == 1, (plain, spans)
        new_plain = plain.replace(old, new)
        h = h.replace(decl.group(0), 'static const RubySpanDef rubySpans%s[]={%s};' % (idx, ','.join('{%d,%d,L"%s"}' % z for z in out)), 1)
        h = h.replace(m.group(0), '{%s,L"%s",rubySpans%s,%s}' % (m.group(1), enc(new_plain), idx, m.group(4)), 1)
        changed.append((int(m.group(1)), new_plain, [(s, n, dec(r)) for s, n, r in out]))
    assert len(changed) == 2, changed
    return h, changed


if __name__ == '__main__':
    import sys
    h = open(sys.argv[1], encoding='ascii').read()
    _, ch = apply(h)
    for c in ch:
        print(c)

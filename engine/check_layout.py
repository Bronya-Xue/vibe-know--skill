#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""布局体检：扫一遍 film.js 的坐标，看有没有元素压到仪表航道 / 掉进字幕带 / 出界。

用法：
    python engine/check_layout.py projects/bystander
    python engine/check_layout.py projects/bystander --json

三条跑道（改数字就改这里，和 film.js 里的 SAFE 保持一致）：
  · 仪表航道  x 64–410 / y 150–400（含仪表下面那行副标题）—— 内容不许进
  · 字幕带    y ≥ 790 开始渐暗 —— 信息类元素不许进；地面、虚化远景可以，用 @allow 放行
  · 版心      120 ≤ x ≤ 1800，y ≥ 100

它扫的是源码里的字面坐标，不是渲染结果。所以够快、够早 —— 写完就能跑，不用等渲染。
代价是只看得见写死的常数；算出来的坐标（lerp / 变量）扫不到，那部分仍要靠抽帧看。
"""
import io, json, os, re, sys

W, H = 1920, 1080
GAUGE = (64, 150, 410, 400)      # 仪表航道（含副标题那行）
SUB_BAND = 790                   # 字幕开始压暗的高度
MARGIN = (110, 1800, 70)   # 顶上那条留给年份标签        # 版心：x0, x1, y0


def parse_args_number(s, i):
    """从 s 的第 i 个位置往后，取出紧跟的若干数字字面量。"""
    nums, j = [], i
    while len(nums) < 4:
        m = re.compile(r'\s*,?\s*(-?\d+(?:\.\d+)?)').match(s, j)
        if not m:
            break
        nums.append(float(m.group(1)))
        j = m.end()
    return nums, j


def scan(path):
    src = io.open(path, encoding='utf-8').read().splitlines()
    boxes = []                    # (tag, x0, y0, x1, y1, line, note)

    def add(tag, x0, y0, x1, y1, ln, note=''):
        # fr.g({at:[x,y]}) 里用的是相对坐标，中心在原点附近 —— 不算出界
        if abs((x0 + x1) / 2) < 200 and abs((y0 + y1) / 2) < 200 and x0 <= 0 <= x1:
            return
        boxes.append((tag, x0, y0, x1, y1, ln, note))

    for ln, s in enumerate(src, 1):
        t = s.strip()
        if t.startswith(('//', '*', '/*')):
            continue
        if '@allow' in t:         # 地面 / 远景：明确放行
            continue

        # stage(fr, x0, y0, x1, y1, ...)
        for m in re.finditer(r'stage\(fr,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)', t):
            a, b, c, d = map(float, m.groups())
            add('stage底板', a, b, c, d, ln)

        # fr.text('...', x, y, { ... size: N ... align: 'l'|'r' })
        for m in re.finditer(r'fr\.text\(\s*((?:\'[^\']*\'|"[^"]*"|[^,]+?))\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*\{([^}]*)\}', t):
            raw, x, y = m.group(1), float(m.group(2)), float(m.group(3))
            opt = m.group(4)
            sm = re.search(r'size:\s*(\d+(?:\.\d+)?)', opt)
            size = float(sm.group(1)) if sm else 34
            am = re.search(r'align:\s*[\'"](\w)[\'"]', opt)
            align = am.group(1) if am else 'c'
            if '+' in raw or raw[:1] not in ("'", '"'):
                continue                       # 拼接表达式 / 变量：宽度估不了，跳过
            txt = raw.strip('\'"')
            n = sum(2 if ord(ch) > 0x2E80 else 1 for ch in txt)
            w = n * size * 0.62
            h = size * 1.2
            if align == 'l':
                x0, x1 = x, x + w
            elif align == 'r':
                x0, x1 = x - w, x
            else:
                x0, x1 = x - w / 2, x + w / 2
            add('fr.text', x0, y - h / 2, x1, y + h / 2, ln, txt[:18])

        # 整块函数：(monitor|labRoom|apartment|stageFull|monitorFull)(fr, x0, y0, x1, y1)
        for m in re.finditer(r'\b(monitorFull|monitor|labRoom|apartment|apartSmall)\(fr,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)', t):
            nm = m.group(1)
            a, b, c, d = map(float, m.groups()[1:])
            add(nm, a, b, c, d, ln)

    return boxes


def check(boxes):
    """返回 [(严重度, 元素, 行, 说明, 包围盒)]"""
    out = []
    gx0, gy0, gx1, gy1 = GAUGE
    mx0, mx1, my0 = MARGIN
    for tag, x0, y0, x1, y1, ln, note in boxes:
        # 压仪表
        ox0, ox1 = max(x0, gx0), min(x1, gx1)
        oy0, oy1 = max(y0, gy0), min(y1, gy1)
        if ox1 > ox0 and oy1 > oy0:
            out.append(('错', tag, ln, f'压住仪表航道 {(ox1-ox0):.0f}×{(oy1-oy0):.0f}px',
                        (x0, y0, x1, y1), note))
        # 掉进字幕带
        if y1 > SUB_BAND:
            out.append(('错', tag, ln, f'伸进字幕带，超出 {y1 - SUB_BAND:.0f}px',
                        (x0, y0, x1, y1), note))
        # 出界
        if x0 < mx0 or x1 > mx1 or y0 < my0:
            out.append(('警', tag, ln, '超出版心留白', (x0, y0, x1, y1), note))
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    as_json = '--json' in sys.argv
    if not args:
        print(__doc__)
        return 2
    proj = args[0]
    fjs = os.path.join(proj, 'film.js')
    if not os.path.exists(fjs):
        fjs = proj if os.path.isfile(proj) else None
    if not fjs:
        print('找不到 film.js：', args[0])
        return 2

    boxes = scan(fjs)
    issues = check(boxes)
    if as_json:
        print(json.dumps([{'level': lv, 'what': tag, 'line': ln, 'why': why,
                           'box': bb, 'note': note} for lv, tag, ln, why, note in [(i[0], i[1], i[2], i[3], i[5]) for i in issues]],
                         ensure_ascii=False, indent=1))
        return 0

    print(f'扫描 {fjs}：{len(boxes)} 个带坐标的元素')
    if not issues:
        print('  ✅ 没有压到仪表航道，没有掉进字幕带，没有出界。')
        return 0
    print(f'  ⚠️  {len(issues)} 处：')
    for lv, tag, ln, why, bb, note in issues:
        extra = '  「%s」' % note if note else ''
        print(f'   [{lv}] 行{ln:>4} {tag:<12} {why:<28} {bb}{extra}')
    return 1


if __name__ == '__main__':
    sys.exit(main())

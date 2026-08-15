# -*- coding: utf-8 -*-
"""把 edge-tts 的词级时间戳合并成短句字幕。

WordBoundary 的 text 不带标点，这里用原始讲稿做逐词对齐，把标点归还到词尾，
再按「标点优先断句 + 单条最长 MAXLEN 字」聚合成适合烧录的短句 cue。
"""
import json
import sys

MAXLEN = 18          # 单条字幕最大字数
BREAK = "。！？；，、：\n"   # 断句标点，前四个为强断点
STRONG = "。！？；\n"


def ts(sec):
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round(s % 1 * 1000)):03d}"


def align(text, marks):
    """把原文标点对齐回每个词，返回 [(词+尾随标点, start, end)]。"""
    out, pos = [], 0
    for m in marks:
        w = m["text"]
        i = text.find(w, pos)
        if i < 0:                      # 对不上就原样保留
            out.append([w, m["start"], m["start"] + m["dur"]])
            continue
        j = i + len(w)
        # 吞掉紧跟其后的标点与空白
        while j < len(text) and (text[j] in BREAK or text[j].isspace()):
            j += 1
        out.append([text[i:j].strip(), m["start"], m["start"] + m["dur"]])
        pos = j
    return out


MINLEN = 6           # 短于此长度的尾块并回前一块


def _pack(chunk):
    """把一串 [词, start, end] 压成一条 cue。"""
    return ("".join(w for w, _, _ in chunk).strip(), chunk[0][1], chunk[-1][2])


def _split_on(chunk, marks_set):
    """在指定标点处切分词序列，返回若干子序列。"""
    subs, cur = [], []
    for item in chunk:
        cur.append(item)
        if item[0] and item[0][-1] in marks_set:
            subs.append(cur)
            cur = []
    if cur:
        subs.append(cur)
    return subs


def _even(chunk):
    """无标点可依时，按词边界近似均分到 MAXLEN 以内。"""
    total = sum(len(w) for w, _, _ in chunk)
    parts = max(1, -(-total // MAXLEN))
    target = -(-total // parts)
    subs, cur, n = [], [], 0
    for item in chunk:
        cur.append(item)
        n += len(item[0])
        if n >= target and len(subs) < parts - 1:
            subs.append(cur)
            cur, n = [], 0
    if cur:
        subs.append(cur)
    return subs


def merge(words):
    cues = []
    # 一级：按强标点聚成完整句
    for sent in _split_on(words, STRONG):
        if not sent:
            continue
        if sum(len(w) for w, _, _ in sent) <= MAXLEN:
            cues.append(_pack(sent))
            continue
        # 二级：句太长，在次级标点处细分
        pieces, buf = [], []
        for sub in _split_on(sent, "，、：,"):
            if buf and sum(len(w) for w, _, _ in buf + sub) > MAXLEN:
                pieces.append(buf)
                buf = list(sub)
            else:
                buf += sub
        if buf:
            pieces.append(buf)
        # 三级：仍超长的块按词边界均分
        for p in pieces:
            if sum(len(w) for w, _, _ in p) > MAXLEN:
                cues.extend(_pack(x) for x in _even(p))
            else:
                cues.append(_pack(p))

    # 收尾：过短的碎片并回前一条
    out = []
    for t, s, e in cues:
        if out and len(t) < MINLEN and len(out[-1][0]) + len(t) <= MAXLEN + 4:
            pt, ps, _ = out[-1]
            out[-1] = (pt + t, ps, e)
        else:
            out.append((t, s, e))
    return out


def to_srt(cues):
    out = []
    for i, (t, s, e) in enumerate(cues, 1):
        out.append(f"{i}\n{ts(s)} --> {ts(e)}\n{t}\n")
    return "\n".join(out)


if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "all" else None
    outdir = sys.argv[2] if len(sys.argv) > 2 else "试听_edge"

    text = open("sample_text.txt", encoding="utf-8").read().strip()
    data = json.load(open(f"{outdir}/word_timestamps.json", encoding="utf-8"))
    keys = [key] if key else list(data)

    for k in keys:
        cues = merge(align(text, data[k]["marks"]))
        open(f"{outdir}/{k}_短句字幕.srt", "w", encoding="utf-8").write(to_srt(cues))
        print(f"{k}: 词级 {len(data[k]['marks'])} 条 → 短句 {len(cues)} 条")

    if len(keys) == 1:
        print()
        for t, s, e in merge(align(text, data[keys[0]]["marks"])):
            print(f"  {s:6.2f} → {e:6.2f}  ({len(t):2d}字) {t}")

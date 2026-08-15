#!/usr/bin/env python3
"""
compose_subtitled_video.py — 把已渲染的幻灯片 PNG + 每页配音 mp3 + 每页 ASR 词级时间戳
合成带 PIL 烧录字幕的 1080p 课程视频。

本机 ffmpeg 常缺 libass/freetype，drawtext/subtitles 滤镜不可用，故字幕改用 PIL
逐条合成 PNG 再 concat（每条字幕一张底图叠字幕条），最后逐页拼接。

目录约定（均可用参数覆盖）：
  slides/slide_001.png ...   幻灯片图（PDF 300dpi 渲染）
  audio/p01.mp3 ...          每页配音（页数与幻灯片一致）
  asr_pages/p01.json ...     每页配音的 ASR 结果（qwen-audio-3.0-asr-flash-filetrans 或 fun-asr，
                             结构一致，含 transcripts[0].sentences[].words[]）

文本清洗（product/fillers/corrections/term_case）从 --config JSON 读取，随课程不同而变，
不写死在脚本里。示例见 skill 的 assets/subtitle_config.example.json。

用法：
  python3 compose_subtitled_video.py \
    --slides slides --audio audio --asr asr_pages \
    --font "/Users/<you>/Library/Fonts/DingTalk JinBuTi.ttf" \
    --config subtitle_config.json \
    --out outputs/课程视频_字幕.mp4
可用 ONLY=8 环境变量只跑第 8 页做预览。
"""
import argparse, json, os, re, subprocess, sys, tempfile, glob
from PIL import Image, ImageDraw, ImageFont

def dur(p):
    return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","csv=p=0",p],capture_output=True,text=True).stdout.strip())

def load_config(path):
    cfg={"product_replace":[],"fillers":"呃嗯啊唉哦","corrections":[],
         "term_case":{"agent":"Agent","skill":"Skill"}}
    if path and os.path.exists(path):
        cfg.update(json.load(open(path,encoding="utf-8")))
    return cfg

class Composer:
    def __init__(self,a):
        self.W,self.H=1920,1080
        self.slides=a.slides; self.audio=a.audio; self.asr=a.asr
        self.imgdir=a.workdir; os.makedirs(self.imgdir,exist_ok=True)
        self.FS=a.fs; self.LEAD=a.lead; self.FADE=a.fade
        self.font=ImageFont.truetype(a.font,self.FS)
        self.cfg=load_config(a.config)
        self.GAP=a.gap; self.MINLEN=a.minlen; self.MAXLEN=a.maxlen; self.MINDUR=a.mindur
        self.MINCHARS=a.minchars; self.HOLDGAP=a.holdgap
        self.out=a.out

    # ---------- text normalization ----------
    def normalize(self,t):
        for x,y in self.cfg.get("product_replace",[]):
            t=t.replace(x,y)
        t=re.sub(r"\s+"," ",t).strip()
        t=re.sub(r"(?<=[A-Za-z])\s(?=[A-Za-z])","",t)  # "A G E N T" -> "AGENT"
        for ch in self.cfg.get("fillers",""):           # drop filler interjections
            t=t.replace(ch,"")
        for a,b in self.cfg.get("corrections",[]):
            t=t.replace(a,b)
        for low,canon in self.cfg.get("term_case",{}).items():
            t=re.sub(rf"(?i)(?<![A-Za-z]){re.escape(low)}(?![A-Za-z])",canon,t)
        t=re.sub(r"\s+"," ",t).strip()
        return t

    # ---------- image building ----------
    def base_canvas(self,i):
        out=f"{self.imgdir}/base_{i:02d}.png"
        if not os.path.exists(out):
            im=Image.open(f"{self.slides}/slide_{i:03d}.png").convert("RGB")
            r=min(self.W/im.width,self.H/im.height); nw,nh=int(im.width*r),int(im.height*r)
            im=im.resize((nw,nh))
            c=Image.new("RGB",(self.W,self.H),"white"); c.paste(im,((self.W-nw)//2,(self.H-nh)//2))
            c.save(out)
        return out

    def wrap_text(self,text,maxw,draw):
        lines=[]; cur=""
        for ch in text:
            if draw.textlength(cur+ch,font=self.font)<=maxw: cur+=ch
            else: lines.append(cur); cur=ch
        if cur: lines.append(cur)
        return lines[:2]   # short chunks: usually 1 line, hard cap 2

    def sub_image(self,i,k,text):
        out=f"{self.imgdir}/p{i:02d}_{k:03d}.png"
        if os.path.exists(out): return out
        c=Image.open(self.base_canvas(i)).convert("RGBA")
        ov=Image.new("RGBA",(self.W,self.H),(0,0,0,0)); d=ImageDraw.Draw(ov)
        maxw=int(self.W*0.86)
        lines=self.wrap_text(text,maxw,d)
        lh=self.FS+14; th=lh*len(lines)
        tw=max(d.textlength(ln,font=self.font) for ln in lines)
        barw=int(tw+72); barh=int(th+34)
        bx0=(self.W-barw)//2; by1=self.H-46; by0=by1-barh
        d.rounded_rectangle([bx0,by0,bx0+barw,by1],radius=18,fill=(0,0,0,150))
        y=by0+17
        for ln in lines:
            lw=d.textlength(ln,font=self.font)
            d.text(((self.W-lw)//2,y),ln,font=self.font,fill=(255,255,255,255),
                   stroke_width=2,stroke_fill=(0,0,0,220))
            y+=lh
        Image.alpha_composite(c,ov).convert("RGB").save(out)
        return out

    # ---------- subtitle timing ----------
    LEADPUNCT = '”’"\'》】）」』，。、！？；：…·—'
    TAILPUNCT = '“‘「『（《【〔'                     # 前引号/前括号不能留在行尾，须搬到下一条
    LEADWEAK = '的地得了'
    TAILWEAK = '就也都还把被从对向让这那是在很更又再而和与及或'   # 与 LEADWEAK 不重叠，避免来回搬字

    def _visible(self,t):
        return re.sub(r"[^\w\u4e00-\u9fff]","",t)

    def _terms(self):
        terms=list(self.cfg.get("protect",[]))+[y for _,y in self.cfg.get("product_replace",[])]
        return [t for t in dict.fromkeys(terms) if len(t)>1]

    def _protect_terms(self,raw):
        """避免品牌词/术语被硬断成两条（如"…千"/"问办公…"）。"""
        terms=self._terms()
        for i in range(len(raw)-1):
            for p in terms:
                hit=False
                for k in range(1,len(p)):
                    head,tail=p[:k],p[k:]
                    if raw[i][2].endswith(head) and raw[i+1][2].startswith(tail):
                        raw[i][2]=raw[i][2][:-len(head)]
                        raw[i+1][2]=head+raw[i+1][2]
                        hit=True; break
                if hit: break
        # 数字串保护：ASR 会把中文数词逆归一成阿拉伯数字（一万八千 -> 18000），
        # 硬断可能落在数字中间，出现"他扫描了18"/"000个实例"这种断法。
        for i in range(len(raw)-1):
            m=re.search(r"\d+$",raw[i][2])
            if not m or not re.match(r"^\d",raw[i+1][2]): continue
            head=m.group(0)
            if len(self._visible(raw[i][2]))-len(head)>=self.MINCHARS:
                raw[i][2]=raw[i][2][:-len(head)]
                raw[i+1][2]=head+raw[i+1][2]
            else:
                m2=re.match(r"^\d+",raw[i+1][2])
                raw[i][2]+=m2.group(0)
                raw[i+1][2]=raw[i+1][2][len(m2.group(0)):]
        return [r for r in raw if r[2].strip()]

    def _wordsafe(self,raw):
        """通用词边界保护：maxlen 硬断可能把词劈开（"维/度"、"返/回"），
        用 jieba 判断断点是否落在词中间，是则把残头搬到下一条。jieba 缺失时静默跳过。"""
        try:
            import jieba
        except ImportError:
            return raw
        CJK=lambda ch: '\u4e00'<=ch<='\u9fff'
        for i in range(len(raw)-1):
            a,b=raw[i][2],raw[i+1][2]
            if not a or not b or not (CJK(a[-1]) and CJK(b[0])): continue
            ta,tb=a[-6:],b[:6]
            pos=0; head=None
            for t in jieba.cut(ta+tb):
                if pos<len(ta)<pos+len(t):
                    if len(t)<=4: head=t[:len(ta)-pos]
                    break
                pos+=len(t)
            if not head or len(head)>2: continue
            if len(self._visible(a))-len(head)<self.MINCHARS: continue
            raw[i][2]=a[:-len(head)]; raw[i+1][2]=head+b
        return raw

    def _tidy(self,raw):
        """开头标点移到上一条；过短碎片(如单字'的')并入邻条。"""
        raw=self._protect_terms(raw)
        terms=self._terms()
        for i,r in enumerate(raw):
            while r[2] and r[2][0] in self.LEADPUNCT:
                ch=r[2][0]; r[2]=r[2][1:]
                if i>0: raw[i-1][2]+=ch
            while (i>0 and len(r[2])>1 and r[2][0] in self.LEADWEAK
                   and not any(r[2].startswith(p) for p in terms)):  # "得到"这类词不拆
                raw[i-1][2]+=r[2][0]; r[2]=r[2][1:]   # 避免"的…"这类断头字幕
        for i in range(len(raw)-1):                    # 前引号/前括号不留行尾
            while raw[i][2] and raw[i][2][-1] in self.TAILPUNCT:
                raw[i+1][2]=raw[i][2][-1]+raw[i+1][2]; raw[i][2]=raw[i][2][:-1]
        for i in range(len(raw)-1):                    # 避免"…出错。就"这类断尾字幕
            while len(self._visible(raw[i][2]))>3:
                m=re.search(r"([\u4e00-\u9fff])([，、；：]*)$",raw[i][2])  # 句末标点结尾视为完整句，不搬
                if not m or m.group(1) not in self.TAILWEAK: break
                raw[i+1][2]=m.group(1)+m.group(2)+raw[i+1][2]
                raw[i][2]=raw[i][2][:m.start()]
        raw=self._wordsafe(raw)                        # 最后统一修硬断劈词
        out=[]
        for r in raw:
            if not r[2].strip():
                if out: out[-1][1]=r[1]
                continue
            if out and len(self._visible(r[2]))<self.MINCHARS:
                out[-1][1]=r[1]; out[-1][2]+=r[2]
            else:
                out.append(r)
        merged=[]; i=0
        while i<len(out):
            cur=out[i]
            if len(self._visible(cur[2]))<self.MINCHARS and i+1<len(out):
                nxt=out[i+1]; nxt[0]=cur[0]; nxt[2]=cur[2]+nxt[2]; i+=1; continue
            merged.append(cur); i+=1
        return [(a,b,t) for a,b,t in merged]

    def chunk_words(self,words):
        toks=[(w["begin_time"]/1000.0,w["end_time"]/1000.0,w["text"],w.get("punctuation") or "")
              for w in words]
        raw=[]; buf=[]; blen=0; start=None; prev_end=None
        for wb,we,wt,wp in toks:
            gap=(wb-prev_end) if prev_end is not None else 0.0
            if buf and ((blen>=self.MINLEN and gap>=self.GAP) or blen>=self.MAXLEN):
                raw.append([start,prev_end,"".join(buf)]); buf=[]; blen=0; start=None
            if start is None: start=wb
            buf.append(wt+wp); blen+=len(wt); prev_end=we
            if wp and wp in "，。、！？；：" and blen>=self.MINLEN:   # 优先在标点处断句
                raw.append([start,we,"".join(buf)]); buf=[]; blen=0; start=None
        if buf: raw.append([start,prev_end,"".join(buf)])
        return self._tidy(raw)

    def intervals(self,i,seg):
        data=json.load(open(f"{self.asr}/p{i:02d}.json",encoding="utf-8"))
        sents=data["transcripts"][0]["sentences"]
        raw=[]
        for s in sents:
            ws=s.get("words") or []
            if ws:
                for a,b,txt in self.chunk_words(ws):
                    raw.append([self.LEAD+a,self.LEAD+b,self.normalize(txt)])
            else:
                raw.append([self.LEAD+s["begin_time"]/1000.0,self.LEAD+s["end_time"]/1000.0,
                            self.normalize(s["text"])])
        raw=[r for r in raw if r[2].strip()]; raw.sort()
        # 规范化与整理交替两轮：合并产生的新文本也能吃到 corrections，合并造成的断尾也能再搬
        for _ in range(2):
            raw=[list(x) for x in self._tidy(raw)]
            for r in raw: r[2]=self.normalize(r[2])
            raw=[r for r in raw if r[2].strip()]
        for idx,r in enumerate(raw):
            r[1]=min(r[1],seg)
            nxt=raw[idx+1][0] if idx+1<len(raw) else seg
            if r[1]-r[0]<self.MINDUR: r[1]=min(r[0]+self.MINDUR,nxt-0.02,seg)
            if r[1]<=r[0]: r[1]=min(r[0]+0.2,seg)
        for idx in range(len(raw)-1):                  # 真实停顿 <HOLDGAP 保持上一条，避免闪空
            if 0 < raw[idx+1][0]-raw[idx][1] < self.HOLDGAP:
                raw[idx][1]=raw[idx+1][0]
        segs=[]; cur=0.0
        for a,b,txt in raw:
            a=max(a,cur)
            if b<=a: continue
            if a>cur+0.05: segs.append((cur,a,None))
            segs.append((a,b,txt)); cur=b
        if cur<seg-0.02: segs.append((cur,seg,None))
        return segs

    # ---------- per-page encode ----------
    def build_page(self,i):
        seg=dur(f"{self.audio}/p{i:02d}.mp3")+0.8
        segs=self.intervals(i,seg)
        lst=[]; k=0
        for (a,b,txt) in segs:
            img=self.base_canvas(i) if txt is None else self.sub_image(i,k,txt)
            if txt is not None: k+=1
            lst.append((os.path.abspath(img),b-a))
        tf=tempfile.NamedTemporaryFile("w",suffix=".txt",delete=False)
        for img,d in lst: tf.write(f"file '{img}'\nduration {d:.3f}\n")
        tf.write(f"file '{lst[-1][0]}'\n"); tf.close()
        out=f"{self.imgdir}/seg_{i:02d}.mp4"
        vf=f"fps=25,format=yuv420p,fade=t=in:st=0:d={self.FADE},fade=t=out:st={seg-self.FADE}:d={self.FADE}"
        cmd=["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",tf.name,
             "-i",f"{self.audio}/p{i:02d}.mp3","-vf",vf,
             "-af","adelay=400|400,apad=pad_dur=0.4",
             "-c:v","libx264","-r","25","-pix_fmt","yuv420p","-crf","18","-preset","medium",
             "-c:a","aac","-b:a","192k","-t",f"{seg:.3f}","-shortest",out]
        r=subprocess.run(cmd,capture_output=True,text=True); os.unlink(tf.name)
        if r.returncode!=0: print("ERR page",i,r.stderr[-600:]); sys.exit(1)
        return out,seg

    def run(self):
        n=len(sorted(glob.glob(f"{self.audio}/p*.mp3")))
        only=os.environ.get("ONLY")
        pages=[int(only)] if only else list(range(1,n+1))
        outs=[]
        for i in pages:
            o,s=self.build_page(i); outs.append(o); print(f"page {i} seg={s:.1f}s -> {o}")
        if only: return
        os.makedirs(os.path.dirname(self.out) or ".",exist_ok=True)
        tf=tempfile.NamedTemporaryFile("w",suffix=".txt",delete=False)
        for s in outs: tf.write(f"file '{os.path.abspath(s)}'\n")
        tf.close()
        subprocess.run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",tf.name,
                        "-c","copy",self.out],check=True)
        os.unlink(tf.name); print("DONE",self.out)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--slides",default="slides")
    ap.add_argument("--audio",default="audio")
    ap.add_argument("--asr",default="asr_pages")
    ap.add_argument("--workdir",default="subs_img")
    ap.add_argument("--font",required=True,help="字幕字体 ttf 路径，如钉钉进步体")
    ap.add_argument("--config",default=None,help="文本清洗配置 JSON")
    ap.add_argument("--out",required=True)
    ap.add_argument("--fs",type=int,default=46)
    ap.add_argument("--lead",type=float,default=0.4,help="每页前置静音(秒)，与字幕时间轴偏移一致")
    ap.add_argument("--fade",type=float,default=0.5)
    ap.add_argument("--gap",type=float,default=0.28,help="断句停顿阈值(秒)")
    ap.add_argument("--minlen",type=int,default=6,help="满足停顿即断句的最小字数")
    ap.add_argument("--maxlen",type=int,default=15,help="强制断句的最大字数")
    ap.add_argument("--mindur",type=float,default=0.6,help="单条字幕最短停留(秒)")
    ap.add_argument("--minchars",type=int,default=4,help="单条字幕最少可见字数，低于则并入邻条(防单字字幕)")
    ap.add_argument("--holdgap",type=float,default=0.45,help="相邻字幕真实停顿小于此值时保持上一条，避免闪空")
    Composer(ap.parse_args()).run()

if __name__=="__main__":
    main()

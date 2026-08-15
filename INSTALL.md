# INSTALL — 安装指令

> 本文件既给人看，也可直接交给 AI Agent 执行：「解压/克隆这个技能包，按 INSTALL.md 安装」。每步都有验证命令，全部通过再报告结果。

## 你要做什么

把 8 个技能装进技能目录、初始化音色库、检查运行依赖，再由用户自备模板与品牌素材。安装完成后即可说"根据这篇文字稿做课程视频"触发整条流水线。

## Step 1 — 安装 8 个技能

`skills/` 下每个子目录是一个技能（根含 `SKILL.md`）。逐个拷进用户技能目录（QoderWork 为 `~/.qoderwork/skills/`；其他宿主端用其对应目录）：

```bash
SKILL_DIR=~/.qoderwork/skills
STAMP=$(date +%Y%m%d)
mkdir -p "$SKILL_DIR"
cd <本仓库根>/skills
for d in */; do
  name="${d%/}"
  if [ -d "$SKILL_DIR/$name" ]; then
    mv "$SKILL_DIR/$name" "$SKILL_DIR/$name.bak-$STAMP"   # 已存在则改名备份，绝不覆盖
  fi
  cp -R "$d" "$SKILL_DIR/$name"
done
```

**验证**：8 个目录各有 SKILL.md——

```bash
SKILL_DIR=~/.qoderwork/skills
for s in course-creation-workflow courseware-brand-styling course-outline-to-ppt \
         courseware-to-lecture-script subtitled-courseware-video courseware-to-video \
         bailian-gen bailian-protocol; do
  test -f "$SKILL_DIR/$s/SKILL.md" && echo "OK $s" || echo "MISSING $s"
done
```

## Step 2 — 初始化音色库

```bash
mkdir -p ~/.qoderwork/voice_library
cp -Rn <本仓库根>/resources/voice_library/ ~/.qoderwork/voice_library/
```

若 `voices.json` 已存在则**不要覆盖**，提示用户手动合并。

**验证**：`python3 -c "import json;d=json.load(open('$HOME/.qoderwork/voice_library/voices.json'));print(len(d['voices']),'voices')"` 有输出即可。

## Step 3 — 自备素材（需用户参与）

通用包不含品牌模板/logo/吉祥物/复刻音色，提醒用户放好：

1. **课程 PPT 模板** → `~/.qoderwork/skills/course-creation-workflow/assets/ppt-template/`（见该目录 README）。没有就走 `course-outline-to-ppt` 内置模板。
2. **品牌 logo / 吉祥物** → `~/.qoderwork/skills/courseware-brand-styling/assets/logo/` 与 `assets/mascot/`（见 `assets/README.md`），并在该技能 SKILL.md 的「样式」「Logo」「吉祥物」几节填自己的规则。
3. **音色** → 在 `~/.qoderwork/voice_library/voices.json` 登记（参考占位条 `C1`）；复刻音色见音色库 README。

## Step 4 — bl CLI 安装与鉴权（配音/ASR 用百炼时需要，需用户参与）

1. 检查：`which bl`。若无，按 `bailian-protocol` 技能说明安装（`npx skills add modelstudioai/cli`）。
2. 鉴权：**由用户本人** `bl auth login` 登录自己的阿里云百炼（DashScope）账号——你只能引导。提醒：TTS/ASR 消耗其本人额度。

> 只用 edge-tts（免费）时可跳过本步。

## Step 5 — 本机依赖检查

```bash
for c in python3 ffmpeg soffice; do which $c || echo "MISSING: $c"; done
python3 -c "import pptx, fitz, PIL, jieba" 2>&1
```

缺什么装什么：`brew install ffmpeg`、`brew install --cask libreoffice`、`pip install python-pptx pymupdf pillow jieba`。装系统软件前先征得用户同意。

## Step 6 — 完成报告

向用户报告：已装技能清单、音色库音色数、依赖检查结果、待用户完成事项（自备模板/logo/吉祥物/音色、bl auth login、缺失依赖）。最后告诉触发方式：

> 对我说"根据这篇文字稿做课程视频"并附上 .md 文字稿即可开始；开工前我会先问清受众、时长、自录还是 TTS、用哪套模板，流程中的 PPT 优化、讲稿过稿、音色试听等决策点我会停下来等你。

## 禁止事项

- 不要删除或覆盖用户已有的同名技能/音色库文件（冲突时备份改名）。
- 不要替用户执行 `bl auth login` 或索要账号凭据。
- 不要跳过验证步骤直接报告成功。

---
name: courseware-brand-styling
description: 把课件/PPT 品牌化并套上统一模板——产品名逐字替换、按用途替换 logo、把吉祥物换成你自己的 IP、按你的品牌口径核对内容、套统一 PPT 模板，输出可再编辑的 .pptx。当用户提到"给课件套模板""PPT 品牌迁移/品牌化""换 logo 换吉祥物""把旧课件改成新品牌""统一课件视觉"或上传旧课件要求品牌化时使用。
version: 2.0.0
---

# 课件品牌化 / 套模板

把一份课件迁移到**你自己的品牌**：**文字**产品名逐字替换、**logo**按用途替换、**吉祥物**换成你自己的 IP、**内容口径**按你的品牌手册/官网核对、**样式**套统一 PPT 模板。输出 .pptx 交给用户手动微调。

> **通用版技能**：不含任何品牌素材。首次使用前，先按「准备工作」把你自己的 logo、吉祥物、模板、品牌口径填进来。

## 触发条件

用户上传/指定一份旧课件（.pptx / .pdf），要求换品牌、换 logo、换吉祥物、按某个品牌口径更新，或套统一模板。

## 准备工作（首次，一次性）

1. **品牌素材**：把 logo 放进 `assets/logo/`、吉祥物放进 `assets/mascot/`（见 `assets/README.md`）。没有吉祥物就跳过吉祥物相关步骤。
2. **填品牌规则**：把下方模板占位（`{{OLD_BRAND}}`/`{{NEW_BRAND}}`/`{{主色}}` 等）替换成你自己的值，或另存一份填好的副本。
3. **课程模板**：把统一 PPT 模板放进 `course-creation-workflow` 技能的 `assets/ppt-template/`，并在下面「样式」一节记录该模板每类版式页的坐标与字号。
4. **品牌口径源**：把你的官网/品牌手册地址填进「内容口径核对」一节。

## 前置依赖

- `python-pptx`（读写 pptx）：`python3 -c "import pptx" || pip3 install python-pptx`
- `Pillow`（吉祥物抠图/贴回）：`python3 -c "import PIL" || pip3 install Pillow`
- 重绘吉祥物/信息图（可选）：任一图像生成/编辑能力（如 `bailian-gen` 的 `bl image edit`）；首次鉴权见 `bailian-protocol`。
- 核对品牌口径需能访问你的官网/品牌手册（用 WebFetch 或浏览器）。

约定工作目录：在工作目录建 `work/`，拆出的图片、抠图中间件、pptx 副本都放这里；**改前先备份原 pptx 到工作目录**（原文件不在 git 里时必须备份）。

## 四条迁移主线

### 1. 文字逐字替换

用 `pptx` skill 的读写能力遍历所有 slide 的 text frame（含表格、文本框、组合内文本），做字符串级替换：

- `{{OLD_BRAND}}` → `{{NEW_BRAND}}`（中英各一组，注意大小写与英文边界）。
- **保留需要保留的叙事**：与合作方/生态的关系表述、渠道场景等不要顺手删——在你的品牌规则里列一张「保留词清单」。
- 只替换品牌词，不顺手改写其他措辞（逐字保真，和讲稿替换同一原则）。

⚠️ 别只用 `python-pptx` 的 `run.text` 遍历就以为替换干净——多页共用的页脚/角标常在 **slide layout / master** 上，还有 SmartArt、组合形状、图片里的文字。见"验收"一节的全量核对。

### 2. Logo 使用规范（`assets/logo/`）

按**用途**选 logo，不要一张打天下。建议在你的 `assets/logo/` 里备齐几种，并照下表登记（示例，按你的素材改）：

| 场景 | 用哪张 | 说明 |
|------|--------|------|
| 封面主 logo | `你的_Logo_主版.png` | 完整版，封面/首页用 |
| 左上角小角标 | `你的_Logo_扁平.png` | 小尺寸、页眉用 |
| 页内较大装饰图标 | `你的_Logo_立体.png` | 页内大图标/配图 |
| 深色底场景 | `你的_Logo_反白.png` | 深色页面上用 |

**禁用**：把 App 图标当品牌 logo 放进课件页面。

多页共用的角标一般挂在 **slide layout** 上：用 `slide.slide_layout` 定位修改（`prs.slide_layouts` 只索引首个 master）；`SlideLayout` 不可 hash，去重用 `id()`。

### 3. 吉祥物 / IP 形象（`assets/mascot/`，可选）

**形象规范**：在你的品牌规则里写死吉祥物的硬特征（造型、主色、姿态），用户会逐一核对，**严禁**擅自改成其他形象。素材建议扁平 2D 与 3D 各一套、各带实底/透明底；**贴页优先用透明底版**免抠图；除非页面整体是 3D 风格，否则统一用扁平 2D 版以免风格不统一。

把页面里的旧吉祥物换成你的 IP，两种做法：

- **独立摆放的吉祥物**：直接用对应版本 PNG（默认扁平主形象），需要透明底/纯白底时用下面的抠图法处理后贴入。
- **嵌在信息图里、周围有文字的角色**：不要整页直抠（悬浮元素会遮头破脸）。做法是"裁面板 → 重绘角色 → 贴回"：
  1. 从整页裁出含角色的面板，记录 box 坐标。
  2. 用图像编辑能力（传对应风格的吉祥物 PNG 作参考图）只替换角色，密集中文文字仍保真无乱码。
  3. PIL 按原 box 把重绘结果贴回整页，护住标题/底部文字。

**抠图技巧**（PIL）：
- 抠透明底：`ImageDraw.floodfill` 从 4 角 + 各边中点（thresh≈60）填哨兵色再置 alpha=0（保住内部白眼睛）；残留柔影用低饱和亮色仅在下半区键除。纯色底素材键除更干净。
- 换纯白底/去投影：用 numpy 饱和度掩码——`(max-min<55)&(min>150)→置白`，保留高饱和本体与深色五官。
- 不要从"含悬浮元素的成图"直抠；需要纯白底独立版时，用图像编辑能力以对应风格 PNG 为参考图重画一张纯白底版本。

满版吉祥物封面要缩小：整图 `resize`≈0.8 → 羽化贴到 clean 区 median 底色画布 → 用 python-pptx `swap_blip` 换掉封面图片的 blip。

### 4. 内容口径核对

口径核验源：① 你的官网/品牌手册（填地址：`{{品牌口径源}}`）；② 若有官方培训/产品介绍 deck，可逐页引用其口径。核对要点建议列成一张**避坑清单**（哪些是过时/错误 claim、哪些术语不能写错、哪些是必须保留的叙事），随品牌规则维护。原则：**逐条核官网再决定去留，别把旧内部叙事当对外能力写进课件**。

### 样式：套统一 PPT 模板

**模板文件**：放在 `course-creation-workflow` 技能的 `assets/ppt-template/`（见该目录 README）。凡遇旧的、与新模板不一致的版式，**不要只做品牌替换，要整页重排为模板规范**。

**在这里记录你自己模板的规范**（下面是需要写清的项，按你的模板填）：

- **画布**：10 × 5.625 in（16:9）。
- **配色（srgbClr）**：主色 `{{主色}}` / 标题色 `{{标题色}}` / 正文色 `{{正文色}}` / 卡片底 `{{卡片底}}` / …
- **字体**：`{{字体}}`。⚠️ CJK 必须同时设 `<a:ea>` typeface，只改 `<a:latin>`（python-pptx 的 `font.name`）会残留旧字形——务必手动写 rPr 的 `<a:ea>`（连带 `<a:latin>`/`<a:cs>`）。
- **每页 chrome**（逐页加：LayoutShapes 不支持 add_picture/add_shape）：白底矩形、品牌装饰条、右上 logo（坐标 `{{logo坐标}}`）、标题块（主标题坐标/字号、下划线、kicker）。
- **标题块坐标**：主标题 `{{主标题坐标}}` sz`{{主标题字号}}`；下划线 `{{下划线坐标}}`；kicker `{{kicker坐标}}` sz`{{kicker字号}}`。
- **目录页 / 章节页 / 结束页**的构图与坐标。
- **卡片/标签**：圆角还是直角、边框、重点卡与最强卡的配色。

> 建议把每类版式页的坐标与字号**写进模板 pptx 的页面备注**里，改字时照抄别重算——这是把「设计模板」变成「可复制占位版式」的关键。

**整页重排的构图纪律**：重排一页时**先复刻同一 deck 里同类页的骨架**（栏宽/卡片/竖条小节等），不要自创构图；但骨架若挤压主图篇幅，宁可裁掉摘要卡放大图——**内容展示尺寸优先于骨架完整**。把原文前缀（如"要点1:""风险N:"）提炼成小标题属于排版、可做；**新写句子不算排版、不可做**。

旧稿那种「引言横条」可改造成 kicker：留住形状与原文，只把 fill 去掉、字号/颜色改成 kicker 规格、挪到 kicker 位——文字零改动。

**信息图为主的页（一页一张密集大图）套模板时压缩标题块**，用紧凑标题块并尽量保留大图原始 left/top/width，只有明显越界才等比 fit 进内容区。**多图页**把多张图视为一个整体 bbox 等比缩放居中填满内容区，保住相对版式，别逐张乱挪；用 PIL 读原生宽高比算高度防拉伸。

### 含吉祥物的复杂信息图：重做流程（HTML→无头 Chrome 截图，勿用 AI 直接改整图）

**经验：图像编辑能力直接改整张密集中文信息图，往往把中文改乱、版面重排——不要这么干**。改用 HTML+CSS 设计 → 无头 Chrome 截图：
```
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
  --hide-scrollbars --force-device-scale-factor=2 --default-background-color=ffffffff \
  --window-size=<W>,<H> --screenshot=out.png "file://<abs>.html"
```
- `window-size` 按 PPT 目标图片框**宽高比**设（如 1600×H），`--force-device-scale-factor=2` 出 2x 高清；截好用 zipfile 替换 `ppt/media/imageNN.png` 字节即可（图框尺寸不变故不失真）。
- 吉祥物用 `assets/mascot/`：3D 光泽版配深色场景；浅色模板用透明底版并去底部白色地影（numpy：下 26% 区域且 `sat<45 & min>110` → alpha=0）。
- 中文 100% 保真。这套 HTML 模板可复用改文案与配色。

## python-pptx 注意事项（血泪坑）

- 脚本**切勿命名 `inspect.py`**（会遮蔽 stdlib 触发循环导入，换名如 `probe_pptx.py`）；本机无 `python` 命令，一律用 `python3`。
- **改形状文字前先 dump 全部 shape**（id/name/geometry/文本），别猜 shape_id 直接 set_text——实测连猜三次都错，dump 一次就准。
- **新增/重排页**：走 `prs.slides._sldIdLst` 直接挪 `<p:sldId>` 元素顺序。
- **两行大标题别加 line_spacing**：过大行距会把标题压到下划线上，多行标题保持默认行距、调 top 就好。
- **迭代重排时永远从最初备份读**：在 v2 产物上做 v3 会留下上一版新增形状难删干净；每版都从原始备份重放全部改动。
- 多页共用 logo/角标常在 **slide layout** 上，经 `slide.slide_layout` 改（`prs.slide_layouts` 仅索引首 master）；`SlideLayout` 不可 hash，用 `id()` 去重。
- **批量改配色**：逐形状 recolor 会漏组合/自由形/SmartArt；save 时需兜底替换 `ppt/slides/*.xml` 里的 `srgbClr`。
- **SmartArt 配色**：只能替换 `ppt/diagrams/*.xml` 里的 `srgbClr`；改 `schemeClr` 会致整图消失。深蓝这类往往分两处——节点填充在 `drawing1.xml` + `data1.xml`（两个文件都要改，否则 PowerPoint 重排版会回原色），环形/箭头装饰走 `schemeClr`，改**该 master 对应 theme 的 scheme 色**更安全。
- 嵌入位图信息图**不可改色**（只能重绘或换图）。
- `LayoutShapes` 无 `add_shape`/`add_picture`，chrome（页眉角标等）须逐页添加。
- **别动 theme 的 `<a:ea>` 字体**：整体改 theme 的 CJK 字体后，soffice 预览会把正文 CJK 回退成别的字体（PowerPoint 正常，但预览没法验收）。字体只在 run 级设 latin/ea/cs。
- **panose 别删，要改写**：删掉 `panose`/`pitchFamily`/`charset` 会让 soffice 把中文回退成宋/楷。正确做法是把 panose 改写为目标字族的 panose 值（如黑体族 `020B0400000000000000`）；若预览机未装目标字体，可临时装克隆字体再验收。
- **soffice 预览对 SmartArt 位置不准**：graphicFrame 的 off/ext 会被忽略，图被顶到左上角。别据此反复调，PowerPoint 里是对的；SmartArt 保持原始几何，缩放交给用户手动拖。

## Verification（验收，逐条自查）

1. **全量核对无残留**：把成品 pptx 的所有图片抽出（解压 `ppt/media/`）逐一 Read 核对，确认无旧品牌字样与旧吉祥物形象；文本层用脚本 grep `ppt/slides/*.xml` + `ppt/slideLayouts/*.xml` + `ppt/diagrams/*.xml` 确认无残留品牌词。
2. **Logo 用途正确**：封面主 logo、角标小 logo、页内装饰图标各就各位；无 App 图标误用。
3. **吉祥物形象合规**：符合你写死的硬特征，五官/文字无破损、无乱码。
4. **口径核对**：随机抽查文案与你的官网/品牌手册一致；无错误 claim；需保留的叙事已保留。
5. 文件可正常打开、可再编辑；备份原 pptx 已保存在工作目录。
6. 交付 .pptx 到用户工作目录并给 file:// 链接，**明确提示这是待用户手动优化细节的中间产物**。

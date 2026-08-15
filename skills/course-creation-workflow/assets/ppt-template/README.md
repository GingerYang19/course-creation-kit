# 课程 PPT 模板（放你自己的模板）

> **这个目录默认是空的。** 通用版技能包不含任何品牌模板——请把你自己的课程 PPT 模板放进来。

## 怎么用

1. 做一套（或两套）**占位版式 PPT 模板**：画布 10 × 5.625 in（16:9），每页放好标题块、内容区、卡片等版式骨架，占位文字写上「≤N 字」上限提示，页面备注里写死该页坐标与字号。
2. 把模板 `.pptx` 放进本目录，并在 `course-creation-workflow` 技能的 Stage 1 里把「模板选用表」改成你自己的模板文件名。
3. 制课时的主路径是**复制占位版式页 → 就地改字**，不动坐标/字号/配色；每页占位文字标了上限，超了就换版式或删句，别缩字号。

## 建议

- 一套模板覆盖一种场景（如「认证课程系列」「对外分享/发布」各一套）。
- 品牌 logo、吉祥物等素材放进 `courseware-brand-styling` 技能的 `assets/` 目录，见那里的 `assets/README.md`。
- 想让脚本批量生成占位模板，可参考 `python-pptx` 写一个构建脚本，素材路径按脚本所在目录解析、输出走 `argv[1]`。

---

# Course PPT Templates (drop your own here)

> **This folder is intentionally empty.** The generic kit ships no branded template — put your own course PPT template here.

## How to use

1. Build a placeholder-layout template: canvas 10 × 5.625 in (16:9), with title block / content area / card skeletons on each page, placeholder text carrying a "≤N chars" cap, and per-slide notes fixing that page's coordinates and font sizes.
2. Drop the `.pptx` here and update the template-selection table in the `course-creation-workflow` skill's Stage 1 to point at your filename.
3. The main authoring path is: copy a placeholder layout page → edit text in place, without touching coordinates / font size / colors.

## Tips

- One template per scenario (e.g. one for a "certification series", one for "external sharing").
- Put brand logos and mascots under the `courseware-brand-styling` skill's `assets/` directory (see its `assets/README.md`).

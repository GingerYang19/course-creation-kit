# 品牌素材（放你自己的 logo 与吉祥物）

> **这个目录默认是空的。** 通用版技能包不含任何品牌素材——请把你自己的品牌资产放进来，再让 `courseware-brand-styling` 技能引用。

建议子目录：

```
assets/
├── logo/        你的课程/产品 logo（建议备齐横版、竖版、深色底、浅色底几种）
└── mascot/      吉祥物/IP 形象（建议扁平 2D 与 3D 各一套，实底 + 透明底）
```

## 用法

1. 把 logo 放进 `logo/`，吉祥物放进 `mascot/`。
2. 在 `SKILL.md` 里把「Logo 使用规范」「吉祥物」两节改成**你自己的**素材文件名与使用规则（尺寸、位置、深浅底选用）。
3. 品牌口径核验源改成你自己的官网/品牌手册地址。

没有吉祥物的品牌，把 `mascot/` 相关步骤跳过即可——它不是必需项。

---

# Brand assets (drop your own logo & mascot here)

> **This folder is intentionally empty.** The generic kit ships no brand assets — add your own and reference them from the `courseware-brand-styling` skill.

Suggested layout:

```
assets/
├── logo/        your course/product logo (landscape, portrait, on-dark, on-light)
└── mascot/      mascot / IP character (flat 2D + 3D, solid + transparent background)
```

Update the "Logo usage" and "Mascot" sections in `SKILL.md` to your own filenames and rules, and point the brand-voice source at your own website / brand book. If you have no mascot, just skip the mascot steps — it is optional.

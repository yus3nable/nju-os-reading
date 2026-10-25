# 南京大学操作系统原理 · 2026

蒋炎岩课程的图文阅读网站，包含全部 30 课。支持手机、平板与桌面浏览、中文全文搜索、连续翻页、课件图片放大、字号调整与本机阅读位置记录。

- 网站：https://yus3nable.github.io/nju-os-reading/
- 原课：https://space.bilibili.com/202224425/lists/7587348?type=season
- 课程主页：https://jyywiki.cn/OS/2026/

## 内容与目录

`chapters/01/001.md` 等文件是可编辑书稿。每篇顶部的 JSON front matter 记录标题、原片时间及来源 PDF 页码，正文保留课堂讲述、代码与图注。标题与时间的修改从 Markdown 进入网站，不需要修改页面模板。

`assets/images/` 保存正文所需的独立课件图片。`maintenance/lesson-*.json` 记录来源文件和课程顺序，`maintenance/reading-pages.json` 是唯一连续阅读顺序。源 PDF 保留在本地原目录，不随网站发布。

首页与侧栏的课名直接进入本课第一篇正文；旁边的箭头独立控制小节展开。底部翻页跨课连续。搜索只索引规范正文，没有聚合页副本。阅读位置只保存在当前浏览器，跨设备不自动同步。

## 本地构建与预览

在仓库根目录运行，使用 Python 3.11：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/build.py --base-path /nju-os-reading/
.venv/bin/python scripts/check_reader.py build --reading-order maintenance/reading-pages.json --base-path /nju-os-reading/ --report maintenance/site-check.json
mkdir -p .preview
ln -s ../build .preview/nju-os-reading
.venv/bin/python -m http.server 8765 --bind 127.0.0.1 --directory .preview
```

打开 http://127.0.0.1:8765/nju-os-reading/ 。`.preview/nju-os-reading` 已存在时跳过 `ln -s`。构建结果在 `build/`，不进入 `main` 分支。

## 转换与校验

`convert.py` 用 PyMuPDF 提取现有 PDF 的文字和独立图片，依据源目录生成小节；Menlo 字体的代码保留缩进，图注与正文分别处理。图片以原始像素尺寸输出 WebP，质量 92，不把整页 PDF 扫描图当正文。

```sh
.venv/bin/python scripts/convert.py /绝对路径/课程.pdf
.venv/bin/python scripts/audit.py /绝对路径/图文PDF
```

默认拒绝覆盖已有书稿。`--replace` 会重新生成对应课程的 Markdown 与图片，仅在明确需要放弃该课手工编辑时使用。

`audit.py` 对全部生成正文与 PDF 文字层逐字符比对，忽略版面空白与时间标签前缀；另外核对图片数量、代码行与缩进。它验证转换是否漏字或改字，无法证明原始转写准确。源 PDF 中已有的听辨缺口、课堂口误和后续更正按原稿保留，未重新识别音频。

`maintenance/content-audit.json`、`maintenance/site-check.json` 和 `maintenance/QA.md` 记录内容、静态链接与浏览器抽查的实际范围。

## 发布

`main` 保存书稿、图片与生成器；`gh-pages` 只保存 `build/` 生成的静态网站。GitHub Pages 从 `gh-pages` 的根目录发布，`.nojekyll` 关闭 Jekyll 处理。部署路径为 `/nju-os-reading/`。更新时先构建并完成检查，再提交书稿、发布构建结果并核对线上页面。

页面不依赖外部字体、CDN JavaScript 或数据库。首次打开搜索会加载本站搜索索引，图片按需加载。桌面和移动版使用同一套内容和规范地址。

转换脚本的 `--text-only` 可在已有图片完整保留时仅重新提取书稿，缺图会明确报错；该选项仍须遵守 `--replace` 的覆盖约束。来源身份、逐单元页码映射及图片位置分别保存在 `maintenance/source-map.json` 和 `maintenance/asset-map.json`。

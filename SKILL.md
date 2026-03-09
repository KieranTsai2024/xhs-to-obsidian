---
name: xhs-to-obsidian
description: "小红书收藏到 Obsidian 技能。支持图文和视频笔记。图文：下载图片+OCR；视频：自动转录文字稿。"
---

# 小红书收藏到 Obsidian

## 📦 安装方式

### 方式 1：从 GitHub 安装（推荐）

```bash
# 克隆仓库
git clone https://github.com/KieranTsai2024/xhs-to-obsidian.git
cp -r xhs-to-obsidian ~/.openclaw/workspace/skills/
```

### 方式 2：直接复制

```bash
# 打包
tar -czf xhs-to-obsidian.tar.gz ~/.openclaw/workspace/skills/xhs-to-obsidian

# 对方解压
tar -xzf xhs-to-obsidian.tar.gz -C ~/.openclaw/workspace/skills/
```

**对方需要额外安装：**
1. Python 依赖：`pip install aiohttp loguru getuseragent pycryptodome`
2. 视频功能（可选）：参考 `INSTALL.md`
3. 配置登录态：复制 `config.json.example` → `config.json` 并填入 cookie

⚠️ **注意**：不要分享 `config.json`（包含个人登录态），使用 `config.json.example` 模板。

---

将小红书笔记一键收藏到 Obsidian 笔记库。**自动识别图文/视频类型**：

- **图文笔记**：内容解析 + 图片下载 + OCR 识别
- **视频笔记**：调用 video-whisper 转录 + 生成带时间轴的文字稿

## Quick Start

### 基本用法

直接给 KK 发送小红书分享链接即可：

```
请帮我收藏这个小红书笔记：https://xhslink.com/xxx
```

或

```
收藏：https://www.xiaohongshu.com/explore/xxx?xsec_token=xxx
```

### 手动运行脚本

**方式 1：完整流程（推荐）**
```bash
cd ~/.openclaw/workspace/skills/xhs-to-obsidian
python scripts/kk_collect.py <小红书链接> [输出目录]
```
自动完成：转录/下载 → 生成总结 → 更新文件

**方式 2：仅转录/下载**
```bash
python scripts/collect.py <小红书链接> [输出目录]
```

## 功能特性

1. **自动类型识别** - 智能判断图文/视频笔记
2. **自动解析** - 支持标准链接和 xhslink.com 短链
3. **内容提取** - 获取标题、作者、正文、发布时间
4. **图片下载** - 下载笔记中的所有图片（**默认最多 25 张**，可配置）
5. **OCR 识别** - 对图片进行文字识别（可选）
6. **视频转录** - 调用 video-whisper 本地转录（Apple Silicon）
7. **时间轴聚合** - 自动将逐句时间轴合并为分段式（~20 段）
8. **结构化总结** - KK 自动生成（核心主题 + 分级内容 + 金句 + 表格）
9. **格式化存储** - 按模板生成 Markdown 存入 Obsidian

## 输出模板

### 图文笔记

```markdown
---
tags: [小红书，收藏]
source: [分享链接]
author: [博主昵称]
publish_date: [发布日期]
collected_date: [收藏日期]
---

# [笔记标题]

## 正文内容
[解析出的正文]

## 图片
![[文件名 1.jpg]]
![[文件名 2.jpg]]
```

### 视频笔记

```markdown
---
tags: [小红书，视频转录，收藏]
source: [分享链接]
author: [博主昵称]
type: video
duration: [视频时长]
transcription_model: mlx-community/whisper-medium-mlx
---

# [笔记标题]

## 📋 结构化总结
[KK 自动生成的总结：核心主题 + 分级内容 + 金句 + 表格]

---

## 📝 完整文字稿
[转录的完整文字稿]

---

## 📍 分段式时间轴
- **[0:00-0:44]** 第一段内容...
- **[0:44-1:16]** 第二段内容...
```

## 默认存储位置

- **笔记文件**: `/Users/kierantsai/Desktop/PARA_系统仓库/A.收集/`
- **图片附件**: `/Users/kierantsai/Desktop/PARA_系统仓库/A.收集/attachments/`
- **文件命名**: 
  - 图文：`小红书 - 博主名 - 笔记标题.md`
  - 视频：`视频转录 - 博主名 - 笔记标题.md`

## 配置自定义

编辑 `config.json` 修改配置：

```json
{
  "image_max_count": 25,          // 图片最大下载数量
  "timeline_segment_enabled": true,  // 启用时间轴聚合
  "timeline_segment_max": 20,        // 时间轴目标分段数
  "auto_summary_enabled": true       // 启用 KK 自动总结
}
```

## 依赖

### 图文笔记
- Python 3.8+
- aiohttp, loguru, getuseragent, pycryptodome
- xiaohongshu 技能（已内置）
- OCR 功能（macOS）：pyobjc-framework-Vision, pyobjc-framework-Quartz

### 图文笔记（OCR 功能）
- macOS Vision Framework（自动调用，无需额外安装）
- 首次使用会安装：`pip install pyobjc-framework-Vision pyobjc-framework-Quartz`

### 视频笔记（额外需要）
- video-whisper 技能
- Homebrew: `yt-dlp`, `ffmpeg`
- Python venv: `mlx-whisper`

视频转录依赖安装：
```bash
brew install yt-dlp ffmpeg
python3 -m venv ~/.openclaw/venvs/whisper
~/.openclaw/venvs/whisper/bin/pip install mlx-whisper
```

## 注意事项

1. **短链处理** - xhslink.com 短链会自动展开
2. **登录态** - 部分笔记需要登录态才能访问，可提供 web_session cookie
3. **图片数量** - 默认最多下载 25 张图片（可在 config.json 调整）
4. **OCR 功能** - macOS 原生 Vision Framework 支持（自动识别图片文字，支持中文）
5. **视频转录** - 首次使用需下载 Whisper 模型（约 1.5GB），之后会缓存
6. **视频时长** - 长视频（>10 分钟）转录可能需要几分钟
7. **自动总结** - 视频笔记完成后 KK 会自动生成结构化总结（无需手动触发）

## 故障排除

### 无法获取笔记详情
- 检查链接是否有效
- 可能需要提供登录态（web_session cookie）
- 短链可能需要先展开为完整链接

### 图片下载失败
- 检查网络连接
- 小红书图片可能有防盗链，需要正确的 referer

### 视频转录失败
- 检查 video-whisper 技能是否安装
- 首次运行需下载模型，确保网络通畅
- 长视频可能需要更长时间，脚本超时设为 10 分钟

### OCR 无结果
- 检查是否安装了 pyobjc 依赖：`pip install pyobjc-framework-Vision pyobjc-framework-Quartz`
- 确认图片清晰可读（模糊图片可能无法识别）
- macOS Vision Framework 仅支持 macOS 10.15+

### 自动总结未触发
- 检查 `config.json` 中 `auto_summary_enabled` 是否为 `true`
- 检查 `pending/` 目录是否有通知文件
- KK 会定期检查 pending 目录并处理

## 相关文件

- `scripts/collect.py` - 主脚本（转录/下载）
- `scripts/kk_collect.py` - 完整流程脚本（推荐）
- `scripts/auto_summary.py` - 自动总结触发脚本
- `scripts/kk_summary.py` - KK 总结处理脚本
- `scripts/kk_process_pending.py` - KK pending 处理脚本
- `pending/` - KK 待处理通知目录
- `config.json` - 配置文件

## 自动化流程

```
用户发送链接
    ↓
collect.py 解析并转录
    ↓
保存临时文件 + 写入 pending 通知
    ↓
auto_summary.py 触发通知
    ↓
KK 读取 pending 目录
    ↓
KK 生成结构化总结并更新 MD 文件
    ↓
✅ 完成（无需手动干预）
```

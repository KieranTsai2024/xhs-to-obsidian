# xhs-to-obsidian 🦊

将小红书笔记一键收藏到 Obsidian，支持**图文笔记**和**视频笔记**自动处理。

- 📸 **图文笔记**：自动下载图片 + OCR 识别
- 🎥 **视频笔记**：调用 video-whisper 本地转录（Apple Silicon）
- 🤖 **自动识别**：智能判断笔记类型
- 📝 **格式化输出**：生成 Markdown 存入 Obsidian

---

## 🚀 快速开始

### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/KieranTsai2024/xhs-to-obsidian.git
cp -r xhs-to-obsidian ~/.openclaw/workspace/skills/

# 2. 安装 Python 依赖
pip3 install --user aiohttp loguru getuseragent pycryptodome

# 3. 配置登录态
cp ~/.openclaw/workspace/skills/xhs-to-obsidian/config.json.example \
   ~/.openclaw/workspace/skills/xhs-to-obsidian/config.json
# 编辑 config.json，填入你的 web_session cookie
```

### 使用

直接给 AI 助手发小红书链接即可：

```
收藏：https://xhslink.com/o/xxx
```

或手动运行：

```bash
# 图文笔记
python3 ~/.openclaw/workspace/skills/xhs-to-obsidian/scripts/collect.py "https://xhslink.com/o/xxx"

# 视频笔记（需要安装 video-whisper）
# 会自动调用 video-whisper 转录
```

---

## 📦 功能特性

| 功能 | 图文笔记 | 视频笔记 |
|------|----------|----------|
| 内容提取 | ✅ | ✅ |
| 图片下载 | ✅ (最多 10 张) | ❌ |
| OCR 识别 | ✅ (可选) | ❌ |
| 语音转录 | ❌ | ✅ (mlx-whisper) |
| 时间轴 | ❌ | ✅ |
| 输出文件 | `小红书 - 作者 - 标题.md` | `视频转录 - 作者 - 标题.md` |

---

## 📋 依赖

### 基础依赖（必需）

- Python 3.8+
- aiohttp, loguru, getuseragent, pycryptodome
- xiaohongshu 技能（OpenClaw 内置）

### 视频依赖（可选）

仅需要视频转录功能时安装：

- Apple Silicon Mac (M1/M2/M3/M4)
- `brew install yt-dlp ffmpeg`
- `pip install mlx-whisper`
- [video-whisper](https://github.com/openclaw/skills/tree/main/video-whisper) 技能

---

## 🙏 致谢

- **video-whisper** — 视频转录功能基于 [video-whisper](https://github.com/openclaw/skills/tree/main/video-whisper) 技能（MLX Whisper）
- **xiaohongshu** — 小红书 API 封装来自 OpenClaw xiaohongshu 技能

---

## 📁 项目结构

```
xhs-to-obsidian/
├── README.md              # 本文件
├── SKILL.md               # 技能文档
├── INSTALL.md             # 详细安装指南
├── config.json.example    # 配置模板
├── .gitignore
├── references/            # 参考模板
│   └── template.md
└── scripts/
    └── collect.py         # 主脚本
```

---

## 🔒 安全提示

- ⚠️ **不要分享 `config.json`** — 包含你的小红书登录态（cookie）
- ✅ 分享配置时用 `config.json.example` 模板
- 🔐 web_session cookie 可能过期，定期更新

---

## 📖 文档

- [SKILL.md](SKILL.md) — 技能详细说明
- [INSTALL.md](INSTALL.md) — 完整安装指南

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT

---

**Made with ❤️ for OpenClaw**

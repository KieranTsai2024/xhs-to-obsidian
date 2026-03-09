# xhs-to-obsidian 安装指南

将小红书笔记一键收藏到 Obsidian，支持图文和视频笔记自动处理。

---

## 🚀 快速安装

### 步骤 1：复制技能到 workspace

```bash
# 复制主技能
cp -r /path/to/xhs-to-obsidian ~/.openclaw/workspace/skills/

# 复制视频转录技能（可选，需要视频功能）
cp -r /path/to/video-whisper ~/.openclaw/workspace/skills/
```

### 步骤 2：安装 Python 依赖

```bash
# 基础依赖（图文笔记必需）
pip3 install --break-system-packages aiohttp loguru getuseragent pycryptodome

# 或使用 --user 标志（推荐）
pip3 install --user aiohttp loguru getuseragent pycryptodome
```

### 步骤 3：安装视频转录依赖（可选）

如果只需要图文笔记功能，**跳过此步骤**。

需要视频转录功能时安装：

```bash
# 1. 安装 Homebrew 工具
brew install yt-dlp ffmpeg

# 2. 创建 Python 虚拟环境
python3 -m venv ~/.openclaw/venvs/whisper

# 3. 安装 mlx-whisper（Apple Silicon 专用）
~/.openclaw/venvs/whisper/bin/pip install mlx-whisper
```

> ⚠️ **注意**：`mlx-whisper` 仅支持 Apple Silicon Mac（M1/M2/M3/M4 芯片）

### 步骤 4：配置登录态

```bash
# 复制配置模板
cp ~/.openclaw/workspace/skills/xhs-to-obsidian/config.json.example \
   ~/.openclaw/workspace/skills/xhs-to-obsidian/config.json

# 编辑配置文件
nano ~/.openclaw/workspace/skills/xhs-to-obsidian/config.json
```

**获取 web_session cookie：**

1. 打开小红书官网 (xiaohongshu.com)
2. 登录你的账号
3. 打开浏览器开发者工具（F12）
4. 进入 Application → Cookies → https://www.xiaohongshu.com
5. 找到 `web_session` 字段，复制其值
6. 粘贴到 `config.json` 的 `web_session` 字段

**修改输出路径（可选）：**

```json
{
  "web_session": "你的 web_session_cookie",
  "proxy": null,
  "output_dir": "/你的/笔记/存储/路径",
  "image_dir": "/你的/图片/存储/路径"
}
```

---

## ✅ 验证安装

### 测试图文笔记

```bash
python3 ~/.openclaw/workspace/skills/xhs-to-obsidian/scripts/collect.py \
  "https://www.xiaohongshu.com/explore/xxx"
```

### 测试视频笔记（如果安装了 video-whisper）

```bash
bash ~/.openclaw/workspace/skills/video-whisper/scripts/transcribe.sh \
  "https://www.xiaohongshu.com/discovery/item/xxx"
```

---

## 📋 依赖清单

### 基础依赖（必需）

| 依赖 | 用途 | 安装命令 |
|------|------|----------|
| Python 3.8+ | 运行环境 | 系统自带或 `brew install python@3.13` |
| aiohttp | HTTP 请求 | `pip install aiohttp` |
| loguru | 日志库 | `pip install loguru` |
| getuseragent | User-Agent 生成 | `pip install getuseragent` |
| pycryptodome | 加密库 | `pip install pycryptodome` |
| xiaohongshu 技能 | 小红书 API | 已内置在 `skills/xiaohongshutools` |

### 视频依赖（可选）

| 依赖 | 用途 | 安装命令 |
|------|------|----------|
| yt-dlp | 视频下载 | `brew install yt-dlp` |
| ffmpeg | 音频提取 | `brew install ffmpeg` |
| mlx-whisper | 语音转录 | `pip install mlx-whisper` |
| video-whisper 技能 | 转录脚本 | 已内置在 `skills/video-whisper` |

---

## 🛠️ 故障排除

### 问题 1：无法获取笔记详情

**可能原因：**
- web_session cookie 过期或无效
- 笔记需要登录才能访问

**解决方案：**
1. 重新获取 web_session cookie
2. 确保笔记是公开的

### 问题 2：图片下载失败

**可能原因：**
- 网络连接问题
- 图片防盗链

**解决方案：**
- 检查网络连接
- 尝试使用代理（在 config.json 中配置）

### 问题 3：视频转录失败

**可能原因：**
- 未安装 video-whisper 技能
- 未安装 mlx-whisper
- 首次运行需下载模型（约 1.5GB）

**解决方案：**
```bash
# 检查视频技能是否存在
ls ~/.openclaw/workspace/skills/video-whisper/scripts/transcribe.sh

# 检查 mlx-whisper 是否安装
~/.openclaw/venvs/whisper/bin/pip list | grep mlx

# 手动下载模型（首次运行）
~/.openclaw/venvs/whisper/bin/python3 -c "import mlx_whisper; mlx_whisper.transcribe('/dev/null', path_or_hf_repo='mlx-community/whisper-small-mlx')"
```

### 问题 4：权限错误

**可能原因：**
- 输出目录不存在或无写入权限

**解决方案：**
```bash
# 创建输出目录
mkdir -p /你的/笔记/存储/路径

# 或使用默认路径
mkdir -p ~/Desktop/PARA_系统仓库/A.收集
```

---

## 📚 使用说明

### 基本用法

```bash
# 使用默认输出路径
python3 scripts/collect.py "https://xhslink.com/xxx"

# 指定输出路径
python3 scripts/collect.py "https://xhslink.com/xxx" "/你的/输出/路径"
```

### 支持的链接格式

- ✅ 短链接：`https://xhslink.com/o/xxx`
- ✅ 标准链接：`https://www.xiaohongshu.com/explore/xxx`
- ✅ 发现页链接：`https://www.xiaohongshu.com/discovery/item/xxx`

### 自动类型识别

脚本会自动识别笔记类型：

- **图文笔记** → 下载图片 + OCR → `小红书 - 作者 - 标题.md`
- **视频笔记** → 转录文字稿 → `视频转录 - 作者 - 标题.md`

---

## 🔒 安全提示

1. **不要分享 `config.json`** — 包含个人登录态
2. **使用 `config.json.example` 模板** — 分享给别人时用这个
3. **定期更新 cookie** — web_session 可能过期

---

## 📞 获取帮助

- 查看 `SKILL.md` 了解更多功能
- 检查 `scripts/collect.py` 了解脚本细节
- 遇到问题查看本文件的「故障排除」部分

---

**安装完成后，直接给 AI 助手发小红书链接即可自动收藏！** 🦊

#!/usr/bin/env python3
"""
小红书收藏到 Obsidian - 主脚本
用法：python collect.py <小红书分享链接> [输出目录]

支持图文笔记和视频笔记：
- 图文：下载图片 + OCR，生成 Markdown
- 视频：调用 video-whisper 转录，生成带文字稿的 Markdown
"""

import asyncio
import sys
import os
import re
import json
import aiohttp
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

# 添加 xiaohongshu 技能路径
XHS_SKILL_PATH = Path.home() / ".openclaw" / "workspace" / "skills" / "xiaohongshutools" / "scripts"
sys.path.insert(0, str(XHS_SKILL_PATH))

from request.web.xhs_session import create_xhs_session

# video-whisper 脚本路径
WHISPER_SCRIPT = Path.home() / ".openclaw" / "workspace" / "skills" / "video-whisper" / "scripts" / "transcribe.sh"
WHISPER_PYTHON = Path.home() / ".openclaw" / "venvs" / "whisper" / "bin" / "python3"

# 加载配置文件
CONFIG_PATH = Path(__file__).parent.parent / "config.json"
DEFAULT_CONFIG = {
    "web_session": None,
    "proxy": None,
    "output_dir": "/Users/kierantsai/Desktop/PARA_系统仓库/A.收集",
    "image_dir": "/Users/kierantsai/Desktop/PARA_系统仓库/A.收集/attachments",
    "image_max_count": 25,
    "timeline_segment_enabled": True,
    "timeline_segment_max": 20,
    "auto_summary_enabled": True
}

def load_config() -> dict:
    """加载配置文件"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return {**DEFAULT_CONFIG, **config}
    return DEFAULT_CONFIG

CONFIG = load_config()
DEFAULT_OUTPUT_DIR = CONFIG["output_dir"]
DEFAULT_IMAGE_DIR = CONFIG["image_dir"]


def parse_xhs_url(url: str) -> Tuple[str, Optional[str]]:
    """
    解析小红书链接，提取 note_id 和 xsec_token
    支持格式:
    - https://www.xiaohongshu.com/explore/<note_id>?xsec_token=xxx
    - https://xhslink.com/<short_code>
    """
    # 标准链接（支持 /explore/ 和 /discovery/item/ 两种格式）
    if "xiaohongshu.com" in url:
        match = re.search(r'/(?:explore|discovery/item)/([a-zA-Z0-9]+)', url)
        token_match = re.search(r'xsec_token=([a-zA-Z0-9_-]+)', url)
        if match:
            note_id = match.group(1)
            xsec_token = token_match.group(1) if token_match else None
            return note_id, xsec_token
    
    raise ValueError(f"无法解析的小红书链接：{url}")


async def download_image(session: aiohttp.ClientSession, url: str, save_path: str) -> bool:
    """下载图片到本地"""
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                with open(save_path, 'wb') as f:
                    f.write(await resp.read())
                return True
    except Exception as e:
        print(f"下载图片失败 {url}: {e}")
    return False


async def ocr_image(image_path: str) -> str:
    """
    对图片进行 OCR 识别
    使用 macOS 自带的 Vision Framework（通过 Python + pyobjc）
    """
    try:
        # 使用 macOS Vision Framework 进行 OCR
        import subprocess
        
        # 创建一个临时 Python 脚本来调用 Vision
        vision_script = Path(__file__).parent / "macos_vision_ocr.py"
        
        if vision_script.exists():
            result = subprocess.run(
                [sys.executable, str(vision_script), image_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        
        # Fallback: 尝试使用 tesseract（如果已安装）
        try:
            result = subprocess.run(
                ['tesseract', image_path, 'stdout', '-l', 'chi_sim+eng'],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except FileNotFoundError:
            pass  # tesseract 未安装
        
        return ""
    except subprocess.TimeoutExpired:
        print(f"OCR 超时：{image_path}")
        return ""
    except Exception as e:
        print(f"OCR 失败：{e}")
        return ""


def generate_markdown(note_data: dict, image_paths: list[str], ocr_results: list[str]) -> str:
    """生成 Markdown 内容（图文笔记）"""
    collected_date = datetime.now().strftime("%Y-%m-%d")
    
    # 构建内容
    md = f"""---
tags: [小红书，收藏]
source: {note_data.get('url', '')}
author: {note_data.get('author', '未知')}
publish_date: {note_data.get('publish_date', '')}
collected_date: {collected_date}
---

# {note_data.get('title', '无标题')}

## 正文内容
{note_data.get('content', '')}

## 图片 OCR 内容
"""
    
    # 添加 OCR 结果
    for i, (img_path, ocr_text) in enumerate(zip(image_paths, ocr_results), 1):
        if ocr_text:
            md += f"\n### 图片 {i}\n{ocr_text}\n"
        else:
            md += f"\n### 图片 {i}\n无文字内容\n"
    
    md += "\n## 图片\n"
    for img_path in image_paths:
        filename = Path(img_path).name
        md += f"![[{filename}]]\n"
    
    return md


def generate_structured_summary_simple(transcript_text: str, title: str) -> str:
    """
    生成简单的结构化整理稿（基于规则的摘要）
    这是一个简化版本，提取关键段落和金句
    """
    print("[整理稿] 正在生成简化版整理稿...")
    
    # 分割成段落
    paragraphs = [p.strip() for p in transcript_text.split('\n\n') if p.strip()]
    
    # 提取可能的标题/分段（包含冒号或数字的行）
    sections = []
    current_section = None
    current_content = []
    
    for para in paragraphs[:50]:  # 限制处理前 50 段
        # 检测是否是新段落标题
        if any(pattern in para for pattern in ['第一', '第二', '第三', '首先', '其次', '最后', '注意', '提醒', '总结']):
            if current_section and current_content:
                sections.append((current_section, current_content))
            current_section = para[:100]
            current_content = []
        else:
            current_content.append(para)
    
    if current_section and current_content:
        sections.append((current_section, current_content))
    
    # 构建简化整理稿
    summary = f"""## 🎯 核心主题

{title}

---

## 📌 主要内容

"""
    
    for i, (section, content) in enumerate(sections[:8], 1):  # 最多 8 个部分
        summary += f"### {i}. {section}\n\n"
        for c in content[:3]:  # 每部分最多 3 段
            summary += f"- {c[:200]}...\n" if len(c) > 200 else f"- {c}\n"
        summary += "\n"
    
    # 提取可能的金句（带引号或感叹号的句子）
    quotes = []
    for para in paragraphs:
        if ('"' in para or '!' in para or '！' in para) and len(para) < 150:
            quotes.append(para.strip())
    
    if quotes:
        summary += "---\n\n## 💬 关键语录\n\n"
        for q in quotes[:5]:
            summary += f"> {q}\n\n"
    
    summary += f"\n*注：这是自动生成的简化整理稿，详细内容见下方完整文字稿。*"
    
    print(f"[整理稿] 生成完成，{len(summary)} 字符")
    return summary


def aggregate_timeline_segments(segments: List[dict], max_segments: int = 20) -> List[dict]:
    """
    将时间轴片段分段聚合，避免一句话一条
    策略：按内容语义相近性合并相邻片段，目标控制在 max_segments 以内
    
    返回：聚合后的片段列表
    """
    if not segments or len(segments) <= max_segments:
        return segments
    
    print(f"[时间轴] 正在聚合时间轴：{len(segments)} 个片段 → 目标 {max_segments} 个")
    
    # 简单策略：按固定比例合并
    # 计算每组需要合并多少个片段
    group_size = len(segments) // max_segments + 1
    
    aggregated = []
    i = 0
    while i < len(segments):
        # 取一组片段
        group = segments[i:i + group_size]
        if not group:
            break
        
        # 合并这组片段
        start_time = group[0].get('start', 0)
        end_time = group[-1].get('end', 0)
        merged_text = ' '.join(seg.get('text', '').strip() for seg in group if seg.get('text'))
        
        aggregated.append({
            'start': start_time,
            'end': end_time,
            'text': merged_text.strip()
        })
        
        i += group_size
    
    print(f"[时间轴] 聚合完成：{len(aggregated)} 个片段")
    return aggregated


def generate_video_markdown(note_data: dict, transcript: dict, structured_summary: str = None, aggregated_segments: List[dict] = None) -> str:
    """生成 Markdown 内容（视频笔记）"""
    collected_date = datetime.now().strftime("%Y-%m-%d")
    
    # 构建内容
    md = f"""---
tags: [小红书，视频转录，收藏]
source: {note_data.get('url', '')}
author: {note_data.get('author', '未知')}
publish_date: {note_data.get('publish_date', '')}
collected_date: {collected_date}
type: video
duration: {transcript.get('duration', '未知')}
transcription_model: mlx-community/whisper-medium-mlx
---

# {note_data.get('title', '无标题')}

> **作者：** {note_data.get('author', '未知')}  
> **视频时长：** {transcript.get('duration', '未知')}  
> **转录工具：** video-whisper (mlx-whisper)

---

## 📋 结构化总结

{structured_summary if structured_summary else '*（待整理）*'}

---

## 📝 完整文字稿

{transcript.get('text', '转录失败')}

---

## 📍 分段式时间轴

"""
    
    # 使用聚合后的时间轴（如果有）
    segments = aggregated_segments if aggregated_segments else transcript.get('segments', [])
    for i, seg in enumerate(segments, 1):
        start = seg.get('start', 0)
        end = seg.get('end', 0)
        text = seg.get('text', '')
        
        # 转换为分钟：秒格式
        start_str = f"{int(start // 60)}:{int(start % 60):02d}"
        end_str = f"{int(end // 60)}:{int(end % 60):02d}"
        
        md += f"- **[{start_str}-{end_str}]** {text}\n"
    
    md += f"\n---\n\n**转录完成时间：** {collected_date}\n"
    
    return md


def detect_note_type(note_card: dict) -> str:
    """
    检测笔记类型：图文 or 视频
    返回："image" 或 "video"
    """
    # 检查是否有视频信息
    if note_card.get('type') == 'video':
        return 'video'
    
    # 检查 video 字段
    if note_card.get('video'):
        return 'video'
    
    # 检查 media 中的视频信息
    media = note_card.get('media', {})
    if media.get('stream') or media.get('video'):
        return 'video'
    
    # 检查 image_list
    image_list = note_card.get('image_list', [])
    if image_list:
        return 'image'
    
    # 默认当作图文
    return 'image'


async def transcribe_video(url: str, note_id: str) -> Optional[dict]:
    """
    调用 video-whisper 转录视频
    返回转录结果：{'text': str, 'segments': list, 'duration': str}
    """
    print(f"[视频转录] 开始转录视频：{url}")
    
    if not WHISPER_SCRIPT.exists():
        print(f"[视频转录] 错误：找不到转录脚本 {WHISPER_SCRIPT}")
        return None
    
    try:
        # 运行转录脚本
        env = os.environ.copy()
        env['WHISPER_PYTHON'] = str(WHISPER_PYTHON)
        
        result = subprocess.run(
            ['bash', str(WHISPER_SCRIPT), url],
            capture_output=True,
            text=True,
            timeout=600,  # 10 分钟超时
            env=env
        )
        
        if result.returncode != 0:
            print(f"[视频转录] 转录失败：{result.stderr}")
            return None
        
        # 读取转录结果
        output_txt = Path("/tmp/whisper_output.txt")
        output_json = Path("/tmp/whisper_output.json")
        
        transcript_text = ""
        segments = []
        
        if output_txt.exists():
            transcript_text = output_txt.read_text(encoding='utf-8')
        
        if output_json.exists():
            with open(output_json, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                segments = json_data.get('segments', [])
        
        print(f"[视频转录] 转录完成，{len(segments)} 个片段，{len(transcript_text)} 字符")
        
        return {
            'text': transcript_text,
            'segments': segments,
            'duration': json_data.get('duration', '未知') if output_json.exists() else '未知'
        }
        
    except subprocess.TimeoutExpired:
        print("[视频转录] 超时（超过 10 分钟）")
        return None
    except Exception as e:
        print(f"[视频转录] 错误：{e}")
        return None


async def expand_short_url(url: str) -> str:
    """展开 xhslink.com 短链接"""
    if "xhslink.com" in url:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, allow_redirects=True) as resp:
                    final_url = str(resp.url)
                    print(f"短链接展开：{url} -> {final_url}")
                    return final_url
            except Exception as e:
                print(f"展开短链接失败：{e}")
    return url


async def collect_xhs_note(url: str, output_dir: str = DEFAULT_OUTPUT_DIR):
    """主函数：收藏小红书笔记到 Obsidian（支持图文和视频）"""
    
    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    image_dir = Path(DEFAULT_IMAGE_DIR)
    image_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"开始解析：{url}")
    
    # 展开短链接
    if "xhslink.com" in url:
        url = await expand_short_url(url)
    
    # 解析 URL
    note_id, xsec_token = parse_xhs_url(url)
    print(f"note_id: {note_id}, xsec_token: {xsec_token}")
    
    # 创建小红书会话（使用配置中的登录态）
    web_session = CONFIG.get("web_session")
    proxy = CONFIG.get("proxy")
    print(f"使用登录态：{'已配置' if web_session else '未配置'}")
    xhs = await create_xhs_session(proxy=proxy, web_session=web_session)
    
    try:
        # 获取笔记详情
        if xsec_token:
            res = await xhs.apis.note.note_detail(note_id, xsec_token)
            data = await res.json()
        else:
            # 尝试搜索获取
            print("需要 xsec_token，尝试从搜索获取...")
            data = None
        
        if not data:
            print("无法获取笔记详情，可能需要登录态或正确的 xsec_token")
            return
        
        # 小红书 API 返回结构：data.items[0].note_card
        items = data.get('data', {}).get('items', [])
        if not items:
            print("无法获取笔记内容，API 返回空数据")
            return
        
        note_card = items[0].get('note_card', {})
        
        # 检测笔记类型
        note_type = detect_note_type(note_card)
        print(f"笔记类型：{note_type}")
        
        # 提取基本信息
        note_data = {
            'url': url,
            'title': note_card.get('title') or note_card.get('display_title') or '无标题',
            'author': note_card.get('user', {}).get('nickname', '未知'),
            'publish_date': note_card.get('time', ''),
            'content': note_card.get('desc', ''),
        }
        
        print(f"标题：{note_data['title']}")
        print(f"作者：{note_data['author']}")
        
        # 根据类型处理
        if note_type == 'video':
            # 视频笔记：转录
            print(f"内容长度：视频")
            
            # 转录视频
            transcript = await transcribe_video(url, note_id)
            
            if not transcript:
                print("转录失败，尝试降级为图文模式...")
                # 降级处理：当作图文
                note_type = 'image'
            else:
                # 保存完整文字稿到临时文件，供 KK 后续总结
                transcript_txt = Path(f"/tmp/xhs_transcript_{note_id}.txt")
                transcript_txt.write_text(transcript.get('text', ''), encoding='utf-8')
                
                # 时间轴分段聚合
                aggregated_segments = None
                timeline_enabled = CONFIG.get("timeline_segment_enabled", True)
                if timeline_enabled:
                    max_segments = CONFIG.get("timeline_segment_max", 20)
                    aggregated_segments = aggregate_timeline_segments(
                        transcript.get('segments', []),
                        max_segments=max_segments
                    )
                
                # 保存文件
                safe_title = re.sub(r'[^\w\u4e00-\u9fff-]', '_', note_data['title'])[:50]
                filename = f"视频转录-{note_data['author']}-{safe_title}.md"
                filepath = output_path / filename
                
                # 先保存一个占位版本
                structured_summary_placeholder = f"""*📝 结构化总结生成中 —— KK 正在处理...*

> 完整文字稿已保存，KK 将自动生成结构化总结（分级标题 + 要点列表 + 金句 + 表格）。"""
                
                md_content_placeholder = generate_video_markdown(
                    note_data, 
                    transcript, 
                    structured_summary_placeholder,
                    aggregated_segments
                )
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(md_content_placeholder)
                
                # 保存文件路径到临时文件，方便 KK 找到
                Path(f"/tmp/xhs_md_path_{note_id}.txt").write_text(str(filepath), encoding='utf-8')
                
                print(f"\n✅ 视频转录完成：{filepath}")
                print(f"⏱️ 时间轴已聚合：{len(aggregated_segments) if aggregated_segments else len(transcript.get('segments', []))} 段")
                
                # 自动触发 KK 后处理（方案 A：调用 auto_summary.py）
                auto_summary_enabled = CONFIG.get("auto_summary_enabled", True)
                if auto_summary_enabled:
                    # 调用 auto_summary.py 触发通知
                    auto_summary_script = Path(__file__).parent / "auto_summary.py"
                    if auto_summary_script.exists():
                        subprocess.run(
                            [sys.executable, str(auto_summary_script), note_id],
                            capture_output=True,
                            text=True
                        )
                        print(f"🔔 已通知 KK 自动生成结构化总结...")
                    else:
                        print(f"⚠️ 找不到 auto_summary.py，使用手动处理")
                        print(f"📋 结构化总结待处理（临时文件：/tmp/xhs_transcript_{note_id}.txt）")
                else:
                    print(f"📋 结构化总结待手动处理（临时文件：/tmp/xhs_transcript_{note_id}.txt）")
                
                return
        
        # 图文笔记：下载图片 + OCR（或降级处理）
        if note_type == 'image':
            print(f"内容长度：{len(note_data['content'])}")
            
            # 下载图片
            image_list = note_card.get('image_list', [])
            if not image_list:
                # 尝试从 media 获取
                media = note_card.get('media', {})
                image_list = media.get('images', [])
            
            image_paths = []
            ocr_results = []
            
            image_max_count = CONFIG.get("image_max_count", 25)
            async with aiohttp.ClientSession() as http_session:
                for i, img_info in enumerate(image_list[:image_max_count], 1):  # 最多 25 张
                    img_url = img_info.get('url', '')
                    if not img_url and isinstance(img_info, dict):
                        # 尝试其他可能的字段
                        img_url = img_info.get('origin_url', '') or img_info.get('url_default', '')
                    
                    if img_url:
                        filename = f"xhs_{note_id}_{i}.jpg"
                        save_path = image_dir / filename
                        
                        if await download_image(http_session, img_url, str(save_path)):
                            image_paths.append(str(save_path))
                            
                            # OCR 识别
                            ocr_text = await ocr_image(str(save_path))
                            ocr_results.append(ocr_text)
                            
                            print(f"下载图片 {i}/{len(image_list)}: {filename}")
            
            # 生成 Markdown
            md_content = generate_markdown(note_data, image_paths, ocr_results)
            
            # 保存文件
            safe_title = re.sub(r'[^\w\u4e00-\u9fff-]', '_', note_data['title'])[:50]
            filename = f"小红书-{note_data['author']}-{safe_title}.md"
            filepath = output_path / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            print(f"\n✅ 收藏完成：{filepath}")
        
    finally:
        await xhs.close_session()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python collect.py <小红书分享链接> [输出目录]")
        sys.exit(1)
    
    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTPUT_DIR
    
    asyncio.run(collect_xhs_note(url, output_dir))

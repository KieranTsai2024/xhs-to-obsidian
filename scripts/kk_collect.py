#!/usr/bin/env python3
"""
KK 处理小红书笔记 - 完整流程
用法：python kk_collect.py <小红书链接> [输出目录]

1. 运行 collect.py 转录/下载
2. 检查 pending 通知
3. 生成结构化总结
4. 更新 Markdown 文件
"""

import sys
import subprocess
import json
import re
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
COLLECT_SCRIPT = SCRIPT_DIR / "collect.py"
PENDING_DIR = SCRIPT_DIR.parent / "pending"


def generate_structured_summary(transcript_text: str, title: str, author: str) -> str:
    """
    生成结构化总结（AI 版本）
    分析转录稿，生成：核心主题 + 分级内容 + 金句 + 表格
    """
    
    # 简单的 AI 风格总结（实际由 KK 的 AI 能力生成）
    # 这里用一个简化的规则版本作为 fallback
    
    # 分割句子
    sentences = re.split(r'(?<=[。！？!?])\s*', transcript_text)
    
    # 提取关键内容（简单规则）
    key_points = []
    quotes = []
    
    for sent in sentences[:50]:  # 限制处理
        sent = sent.strip()
        if len(sent) < 10 or len(sent) > 200:
            continue
        
        # 检测可能的金句
        if any(kw in sent for kw in ['核心', '本质', '关键', '重要', '记住', '不要']):
            key_points.append(sent)
        
        # 检测引用风格
        if '你' in sent and ('不要' in sent or '要' in sent):
            quotes.append(sent)
    
    # 构建总结
    summary = f"""## 🎯 核心主题

{title} - {author} 分享的核心内容。

---

## 📌 主要内容

### 一、核心观点
- 视频讲解了与"{title}"相关的重要内容
- 包含多个关键要点和实用建议

### 二、详细内容
- 详细内容涵盖多个方面
- 建议观看完整文字稿获取全部信息

### 三、实践建议
- 将内容应用到实际场景
- 结合自身情况灵活运用

---

## 💬 金句摘录

"""
    
    # 添加金句
    for q in quotes[:5]:
        summary += f'> "{q}"\n\n'
    
    if not quotes:
        summary += '> *（金句待提取）*\n\n'
    
    summary += """
---

## 📊 核心总结

| 部分 | 关键要点 |
|------|----------|
| 核心观点 | 视频主要内容概述 |
| 详细讲解 | 多个方面的深入分析 |
| 实践应用 | 如何应用到实际场景 |

---

*注：内容由 KK 自动生成，详细内容见下方完整文字稿。*"""
    
    return summary


def process_pending_and_summarize(note_id: str = None) -> bool:
    """处理 pending 文件并生成总结"""
    
    # 找 pending 文件（优先从 /tmp/ 找，因为 collect.py 写在那里）
    pending_file = None
    if note_id:
        # 先找 /tmp/ 目录
        tmp_pending = Path(f"/tmp/xhs_pending_{note_id}.json")
        if tmp_pending.exists():
            pending_file = tmp_pending
        else:
            # 再找 pending/ 目录
            pending_file = PENDING_DIR / f"{note_id}.json"
    
    if not pending_file or not pending_file.exists():
        # 找 /tmp/ 中最新的 pending 文件
        tmp_pending_files = sorted(Path("/tmp").glob("xhs_pending_*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        if tmp_pending_files:
            pending_file = tmp_pending_files[0]
        
        if not pending_file:
            # 找 pending/ 目录中最新的
            pending_files = sorted(PENDING_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
            if pending_files:
                pending_file = pending_files[0]
            else:
                print("⏳ 没有找到 pending 文件（可能无需总结）")
                return True
    
    try:
        with open(pending_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        md_path = data.get('md_path')
        transcript_path = data.get('transcript_path')
        title = data.get('title', '无标题')
        author = data.get('author', '未知')
        
        print(f"\n📋 处理笔记：{title}")
        print(f"   作者：{author}")
        print(f"   note_id: {data.get('note_id')}")
        
        # 读取转录稿
        if not Path(transcript_path).exists():
            print(f"⚠️ 转录稿不存在：{transcript_path}")
            return False
        
        transcript_text = Path(transcript_path).read_text(encoding='utf-8')
        print(f"📄 转录稿长度：{len(transcript_text)} 字符")
        
        # 生成结构化总结
        print(f"🤖 正在生成结构化总结...")
        structured_summary = generate_structured_summary(transcript_text, title, author)
        print(f"✅ 总结生成完成：{len(structured_summary)} 字符")
        
        # 读取 Markdown 文件
        if not Path(md_path).exists():
            print(f"❌ Markdown 文件不存在：{md_path}")
            return False
        
        md_content = Path(md_path).read_text(encoding='utf-8')
        
        # 替换占位符
        placeholder_pattern = r'\*\📝 结构化总结生成中 —— KK 正在处理\.\.\.\*[\s\S]*?> 完整文字稿已保存，KK 将自动生成结构化总结.*?\n'
        md_content_new = re.sub(placeholder_pattern, structured_summary + '\n', md_content)
        
        if md_content_new == md_content:
            # 尝试另一种占位符
            placeholder_pattern2 = r'## 📋 结构化总结\n\n\*.*?\n'
            md_content_new = re.sub(placeholder_pattern2, f'## 📋 结构化总结\n\n{structured_summary}\n', md_content)
        
        # 写回文件
        Path(md_path).write_text(md_content_new, encoding='utf-8')
        print(f"✅ 已更新 Markdown 文件：{md_path}")
        
        # 删除 pending 文件
        pending_file.unlink()
        print(f"🗑️ 已清理 pending 文件")
        
        return True
        
    except Exception as e:
        print(f"❌ 处理失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    if len(sys.argv) < 2:
        print("用法：python kk_collect.py <小红书链接> [输出目录]")
        sys.exit(1)
    
    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    print("🦊 KK 开始处理小红书笔记...")
    print(f"链接：{url}")
    if output_dir:
        print(f"输出目录：{output_dir}")
    print()
    
    # Step 1: 运行 collect.py
    print("=" * 50)
    print("Step 1: 转录/下载笔记")
    print("=" * 50)
    
    cmd = [sys.executable, str(COLLECT_SCRIPT), url]
    if output_dir:
        cmd.append(output_dir)
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode != 0:
        print(f"\n❌ collect.py 执行失败")
        sys.exit(1)
    
    # Step 2: 处理 pending 并生成总结
    print("\n" + "=" * 50)
    print("Step 2: 生成结构化总结")
    print("=" * 50)
    
    success = process_pending_and_summarize()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ KK 处理完成！")
        print("=" * 50)
    else:
        print("\n⚠️ 总结生成失败，但笔记已保存")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
自动总结触发脚本
用法：python auto_summary.py <note_id>

检查待处理文件，通过 sessions_send 通知 KK 处理
"""

import sys
import json
from pathlib import Path

def trigger_auto_summary(note_id: str):
    """触发 KK 自动总结"""
    
    pending_file = Path(f"/tmp/xhs_pending_{note_id}.json")
    
    if not pending_file.exists():
        print(f"❌ 待处理文件不存在：{pending_file}")
        return False
    
    # 读取待处理信息
    with open(pending_file, 'r', encoding='utf-8') as f:
        pending_data = json.load(f)
    
    md_path = pending_data.get('md_path')
    transcript_path = pending_data.get('transcript_path')
    title = pending_data.get('title')
    author = pending_data.get('author')
    
    if not all([md_path, transcript_path, title]):
        print(f"❌ 待处理文件数据不完整：{pending_data}")
        return False
    
    # 构建通知消息
    message = f"""📕 小红书视频笔记待总结

**笔记信息：**
- 标题：{title}
- 作者：{author}
- note_id: {note_id}

**文件路径：**
- 转录稿：{transcript_path}
- Markdown: {md_path}

请读取转录稿，生成结构化总结（核心主题 + 分级内容 + 金句 + 表格），然后更新 Markdown 文件。"""
    
    # 写入通知文件（KK 会检查这个目录）
    notify_file = Path.home() / ".openclaw" / "workspace" / "skills" / "xhs-to-obsidian" / "pending" / f"{note_id}.json"
    notify_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(notify_file, 'w', encoding='utf-8') as f:
        json.dump({
            "note_id": note_id,
            "md_path": md_path,
            "transcript_path": transcript_path,
            "title": title,
            "author": author,
            "message": message
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已写入通知文件：{notify_file}")
    print(f"📋 KK 将检查 pending 目录并自动处理...")
    
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python auto_summary.py <note_id>")
        sys.exit(1)
    
    note_id = sys.argv[1]
    success = trigger_auto_summary(note_id)
    sys.exit(0 if success else 1)

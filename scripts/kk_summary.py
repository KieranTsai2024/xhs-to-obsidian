#!/usr/bin/env python3
"""
KK 生成结构化总结并更新 Markdown 文件
用法：python kk_summary.py <note_id>

读取转录稿，用 KK 的 AI 能力生成结构化总结，更新 MD 文件
"""

import sys
import json
import re
from pathlib import Path

PENDING_DIR = Path.home() / ".openclaw" / "workspace" / "skills" / "xhs-to-obsidian" / "pending"


def generate_summary_with_kk(transcript_text: str, title: str, author: str) -> str:
    """
    调用 KK 生成结构化总结
    这里通过写入一个请求文件，让 KK 的主进程读取并生成
    """
    # 写入请求文件
    request_file = Path("/tmp/xhs_kk_summary_request.json")
    request_file.write_text(json.dumps({
        "transcript": transcript_text[:15000],  # 限制长度
        "title": title,
        "author": author
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    
    print(f"📝 已写入 KK 总结请求：{request_file}")
    return None  # KK 会处理这个文件


def process_pending(note_id: str) -> bool:
    """处理 pending 文件并生成总结"""
    
    pending_file = PENDING_DIR / f"{note_id}.json"
    
    if not pending_file.exists():
        # 尝试找任意 pending 文件
        pending_files = list(PENDING_DIR.glob("*.json"))
        if pending_files:
            pending_file = pending_files[0]
        else:
            print(f"❌ 没有找到 pending 文件")
            return False
    
    try:
        with open(pending_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        md_path = data.get('md_path')
        transcript_path = data.get('transcript_path')
        title = data.get('title', '无标题')
        author = data.get('author', '未知')
        
        print(f"📋 处理笔记：{title}")
        print(f"   作者：{author}")
        print(f"   MD 文件：{md_path}")
        
        # 读取转录稿
        if not Path(transcript_path).exists():
            print(f"❌ 转录稿不存在：{transcript_path}")
            return False
        
        transcript_text = Path(transcript_path).read_text(encoding='utf-8')
        print(f"📄 转录稿长度：{len(transcript_text)} 字符")
        
        # 生成结构化总结（KK 会在这里生成）
        print(f"🤖 正在生成结构化总结...")
        
        # 这里直接调用 KK 的总结逻辑
        # 为了简化，我们写入一个请求文件，让 KK 的主进程处理
        request_file = Path("/tmp/xhs_kk_summary_request.json")
        request_file.write_text(json.dumps({
            "transcript": transcript_text[:15000],
            "title": title,
            "author": author,
            "md_path": md_path,
            "pending_file": str(pending_file)
        }, ensure_ascii=False, indent=2), encoding='utf-8')
        
        print(f"✅ 已写入 KK 总结请求：{request_file}")
        print(f"🔔 KK 将读取并生成结构化总结...")
        
        return True
        
    except Exception as e:
        print(f"❌ 处理失败：{e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        note_id = sys.argv[1]
    else:
        note_id = None
    
    success = process_pending(note_id)
    sys.exit(0 if success else 1)

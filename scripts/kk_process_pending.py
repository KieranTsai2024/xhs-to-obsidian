#!/usr/bin/env python3
"""
KK 处理 xhs-to-obsidian 待总结通知
检查 pending 目录，读取转录稿，生成结构化总结，更新 Markdown 文件
"""

import json
import re
from pathlib import Path
from datetime import datetime

PENDING_DIR = Path.home() / ".openclaw" / "workspace" / "skills" / "xhs-to-obsidian" / "pending"


def generate_structured_summary(transcript_text: str, title: str, author: str) -> str:
    """
    生成结构化总结（KK 版本）
    格式：核心主题 + 分级内容 + 金句 + 表格
    """
    # 这里由 KK 的 AI 能力生成
    # 为了演示，返回一个占位符
    # 实际使用时，KK 会读取这个文件并用自己的能力生成
    
    return f"""## 🎯 核心主题

[KK 将在这里生成 1-2 句话的核心主题概括]

---

## 📌 主要内容

### 一、[章节 1 标题]
- [要点 1]
- [要点 2]

### 二、[章节 2 标题]
- [要点 1]
- [要点 2]

### 三、[章节 3 标题]
- [要点 1]
- [要点 2]

---

## 💬 金句摘录

> "[金句 1]"

> "[金句 2]"

> "[金句 3]"

---

## 📊 核心总结

| 部分 | 关键要点 |
|------|----------|
| [部分 1] | [要点] |
| [部分 2] | [要点] |
| [部分 3] | [要点] |

---

*注：内容由 KK 自动生成，详细内容见下方完整文字稿。*"""


def process_pending_file(pending_path: Path) -> bool:
    """处理单个 pending 文件"""
    
    try:
        with open(pending_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        note_id = data.get('note_id')
        md_path = data.get('md_path')
        transcript_path = data.get('transcript_path')
        title = data.get('title', '无标题')
        author = data.get('author', '未知')
        
        print(f"📋 处理笔记：{title}")
        print(f"   note_id: {note_id}")
        print(f"   MD 文件：{md_path}")
        print(f"   转录稿：{transcript_path}")
        
        # 读取转录稿
        if not Path(transcript_path).exists():
            print(f"❌ 转录稿不存在：{transcript_path}")
            return False
        
        transcript_text = Path(transcript_path).read_text(encoding='utf-8')
        
        # 生成结构化总结（KK 会在这里用自己的能力生成）
        print(f"🤖 正在生成结构化总结...")
        structured_summary = generate_structured_summary(transcript_text, title, author)
        
        # 读取 Markdown 文件
        if not Path(md_path).exists():
            print(f"❌ Markdown 文件不存在：{md_path}")
            return False
        
        md_content = Path(md_path).read_text(encoding='utf-8')
        
        # 替换占位符
        placeholder_pattern = r'\*\📝 结构化总结生成中 —— KK 正在处理\.\.\.\*[\s\S]*?> 完整文字稿已保存，KK 将自动生成结构化总结.*?\n'
        md_content = re.sub(placeholder_pattern, structured_summary + '\n', md_content)
        
        # 写回文件
        Path(md_path).write_text(md_content, encoding='utf-8')
        
        print(f"✅ 已更新 Markdown 文件：{md_path}")
        
        # 删除 pending 文件
        pending_path.unlink()
        print(f"🗑️ 已删除 pending 文件：{pending_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ 处理失败：{e}")
        return False


def check_and_process():
    """检查并处理所有 pending 文件"""
    
    if not PENDING_DIR.exists():
        print(f"⏳ pending 目录不存在，无需处理")
        return
    
    pending_files = list(PENDING_DIR.glob("*.json"))
    
    if not pending_files:
        print(f"⏳ pending 目录为空，无需处理")
        return
    
    print(f"📬 发现 {len(pending_files)} 个待处理笔记")
    
    for pending_file in pending_files:
        print(f"\n--- 处理：{pending_file.name} ---")
        success = process_pending_file(pending_file)
        if success:
            print(f"✅ 完成：{pending_file.name}")
        else:
            print(f"❌ 失败：{pending_file.name}")


if __name__ == "__main__":
    check_and_process()

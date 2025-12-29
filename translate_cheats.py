#!/usr/bin/env python3
"""
翻译 public/cheats 目录下所有 .cht 文件中的 cheat*_desc 英文描述为中文
"""

import os
import re
import time
from pathlib import Path
from deep_translator import GoogleTranslator


def translate_text(text, retries=3):
    """翻译文本，带重试机制"""
    print(f"    正在翻译: {text[:50]}...", end=" ", flush=True)
    for attempt in range(retries):
        try:
            translator = GoogleTranslator(source='en', target='zh-CN')
            result = translator.translate(text)
            if result:
                print(f"-> {result[:50]}...")
                return result
            else:
                print("-> [保持原文]")
                return text
        except Exception as e:
            if attempt < retries - 1:
                print(f"[重试{attempt+1}]", end=" ", flush=True)
                time.sleep(1)
            else:
                print(f"-> [翻译失败: {e}]")
                return text
    return text


def translate_cht_file(file_path, dry_run=True):
    """翻译单个 .cht 文件中的描述"""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    # 匹配 cheat*_desc = "..." 格式
    desc_pattern = re.compile(r'^(cheat\d+_desc\s*=\s*)"(.+)"$')
    
    modified = False
    new_lines = []
    translations = []
    
    for line in lines:
        match = desc_pattern.match(line.strip())
        if match:
            prefix = match.group(1)
            english_desc = match.group(2)
            
            # 检查是否已经是中文（包含中文字符）
            if re.search(r'[\u4e00-\u9fff]', english_desc):
                new_lines.append(line)
                continue
            
            # 翻译
            chinese_desc = translate_text(english_desc)
            
            if chinese_desc != english_desc:
                translations.append((english_desc, chinese_desc))
                # 保持原始行的缩进
                leading_space = len(line) - len(line.lstrip())
                new_line = ' ' * leading_space + f'{prefix}"{chinese_desc}"\n'
                new_lines.append(new_line)
                modified = True
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    if modified and not dry_run:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    
    return translations


def translate_all_cheats(cheats_dir, dry_run=True, limit=None):
    """翻译目录下所有 .cht 文件"""
    cht_files = list(Path(cheats_dir).glob('*.cht'))
    print(f"找到 {len(cht_files)} 个 .cht 文件")
    
    if limit:
        cht_files = cht_files[:limit]
        print(f"限制处理前 {limit} 个文件")
    
    total_translations = 0
    processed_files = 0
    
    for i, cht_file in enumerate(cht_files, 1):
        print(f"\n[{i}/{len(cht_files)}] 正在处理: {cht_file.name}")
        
        try:
            translations = translate_cht_file(str(cht_file), dry_run=dry_run)
            
            if translations:
                total_translations += len(translations)
                processed_files += 1
                print(f"  ✓ 已翻译 {len(translations)} 条描述")
            else:
                print(f"  - 无需翻译（已是中文或无描述）")
                
            # 添加延时避免API限制
            if translations:
                time.sleep(0.3)
                
        except Exception as e:
            print(f"  ✗ 错误: {e}")
    
    print(f"\n{'='*50}")
    print(f"=== 翻译完成 ===")
    print(f"处理文件数: {len(cht_files)}")
    print(f"翻译文件数: {processed_files}")
    print(f"总共翻译描述: {total_translations} 条")
    print(f"{'='*50}")
    
    if dry_run:
        print("\n这是模拟运行，文件未被修改。使用 --execute 参数实际执行。")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='翻译CHT文件中的英文描述为中文')
    parser.add_argument('--dry-run', action='store_true', help='仅显示将要执行的操作，不实际修改文件')
    parser.add_argument('--execute', action='store_true', help='实际执行翻译操作')
    parser.add_argument('--limit', type=int, help='限制处理的文件数量（用于测试）')
    
    args = parser.parse_args()
    
    # 路径配置
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cheats_dir = os.path.join(base_dir, 'public', 'cheats')
    
    dry_run = not args.execute
    
    if dry_run:
        print("=== 模拟运行模式 (使用 --execute 参数实际执行) ===\n")
    else:
        print("=== 实际执行模式 ===\n")
    
    translate_all_cheats(cheats_dir, dry_run=dry_run, limit=args.limit)

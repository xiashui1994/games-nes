#!/usr/bin/env python3
"""
根据 games.json 中的游戏名称，将 cheats 目录下对应的 cht 文件
复制到 public/cheats 目录下，并重命名为 games.name.cht
"""

import json
import os
import shutil
import re
import pandas as pd
from pathlib import Path


def normalize_name(name: str) -> str:
    """标准化游戏名称，用于匹配"""
    if not name or pd.isna(name):
        return ""
    # 移除特殊字符，转为小写
    name = str(name).lower()
    # 移除括号内的内容
    name = re.sub(r'\([^)]*\)', '', name)
    name = re.sub(r'\[[^\]]*\]', '', name)
    # 只保留字母数字
    name = re.sub(r'[^a-z0-9]', '', name)
    return name


def extract_english_names(name_en: str) -> list:
    """从英文名称字段提取所有可能的英文名"""
    if not name_en or pd.isna(name_en):
        return []
    # 使用 ; 分隔多个名称
    names = [n.strip() for n in str(name_en).split(';')]
    # 移除空名称和方括号标记的别名
    names = [n for n in names if n and not n.startswith('[')]
    return names


def extract_chinese_names(name_cn: str) -> list:
    """从中文名称字段提取所有可能的中文名"""
    if not name_cn or pd.isna(name_cn):
        return []
    # 使用 ； 或 ; 分隔多个名称
    names = re.split(r'[；;]', str(name_cn))
    names = [n.strip() for n in names]
    # 移除空名称和方括号标记的别名
    names = [n for n in names if n and not n.startswith('[')]
    return names


def build_name_mapping(excel_path: str) -> dict:
    """
    构建中文名到英文名的映射
    返回: {normalized_chinese_name: [english_names]}
    """
    df = pd.read_excel(excel_path, skiprows=1)
    mapping = {}
    
    for _, row in df.iterrows():
        chinese_names = extract_chinese_names(row.get('name_cn', ''))
        english_names = extract_english_names(row.get('name_en', ''))
        
        if not english_names:
            continue
            
        for cn_name in chinese_names:
            normalized = normalize_name(cn_name)
            if normalized:
                if normalized not in mapping:
                    mapping[normalized] = []
                mapping[normalized].extend(english_names)
                
        # 也用原始中文名作为key
        for cn_name in chinese_names:
            if cn_name:
                if cn_name not in mapping:
                    mapping[cn_name] = []
                mapping[cn_name].extend(english_names)
    
    return mapping


def find_cheat_file(english_names: list, cheats_dir: str, cheat_files: list):
    """
    在cheats目录中查找匹配的cht文件
    返回匹配的文件名
    
    匹配优先级：
    1. 完全匹配（标准化后）
    2. 英文名在cheat文件名开头（标准化后）
    """
    # 预处理cheat文件名
    cheat_mapping = {}
    for cheat_file in cheat_files:
        cheat_base = os.path.splitext(cheat_file)[0]
        normalized_cheat = normalize_name(cheat_base)
        if normalized_cheat:
            cheat_mapping[normalized_cheat] = cheat_file
    
    # 第一轮：精确匹配
    for en_name in english_names:
        normalized_en = normalize_name(en_name)
        if normalized_en and normalized_en in cheat_mapping:
            return cheat_mapping[normalized_en]
    
    # 第二轮：英文名作为cheat文件名的前缀匹配
    for en_name in english_names:
        normalized_en = normalize_name(en_name)
        if not normalized_en or len(normalized_en) < 5:  # 名称太短，跳过前缀匹配
            continue
        
        for normalized_cheat, cheat_file in cheat_mapping.items():
            # 检查cheat文件名是否以英文名开头
            if normalized_cheat.startswith(normalized_en):
                return cheat_file
    
    return None


def copy_cheats(games_json_path: str, excel_path: str, cheats_dir: str, output_dir: str, unknown_file: str, dry_run: bool = True):
    """
    主函数：复制并重命名cheat文件
    """
    # 加载games.json
    with open(games_json_path, 'r', encoding='utf-8') as f:
        games_data = json.load(f)
    
    games = games_data.get('games', [])
    print(f"找到 {len(games)} 个游戏")
    
    # 构建中英文名称映射
    name_mapping = build_name_mapping(excel_path)
    print(f"构建了 {len(name_mapping)} 个名称映射")
    
    # 获取cheats目录下的所有cht文件
    cheat_files = [f for f in os.listdir(cheats_dir) if f.endswith('.cht')]
    print(f"找到 {len(cheat_files)} 个cheat文件")
    
    # 创建输出目录
    if not dry_run:
        os.makedirs(output_dir, exist_ok=True)
    
    # 统计
    found_count = 0
    not_found = []
    copied_files = []
    
    for game in games:
        game_name = game.get('name', '')
        if not game_name:
            continue
        
        # 尝试在映射中查找
        english_names = []
        
        # 直接查找
        if game_name in name_mapping:
            english_names = name_mapping[game_name]
        else:
            # 标准化查找
            normalized = normalize_name(game_name)
            if normalized in name_mapping:
                english_names = name_mapping[normalized]
        
        # 查找对应的cheat文件
        cheat_file = None
        if english_names:
            cheat_file = find_cheat_file(english_names, cheats_dir, cheat_files)
        
        if cheat_file:
            found_count += 1
            src_path = os.path.join(cheats_dir, cheat_file)
            dst_path = os.path.join(output_dir, f"{game_name}.cht")
            
            if dry_run:
                print(f"[DRY RUN] 复制: {cheat_file} -> {game_name}.cht")
            else:
                shutil.copy2(src_path, dst_path)
                print(f"复制: {cheat_file} -> {game_name}.cht")
            
            copied_files.append({
                'game_name': game_name,
                'source': cheat_file,
                'english_names': english_names[:3] if english_names else []
            })
        else:
            not_found.append(game_name)
    
    print(f"\n=== 统计 ===")
    print(f"找到并复制: {found_count} 个")
    print(f"未找到: {len(not_found)} 个")
    
    # 将未找到的游戏写入unknown.txt
    with open(unknown_file, 'w', encoding='utf-8') as f:
        for name in not_found:
            f.write(f"{name}\n")
    print(f"未找到的游戏已写入: {unknown_file}")
    
    if not_found:
        print(f"\n未找到cheat的游戏 (前20个):")
        for name in not_found[:20]:
            print(f"  - {name}")
    
    return copied_files, not_found


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='复制并重命名NES游戏cheat文件')
    parser.add_argument('--dry-run', action='store_true', help='仅显示将要执行的操作，不实际复制文件')
    parser.add_argument('--execute', action='store_true', help='实际执行复制操作')
    
    args = parser.parse_args()
    
    # 路径配置
    base_dir = os.path.dirname(os.path.abspath(__file__))
    games_json_path = os.path.join(base_dir, 'public', 'games.json')
    excel_path = os.path.join(base_dir, '游戏列表.xls')
    cheats_dir = os.path.join(base_dir, 'cheats')
    output_dir = os.path.join(base_dir, 'public', 'cheats')
    unknown_file = os.path.join(base_dir, 'unknown.txt')
    
    dry_run = not args.execute
    
    if dry_run:
        print("=== 模拟运行模式 (使用 --execute 参数实际执行) ===\n")
    else:
        print("=== 实际执行模式 ===\n")
    
    copy_cheats(games_json_path, excel_path, cheats_dir, output_dir, unknown_file, dry_run=dry_run)

#!/usr/bin/env python3
"""
为 games.json 中的每个游戏添加 cheats 字段
如果 public/cheats 目录下存在对应的 .cht 文件，则设置路径
否则设置为空字符串
"""

import json
import os
from pathlib import Path


def add_cheats_field(games_json_path, cheats_dir):
    """为games.json添加cheats字段，放在description之前"""
    
    # 读取games.json
    with open(games_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    games = data.get('games', [])
    print(f"找到 {len(games)} 个游戏")
    
    # 获取cheats目录下的所有cht文件名（不含扩展名）
    cht_files = set()
    for f in Path(cheats_dir).glob('*.cht'):
        cht_files.add(f.stem)
    print(f"找到 {len(cht_files)} 个金手指文件")
    
    # 统计
    with_cheats = 0
    without_cheats = 0
    
    # 为每个游戏添加cheats字段
    new_games = []
    for game in games:
        game_name = game.get('name', '')
        
        # 确定cheats值
        if game_name in cht_files:
            cheats_value = f"/cheats/{game_name}.cht"
            with_cheats += 1
        else:
            cheats_value = ""
            without_cheats += 1
        
        # 重新构建game对象，确保cheats在description之前
        new_game = {}
        for key in game:
            if key == 'description':
                new_game['cheats'] = cheats_value
            new_game[key] = game[key]
        
        # 如果没有description字段，在末尾添加cheats
        if 'cheats' not in new_game:
            new_game['cheats'] = cheats_value
        
        new_games.append(new_game)
    
    data['games'] = new_games
    
    # 保存更新后的games.json
    with open(games_json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"\n=== 完成 ===")
    print(f"有金手指: {with_cheats} 个游戏")
    print(f"无金手指: {without_cheats} 个游戏")
    print(f"已更新: {games_json_path}")


if __name__ == "__main__":
    # 路径配置
    base_dir = os.path.dirname(os.path.abspath(__file__))
    games_json_path = os.path.join(base_dir, 'public', 'games.json')
    cheats_dir = os.path.join(base_dir, 'public', 'cheats')
    
    add_cheats_field(games_json_path, cheats_dir)

#!/usr/bin/env python3
"""
DataFrame迁移脚本
用于更新现有的DataFrame结构以支持新的三阶段处理流程
"""

import pandas as pd
from data_cache import data_cache, get_articles_dataframe, save_articles_dataframe

def migrate_dataframe():
    """迁移现有的DataFrame结构"""
    print("开始迁移DataFrame结构...")
    
    try:
        # 加载现有DataFrame
        df = get_articles_dataframe()
        print(f"当前DataFrame形状: {df.shape}")
        print(f"当前列名: {list(df.columns)}")
        
        # 检查是否需要迁移
        required_columns = ['栏目', 'HTML缓存路径']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if not missing_columns:
            print("DataFrame结构已是最新的，无需迁移")
            return True
        
        print(f"需要添加的列: {missing_columns}")
        
        # 检查是否有旧的'内容缓存路径'列需要重命名
        if '内容缓存路径' in df.columns and 'HTML缓存路径' in missing_columns:
            print("正在重命名'内容缓存路径'列为'HTML缓存路径'...")
            df = df.rename(columns={'内容缓存路径': 'HTML缓存路径'})
            missing_columns.remove('HTML缓存路径')
        
        # 移动现有的HTML文件到content文件夹
        if 'HTML缓存路径' in df.columns:
            print("正在移动现有HTML文件到content文件夹...")
            import os
            import shutil
            
            for index, row in df.iterrows():
                if pd.notna(row['HTML缓存路径']) and row['HTML缓存路径']:
                    old_path = row['HTML缓存路径']
                    if os.path.exists(old_path) and not old_path.startswith('content/'):
                        # 移动文件到content文件夹
                        new_path = f"content/{os.path.basename(old_path)}"
                        try:
                            shutil.move(old_path, new_path)
                            # 更新DataFrame中的路径
                            df.at[index, 'HTML缓存路径'] = new_path
                        except Exception as e:
                            print(f"  移动文件失败: {old_path} -> {new_path}: {e}")
            
            print("HTML文件移动完成")
        
        # 添加缺失的列
        for col in missing_columns:
            df[col] = ''
        
        # 如果有'正文内容'列，我们可以将其作为内容缓存
        if '正文内容' in df.columns and 'HTML缓存路径' in df.columns:
            print("正在迁移现有正文内容到HTML缓存...")
            
            for index, row in df.iterrows():
                if pd.notna(row['正文内容']) and row['正文内容'].strip():
                    # 生成HTML缓存路径
                    import hashlib
                    url_hash = hashlib.md5(row['文章链接'].encode()).hexdigest()
                    html_cache_path = f"content_{url_hash}.html"
                    
                    # 创建简单的HTML内容
                    simple_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{row['文章标题']}</title>
</head>
<body>
    <h1>{row['文章标题']}</h1>
    <p>{row['正文内容']}</p>
</body>
</html>"""
                    
                    # 保存HTML内容到缓存
                    data_cache.save_data(simple_html, html_cache_path)
                    
                    # 更新DataFrame
                    df.at[index, 'HTML缓存路径'] = html_cache_path
            
            # 移除旧的正文内容列
            df = df.drop('正文内容', axis=1)
            print("已迁移正文内容并移除旧列")
        
        # 保存更新后的DataFrame
        save_articles_dataframe(df)
        print(f"迁移完成！新DataFrame形状: {df.shape}")
        print(f"新列名: {list(df.columns)}")
        
        return True
        
    except Exception as e:
        print(f"迁移失败: {e}")
        return False

if __name__ == "__main__":
    migrate_dataframe()
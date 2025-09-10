import pandas as pd
import json
import os
import pickle
from datetime import datetime
from typing import Any, Dict, List, Optional
import hashlib
from bs4 import BeautifulSoup
from config import config

class DataCache:
    """数据缓存管理类"""
    
    def __init__(self, cache_dir: str = "results/cache", output_dir: str = "results"):
        self.cache_dir = cache_dir
        self.output_dir = output_dir
        self.content_dir = f"{output_dir}/content"
        self.ensure_directories()
    
    def ensure_directories(self):
        """确保缓存和输出目录存在"""
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.content_dir, exist_ok=True)
    
    def generate_cache_filename(self, url: str) -> str:
        """生成缓存文件名"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return f"{url_hash}.html"
    
    def save_html_cache(self, url: str, content: str) -> str:
        """保存HTML内容到缓存"""
        filename = self.generate_cache_filename(url)
        filepath = os.path.join(self.cache_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
    
    def load_html_cache(self, url: str) -> Optional[str]:
        """从缓存加载HTML内容"""
        filename = self.generate_cache_filename(url)
        filepath = os.path.join(self.cache_dir, filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    
    def load_html_cache_by_filename(self, filename: str) -> Optional[str]:
        """根据文件名从缓存加载HTML内容"""
        filepath = os.path.join(self.cache_dir, filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    
    def save_soup_cache(self, url: str, soup: BeautifulSoup) -> str:
        """保存BeautifulSoup对象到缓存"""
        filename = self.generate_cache_filename(url) + '.soup'
        filepath = os.path.join(self.cache_dir, filename)
        
        with open(filepath, 'wb') as f:
            pickle.dump(soup, f)
        
        return filepath
    
    def load_soup_cache(self, url: str) -> Optional[BeautifulSoup]:
        """从缓存加载BeautifulSoup对象"""
        filename = self.generate_cache_filename(url) + '.soup'
        filepath = os.path.join(self.cache_dir, filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                return pickle.load(f)
        return None
    
    def save_data(self, data: Any, filename: str) -> str:
        """保存数据到输出目录"""
        filepath = os.path.join(self.output_dir, filename)
        
        if filename.endswith('.xlsx'):
            data.to_excel(filepath, index=False)
        elif filename.endswith('.json'):
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(data))
        
        return filepath
    
    def load_data(self, filename: str) -> Any:
        """从输出目录加载数据"""
        filepath = os.path.join(self.output_dir, filename)
        
        if not os.path.exists(filepath):
            return None
        
        if filename.endswith('.xlsx'):
            return pd.read_excel(filepath)
        elif filename.endswith('.json'):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
    
    def get_articles_dataframe(self) -> pd.DataFrame:
        """获取文章数据DataFrame"""
        # 使用配置的文件前缀
        articles_filename = f"{config.output_file_prefix}_articles.xlsx"
        df = self.load_data(articles_filename)
        if df is None:
            # 创建新的DataFrame结构
            df = pd.DataFrame(columns=[
                '采集日期', '文章标题', '文章链接', '缓存路径', 
                '关键词', '订阅者ID', '新闻源', '栏目', 'HTML缓存路径'
            ])
        
        # 确保字符串列有正确的数据类型（无论是新创建还是加载的DataFrame）
        string_columns = ['采集日期', '文章标题', '文章链接', '缓存路径', 
                         '关键词', '订阅者ID', '新闻源', '栏目', 'HTML缓存路径']
        for col in string_columns:
            if col in df.columns:
                # 将NaN转换为空字符串，并确保数据类型为字符串
                df[col] = df[col].fillna('').astype(str)
        
        return df
    
    def save_articles_dataframe(self, df: pd.DataFrame):
        """保存文章数据DataFrame"""
        # 使用配置的文件前缀
        articles_filename = f"{config.output_file_prefix}_articles.xlsx"
        self.save_data(df, articles_filename)
    
    def save_matched_news(self, matched_articles: List[Dict]):
        """保存匹配的新闻到JSON文件"""
        today = datetime.now().strftime('%Y-%m-%d')
        # 使用配置的文件前缀
        filename = f'{config.output_file_prefix}_matched_news_{today}.json'
        self.save_data(matched_articles, filename)
    
    def clear_cache(self):
        """清空缓存目录"""
        for filename in os.listdir(self.cache_dir):
            filepath = os.path.join(self.cache_dir, filename)
            if os.path.isfile(filepath):
                os.unlink(filepath)
    
    def clear_output(self):
        """清空输出目录"""
        for filename in os.listdir(self.output_dir):
            filepath = os.path.join(self.output_dir, filename)
            if os.path.isfile(filepath):
                os.unlink(filepath)

# 全局实例
data_cache = DataCache()

def save_data(data: Any, filename: str) -> str:
    """保存数据的便捷函数"""
    return data_cache.save_data(data, filename)

def load_data(filename: str) -> Any:
    """加载数据的便捷函数"""
    return data_cache.load_data(filename)

def get_articles_dataframe() -> pd.DataFrame:
    """获取文章DataFrame的便捷函数"""
    return data_cache.get_articles_dataframe()

def save_articles_dataframe(df: pd.DataFrame):
    """保存文章DataFrame的便捷函数"""
    data_cache.save_articles_dataframe(df)
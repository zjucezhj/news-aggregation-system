import pandas as pd
import re
import os
from typing import List, Dict, Set
from datetime import datetime, date
from data_cache import data_cache
from bs4 import BeautifulSoup
from config import config

class KeywordFilter:
    """关键词筛选器"""
    
    def __init__(self):
        # 从配置读取匹配行为设置
        self.case_sensitive = config.case_sensitive_matching
        self.whole_word = config.keyword_match_type == 'whole_word'
    
    def filter_articles_by_keywords(self, df: pd.DataFrame, keywords: List[str], force_reprocess: bool = False) -> pd.DataFrame:
        """根据关键词筛选文章"""
        if df.empty:
            return df
        
        # 复制DataFrame避免修改原数据
        filtered_df = df.copy()
        
        # 确保关键词列存在
        if '关键词' not in filtered_df.columns:
            filtered_df['关键词'] = ''
            articles_to_process = filtered_df
        else:
            if force_reprocess:
                # 强制重新处理所有文章
                articles_to_process = filtered_df
            else:
                # 只处理关键词列为空或标记为"不匹配"的文章
                mask = filtered_df['关键词'].isna() | (filtered_df['关键词'] == '') | (filtered_df['关键词'] == '不匹配')
                articles_to_process = filtered_df[mask]
        
        if not articles_to_process.empty:
            print(f"  处理 {len(articles_to_process)} 篇文章的关键词匹配")
            # 处理需要筛选的文章
            processed_articles = self._process_articles_for_keywords(articles_to_process, keywords)
            
            # 更新原DataFrame
            for idx, row in processed_articles.iterrows():
                filtered_df.loc[idx, '关键词'] = row['关键词']
        else:
            print("  没有需要处理的文章")
        
        return filtered_df
    
    def _process_articles_for_keywords(self, df: pd.DataFrame, keywords: List[str]) -> pd.DataFrame:
        """处理文章的关键词匹配"""
        result_df = df.copy()
        
        for idx, row in df.iterrows():
            matched_keywords = self._extract_keywords_from_article(row, keywords)
            
            if matched_keywords:
                result_df.loc[idx, '关键词'] = ', '.join(matched_keywords)
            else:
                result_df.loc[idx, '关键词'] = '不匹配'
        
        return result_df
    
    def _extract_keywords_from_article(self, article_row: Dict, keywords: List[str]) -> List[str]:
        """从文章中提取匹配的关键词"""
        try:
            # 获取文章内容
            content = self._get_article_content(article_row)
            if not content:
                return []
            
            # 准备关键词匹配
            matched_keywords = []
            
            for keyword in keywords:
                if self._keyword_in_content(keyword, content):
                    matched_keywords.append(keyword)
            
            return matched_keywords
            
        except Exception as e:
            print(f"提取关键词失败: {e}")
            return []
    
    def _get_article_content(self, article_row: Dict) -> str:
        """获取文章内容"""
        try:
            # 优先从HTML缓存路径读取提取的内容
            if 'HTML缓存路径' in article_row and pd.notna(article_row['HTML缓存路径']) and article_row['HTML缓存路径']:
                html_cache_file = article_row['HTML缓存路径']
                # 尝试从content文件夹读取HTML文件
                content_path = os.path.join(data_cache.content_dir, html_cache_file)
                if os.path.exists(content_path):
                    with open(content_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    # 从HTML中提取纯文本内容
                    return self._extract_text_from_html(html_content)
                # 回退到使用data_cache.load_data（兼容性）
                else:
                    html_content = data_cache.load_data(html_cache_file)
                    if html_content:
                        # 从HTML中提取纯文本内容
                        return self._extract_text_from_html(html_content)
            
            # 如果没有HTML缓存，回退到原始HTML解析
            if '缓存路径' in article_row and pd.notna(article_row['缓存路径']) and article_row['缓存路径']:
                cache_file = article_row['缓存路径']
                original_html = data_cache.load_html_cache_by_filename(cache_file)
                if original_html:
                    return self._extract_text_from_html(original_html)
            
            # 如果有正文内容列，直接使用
            if '正文内容' in article_row and pd.notna(article_row['正文内容']) and article_row['正文内容']:
                return article_row['正文内容']
            
            # 组合标题和链接作为备选
            title = article_row.get('文章标题', '')
            return title
            
        except Exception as e:
            print(f"获取文章内容失败: {e}")
            return ""
    
    def _extract_text_from_html(self, html_content: str) -> str:
        """从HTML中提取文本"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 移除不需要的元素
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # 提取标题
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ""
            
            # 提取正文（排除标题）
            if title:
                title.decompose()
            
            # 提取主要文章内容
            article_content = soup.find('article') or soup.find('main') or soup.find('div', class_='content') or soup.body
            if article_content:
                content_text = article_content.get_text()
            else:
                content_text = soup.get_text()
            
            # 组合标题和正文，避免重复
            if title_text and title_text.lower() in content_text.lower():
                # 如果标题已经在正文中，只使用正文
                full_text = content_text
            else:
                # 否则组合标题和正文
                full_text = f"{title_text} {content_text}"
            
            # 清理文本
            full_text = re.sub(r'\s+', ' ', full_text)
            full_text = full_text.strip()
            
            return full_text
            
        except Exception as e:
            print(f"HTML文本提取失败: {e}")
            return ""
    
    def _keyword_in_content(self, keyword: str, content: str) -> bool:
        """检查关键词是否在内容中"""
        if not keyword or not content:
            return False
        
        search_content = content if self.case_sensitive else content.lower()
        search_keyword = keyword if self.case_sensitive else keyword.lower()
        
        if self.whole_word:
            # 全词匹配
            pattern = r'\b' + re.escape(search_keyword) + r'\b'
            return bool(re.search(pattern, search_content))
        else:
            # 部分匹配
            return search_keyword in search_content
    
    def get_today_articles(self, df: pd.DataFrame) -> pd.DataFrame:
        """获取今天的文章"""
        if df.empty:
            return df
        
        today = date.today().strftime('%Y-%m-%d')
        
        if '采集日期' in df.columns:
            today_articles = df[df['采集日期'] == today]
        else:
            today_articles = df
        
        return today_articles
    
    def get_matched_articles(self, df: pd.DataFrame) -> pd.DataFrame:
        """获取匹配关键词的文章"""
        if df.empty:
            return df
        
        if '关键词' in df.columns:
            # 排除不匹配和空值
            matched_df = df[
                (df['关键词'] != '不匹配') & 
                (df['关键词'].notna()) & 
                (df['关键词'] != '')
            ]
        else:
            matched_df = df
        
        return matched_df
    
    def filter_by_subscriber(self, df: pd.DataFrame, subscriber_id: str) -> pd.DataFrame:
        """根据订阅者ID筛选文章"""
        if df.empty:
            return df
        
        if '订阅者ID' in df.columns:
            subscriber_df = df[df['订阅者ID'] == subscriber_id]
        else:
            subscriber_df = df
        
        return subscriber_df
    
    def get_statistics(self, df: pd.DataFrame) -> Dict:
        """获取筛选统计信息"""
        if df.empty:
            return {
                'total_articles': 0,
                'matched_articles': 0,
                'unmatched_articles': 0,
                'today_articles': 0,
                'by_subscriber': {}
            }
        
        stats = {
            'total_articles': len(df),
            'matched_articles': 0,
            'unmatched_articles': 0,
            'today_articles': 0,
            'by_subscriber': {}
        }
        
        # 统计匹配情况
        if '关键词' in df.columns:
            stats['matched_articles'] = len(df[df['关键词'] != '不匹配'])
            stats['unmatched_articles'] = len(df[df['关键词'] == '不匹配'])
        
        # 统计今天的文章
        if '采集日期' in df.columns:
            today = date.today().strftime('%Y-%m-%d')
            stats['today_articles'] = len(df[df['采集日期'] == today])
        
        # 按订阅者统计
        if '订阅者ID' in df.columns:
            subscriber_counts = df['订阅者ID'].value_counts().to_dict()
            stats['by_subscriber'] = subscriber_counts
        
        return stats

# 全局实例
keyword_filter = KeywordFilter()

def get_keyword_filter() -> KeywordFilter:
    """获取关键词筛选器实例"""
    return keyword_filter
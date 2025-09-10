from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
from data_cache import data_cache
import requests
from bs4 import BeautifulSoup
import re

class BaseScraper(ABC):
    """基础爬取类"""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    @abstractmethod
    def get_article_list(self, url: str) -> List[Dict]:
        """获取文章列表"""
        pass
    
    @abstractmethod
    def extract_article_content(self, url: str) -> Dict:
        """提取文章内容"""
        pass
    
    def clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text
    
    def extract_title_from_html(self, html_content: str) -> str:
        """从HTML中提取标题"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 尝试多种标题提取方式
        title_selectors = [
            ['h1'],
            ['.title'],
            ['.article-title'],
            ['.post-title'],
            ['title']
        ]
        
        for selectors in title_selectors:
            for selector in selectors:
                title_element = soup.select_one(selector)
                if title_element:
                    return self.clean_text(title_element.get_text())
        
        return "未知标题"
    
    def extract_content_from_html(self, html_content: str) -> str:
        """从HTML中提取正文内容"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 调用子类重写的_extract_content方法
        return self._extract_content(soup)
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取正文内容（子类可重写此方法）"""
        # 移除不需要的元素
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # 尝试多种正文提取方式
        content_selectors = [
            '.article-content',
            '.post-content', 
            '.entry-content',
            '.content',
            'article',
            '.main-content'
        ]
        
        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                # 移除不需要的元素
                for unwanted in content_element(['script', 'style', 'ads', '.ads', '.social-share']):
                    unwanted.decompose()
                
                text = self.clean_text(content_element.get_text())
                if len(text) > 200:  # 确保内容足够长
                    return text
        
        # 如果没有找到特定选择器，提取所有段落
        paragraphs = soup.find_all('p')
        content_parts = []
        
        for p in paragraphs:
            text = p.get_text().strip()
            if text and len(text) > 30:  # 过滤太短的文本
                content_parts.append(text)
        
        if content_parts:
            return '\n\n'.join(content_parts[:10])  # 限制段落数量
        
        return ""
    
    def scrape_article(self, article_url: str, subscriber_id: str) -> Dict:
        """爬取单篇文章"""
        try:
            # 检查缓存
            cached_content = data_cache.load_html_cache(article_url)
            if cached_content:
                print(f"从缓存加载: {article_url}")
                content = cached_content
            else:
                print(f"爬取文章: {article_url}")
                response = self.session.get(article_url, timeout=30)
                response.raise_for_status()
                content = response.text
                
                # 保存到缓存
                cache_path = data_cache.save_html_cache(article_url, content)
            
            # 只提取标题，正文内容留空由提取阶段处理
            title = self.extract_title_from_html(content)
            
            # 尝试从URL中提取栏目信息
            section = self._extract_section_from_url(article_url)
            
            return {
                '采集日期': datetime.now().strftime('%Y-%m-%d'),
                '文章标题': title,
                '文章链接': article_url,
                '缓存路径': data_cache.generate_cache_filename(article_url),
                '订阅者ID': subscriber_id,
                '新闻源': self.source_name,
                '关键词': '',  # 稍后由关键词筛选模块填充
                '栏目': section,
                'HTML缓存路径': ''  # 留空由提取阶段填充
            }
            
        except Exception as e:
            print(f"爬取文章失败 {article_url}: {e}")
            return None
    
    def _extract_section_from_url(self, url: str) -> str:
        """从URL中提取栏目信息"""
        try:
            from urllib.parse import urlparse
            
            parsed = urlparse(url)
            path_parts = [part for part in parsed.path.split('/') if part]
            
            # 根据不同新闻源的URL结构提取栏目
            if self.source_name == 'CNN':
                if len(path_parts) >= 2:
                    # CNN URL格式: /section/article.html
                    section = path_parts[0].replace('-', ' ').title()
                    return section
                    
            elif self.source_name == 'Mail & Guardian':
                if len(path_parts) >= 2:
                    # MG URL格式: /section/article-title
                    section_part = path_parts[0]
                    if section_part in ['news', 'business', 'thought-leader', 'friday', 'the-green-guardian']:
                        section = section_part.replace('-', ' ').title()
                        return section
                    
            elif self.source_name == 'This Day Live':
                if len(path_parts) >= 1:
                    # ThisDay URL格式直接包含在路径中
                    section = path_parts[0].replace('-', ' ').title()
                    return section
            
            return ''
            
        except Exception as e:
            print(f"  提取栏目信息失败: {url} - {e}")
            return ''
    
    def get_domain_from_url(self, url: str) -> str:
        """从URL提取域名"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return ""
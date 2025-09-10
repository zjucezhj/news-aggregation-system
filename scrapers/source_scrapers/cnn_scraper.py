from ..base_scraper import BaseScraper
from bs4 import BeautifulSoup
from typing import List, Dict
import re
from data_cache import data_cache

class CNNScraper(BaseScraper):
    """CNN 新闻网站爬取类"""
    
    def __init__(self):
        super().__init__("CNN")
    
    def get_article_list(self, url: str) -> List[Dict]:
        """获取CNN文章列表"""
        try:
            # 尝试从缓存加载soup
            soup = data_cache.load_soup_cache(url)
            if not soup:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                # 保存soup到缓存
                data_cache.save_soup_cache(url, soup)
            
            articles = []
            seen_urls = set()
            
            # 多层次文章提取策略
            
            # 策略1：从article标签中提取
            article_elements = soup.find_all('article')
            print(f"  策略1：找到 {len(article_elements)} 个article标签")
            
            for article_elem in article_elements:
                links = article_elem.find_all('a', href=True)
                for link in links:
                    href = link['href']
                    title = link.get_text().strip()
                    
                    if self._is_valid_article_link(href, title) and href not in seen_urls:
                        if not href.startswith('http'):
                            href = self._make_absolute_url(href, url)
                        
                        articles.append({
                            'title': title,
                            'url': href,
                            'source': self.source_name
                        })
                        seen_urls.add(href)
            
            # 策略2：从容器中提取
            if len(articles) < 30:
                containers = soup.find_all(['article', 'div'], class_=re.compile(r'container|card|item|zone', re.IGNORECASE))
                print(f"  策略2：找到 {len(containers)} 个容器")
                
                for container in containers:
                    links = container.find_all('a', href=True)
                    for link in links:
                        href = link['href']
                        title = link.get_text().strip()
                        
                        if self._is_valid_article_link(href, title) and href not in seen_urls:
                            if not href.startswith('http'):
                                href = self._make_absolute_url(href, url)
                            
                            articles.append({
                                'title': title,
                                'url': href,
                                'source': self.source_name
                            })
                            seen_urls.add(href)
            
            # 策略3：搜索所有有效链接
            if len(articles) < 50:
                all_links = soup.find_all('a', href=True)
                print(f"  策略3：分析 {len(all_links)} 个链接")
                
                for link in all_links:
                    href = link['href']
                    title = link.get_text().strip()
                    
                    if (self._is_valid_article_link(href, title) and 
                        href not in seen_urls and
                        len(title) > 10):
                        
                        if not href.startswith('http'):
                            href = self._make_absolute_url(href, url)
                        
                        articles.append({
                            'title': title,
                            'url': href,
                            'source': self.source_name
                        })
                        seen_urls.add(href)
            
            # 策略4：备用搜索
            if len(articles) < 20:
                fallback_articles = self._fallback_article_search(soup, url)
                print(f"  策略4：备用搜索找到 {len(fallback_articles)} 篇文章")
                
                for article in fallback_articles:
                    if article['url'] not in seen_urls:
                        articles.append(article)
                        seen_urls.add(article['url'])
            
            print(f"  总共找到 {len(articles)} 篇不重复文章")
            return articles
            
        except Exception as e:
            print(f"获取CNN文章列表失败: {e}")
            return []
    
    def extract_article_content(self, url: str) -> Dict:
        """提取CNN文章内容"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取标题
            title = self._extract_title(soup)
            
            # 提取正文
            content = self._extract_content(soup)
            
            return {
                'title': title,
                'content': content,
                'url': url
            }
            
        except Exception as e:
            print(f"提取CNN文章内容失败: {e}")
            return {'title': '', 'content': '', 'url': url}
    
    def _is_valid_article_link(self, href: str, title: str) -> bool:
        """判断是否为有效的文章链接"""
        if not title or len(title.strip()) < 10:
            return False
        
        # CNN文章链接通常包含特定模式
        if not re.search(r'index\.html|/\d{4}/\d{2}/\d{2}/', href):
            return False
        
        # 排除非文章链接
        exclude_patterns = [
            r'video', r'gallery', r'opinion', r'live-news',
            r'weather', r'sport', r'entertainment', r'tv'
        ]
        
        for pattern in exclude_patterns:
            if re.search(pattern, href, re.IGNORECASE):
                return False
        
        return True
    
    def _make_absolute_url(self, href: str, base_url: str) -> str:
        """将相对URL转换为绝对URL"""
        if href.startswith('http'):
            return href
        
        if href.startswith('//'):
            return 'https:' + href
        
        if href.startswith('/'):
            return 'https://edition.cnn.com' + href
        
        return base_url.rstrip('/') + '/' + href.lstrip('/')
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取标题"""
        title_selectors = [
            'h1.headline__text',
            'h1.pg-headline',
            'h1.article-title',
            'h1'
        ]
        
        for selector in title_selectors:
            title_element = soup.select_one(selector)
            if title_element:
                return self.clean_text(title_element.get_text())
        
        return "未知标题"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取正文内容"""
        content_selectors = [
            '.article__content',
            '.l-container__content',
            '.article-content',
            '.content'
        ]
        
        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                # 移除不需要的元素
                for unwanted in content_element(['script', 'style', '.advertisement', '.social-share']):
                    unwanted.decompose()
                
                return self.clean_text(content_element.get_text())
        
        return ""
    
    def _fallback_article_search(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """备用文章搜索方法"""
        articles = []
        
        # 查找所有包含文章特征的链接
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link['href']
            title = link.get_text().strip()
            
            if self._is_valid_article_link(href, title):
                if not href.startswith('http'):
                    href = self._make_absolute_url(href, base_url)
                
                articles.append({
                    'title': title,
                    'url': href,
                    'source': self.source_name
                })
        
        return articles
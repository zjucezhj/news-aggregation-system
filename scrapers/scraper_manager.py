from .base_scraper import BaseScraper
from .source_scrapers.thisdaylive_scraper import ThisDayLiveScraper
from .source_scrapers.cnn_scraper import CNNScraper
from .source_scrapers.mgcoza_scraper import MGCoZaScraper
from typing import Dict, List, Optional
from urllib.parse import urlparse
from config import config

class ScraperManager:
    """爬取管理器"""
    
    def __init__(self):
        self.scrapers = {
            'thisdaylive.com': ThisDayLiveScraper(),
            'edition.cnn.com': CNNScraper(),
            'mg.co.za': MGCoZaScraper()
        }
    
    def get_scraper_by_domain(self, domain: str) -> Optional[BaseScraper]:
        """根据域名获取对应的爬取器"""
        return self.scrapers.get(domain)
    
    def get_scraper_by_url(self, url: str) -> Optional[BaseScraper]:
        """根据URL获取对应的爬取器"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # 移除www.前缀
            if domain.startswith('www.'):
                domain = domain[4:]
            
            return self.get_scraper_by_domain(domain)
        except:
            return None
    
    def get_all_scrapers(self) -> Dict[str, BaseScraper]:
        """获取所有爬取器"""
        return self.scrapers
    
    def scrape_source(self, source_url: str, subscriber_id: str) -> List[Dict]:
        """爬取指定新闻源"""
        scraper = self.get_scraper_by_url(source_url)
        if not scraper:
            print(f"未找到对应的爬取器: {source_url}")
            return []
        
        try:
            print(f"开始爬取: {source_url}")
            articles = scraper.get_article_list(source_url)
            
            # 限制每个新闻源最多处理的文章数量（从配置读取）
            max_articles = config.max_articles_per_source
            if len(articles) > max_articles:
                print(f" 文章数量过多 ({len(articles)} 篇)，限制处理前 {max_articles} 篇")
                articles = articles[:max_articles]
            
            scraped_articles = []
            for article in articles:
                article_data = scraper.scrape_article(article['url'], subscriber_id)
                if article_data:
                    scraped_articles.append(article_data)
            
            print(f"爬取完成: {source_url}, 获取 {len(scraped_articles)} 篇文章")
            return scraped_articles
            
        except Exception as e:
            print(f"爬取新闻源失败 {source_url}: {e}")
            return []

# 全局实例
scraper_manager = ScraperManager()

def get_scraper_manager() -> ScraperManager:
    """获取爬取管理器实例"""
    return scraper_manager
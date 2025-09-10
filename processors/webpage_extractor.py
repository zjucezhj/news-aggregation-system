"""
网页内容提取模块
负责从缓存的HTML文件中提取标题和正文内容
"""

import os
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from data_cache import data_cache
from scrapers.scraper_manager import scraper_manager

class WebpageExtractor:
    """网页内容提取器"""
    
    def __init__(self):
        self.scraper_manager = scraper_manager
        self.data_cache = data_cache
    
    def extract_all_articles(self) -> bool:
        """提取所有未提取内容的文章"""
        try:
            df = self.data_cache.get_articles_dataframe()
            
            # 找到需要提取的文章（没有HTML缓存路径的）
            need_extraction = df[df['HTML缓存路径'].isna() | (df['HTML缓存路径'] == '')]
            
            if need_extraction.empty:
                print(" 所有文章内容已提取完成")
                return True
            
            print(f" 开始提取 {len(need_extraction)} 篇文章的内容...")
            
            extracted_count = 0
            for index, row in need_extraction.iterrows():
                try:
                    result = self.extract_article_content(row['文章链接'], row['新闻源'])
                    if result:
                        # 更新DataFrame
                        df.at[index, 'HTML缓存路径'] = result['html_cache_path']
                        df.at[index, '栏目'] = result.get('section', '')
                        extracted_count += 1
                        
                        if extracted_count % 10 == 0:
                            print(f"  已提取 {extracted_count} 篇文章内容")
                            
                except Exception as e:
                    print(f"  提取文章内容失败: {row['文章链接']} - {e}")
                    continue
            
            # 保存更新后的DataFrame
            self.data_cache.save_articles_dataframe(df)
            print(f" 成功提取 {extracted_count} 篇文章内容")
            
            return True
            
        except Exception as e:
            print(f" 提取文章内容失败: {e}")
            return False
    
    def extract_article_content(self, url: str, source: str) -> Optional[Dict]:
        """提取单篇文章内容"""
        try:
            # 获取对应的爬取器
            scraper = self.scraper_manager.get_scraper_by_url(url)
            if not scraper:
                print(f"  未找到对应的爬取器: {url}")
                return None
            
            # 从缓存加载原始HTML内容
            original_html = self.data_cache.load_html_cache(url)
            if not original_html:
                print(f"  未找到HTML缓存: {url}")
                return None
            
            # 使用爬取器提取标题和正文内容
            title = scraper.extract_title_from_html(original_html)
            content = scraper.extract_content_from_html(original_html)
            
            if not content or len(content.strip()) < 50:
                print(f"  内容提取失败或内容过短: {url}")
                return None
            
            # 生成HTML缓存文件名
            html_cache_path = self._generate_html_cache_path(url)
            
            # 创建包含样式的HTML文档
            styled_html = self._create_styled_html(title, content, url, source)
            
            # 保存包含样式的HTML文档到content文件夹
            content_path = os.path.join(self.data_cache.content_dir, html_cache_path)
            with open(content_path, 'w', encoding='utf-8') as f:
                f.write(styled_html)
            
            # 尝试提取栏目信息
            section = self._extract_section_from_url(url, source)
            
            return {
                'html_cache_path': html_cache_path,
                'section': section,
                'content_length': len(content)
            }
            
        except Exception as e:
            print(f"  提取文章内容时出错: {url} - {e}")
            return None
    
    def _generate_html_cache_path(self, url: str) -> str:
        """生成HTML缓存文件路径"""
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return f"content_{url_hash}.html"
    
    def _create_styled_html(self, title: str, content: str, url: str, source: str) -> str:
        """创建包含样式的HTML文档"""
        from datetime import datetime
        
        # 将纯文本内容转换为HTML段落
        content_paragraphs = []
        for paragraph in content.split('\n\n'):
            if paragraph.strip():
                content_paragraphs.append(f'<p>{paragraph.strip()}</p>')
        
        html_content = '\n'.join(content_paragraphs)
        
        # 创建完整的HTML文档
        styled_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
            color: #333;
        }}
        .article-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .article-header h1 {{
            margin: 0;
            font-size: 2.2em;
            font-weight: 700;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }}
        .article-meta {{
            margin-top: 15px;
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .article-meta .source {{
            background: rgba(255, 255, 255, 0.2);
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
        }}
        .article-content {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
        }}
        .article-content p {{
            margin-bottom: 1.2em;
            text-align: justify;
            font-size: 1.1em;
            line-height: 1.8;
        }}
        .article-content p:first-of-type {{
            font-size: 1.2em;
            font-weight: 500;
            color: #2c3e50;
        }}
        .article-footer {{
            text-align: center;
            color: #666;
            font-size: 0.9em;
            padding: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }}
        .article-footer a {{
            color: #667eea;
            text-decoration: none;
        }}
        .article-footer a:hover {{
            text-decoration: underline;
        }}
        @media (max-width: 600px) {{
            body {{
                padding: 10px;
            }}
            .article-header {{
                padding: 20px;
            }}
            .article-header h1 {{
                font-size: 1.8em;
            }}
            .article-content {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="article-header">
        <h1>{title}</h1>
        <div class="article-meta">
            <span class="source">来源: {source}</span>
            <span style="margin-left: 15px;">采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
        </div>
    </div>
    
    <div class="article-content">
        {html_content}
    </div>
    
    <div class="article-footer">
        <p>原文链接: <a href="{url}" target="_blank">{url}</a></p>
        <p>此内容由新闻聚合系统自动提取和格式化</p>
    </div>
</body>
</html>"""
        
        return styled_html
    
    def _extract_section_from_url(self, url: str, source: str) -> str:
        """从URL中提取栏目信息"""
        try:
            from urllib.parse import urlparse
            
            parsed = urlparse(url)
            path_parts = [part for part in parsed.path.split('/') if part]
            
            # 根据不同新闻源的URL结构提取栏目
            if source == 'CNN':
                if len(path_parts) >= 2:
                    # CNN URL格式: /section/article.html
                    return path_parts[0].replace('-', ' ').title()
                    
            elif source == 'Mail & Guardian':
                if len(path_parts) >= 2:
                    # MG URL格式: /section/article-title
                    section_part = path_parts[0]
                    if section_part in ['news', 'business', 'thought-leader', 'friday', 'the-green-guardian']:
                        return section_part.replace('-', ' ').title()
                    
            elif source == 'This Day Live':
                if len(path_parts) >= 1:
                    # ThisDay URL格式直接包含在路径中
                    return path_parts[0].replace('-', ' ').title()
            
            return ''
            
        except Exception as e:
            print(f"  提取栏目信息失败: {url} - {e}")
            return ''
    
    def get_article_content(self, html_cache_path: str) -> Optional[str]:
        """从缓存获取文章内容"""
        try:
            content_path = os.path.join(self.data_cache.content_dir, html_cache_path)
            if os.path.exists(content_path):
                with open(content_path, 'r', encoding='utf-8') as f:
                    return f.read()
            return None
        except Exception as e:
            print(f"  读取文章内容失败: {html_cache_path} - {e}")
            return None
    
    def reextract_failed_articles(self) -> bool:
        """重新提取失败的文章"""
        try:
            df = self.data_cache.get_articles_dataframe()
            
            # 找到提取失败的文章（HTML缓存路径为空但有原始缓存路径）
            failed_articles = df[
                (df['HTML缓存路径'].isna() | (df['HTML缓存路径'] == '')) & 
                (df['缓存路径'].notna()) & 
                (df['缓存路径'] != '')
            ]
            
            if failed_articles.empty:
                print(" 没有需要重新提取的文章")
                return True
            
            print(f" 开始重新提取 {len(failed_articles)} 篇文章的内容...")
            
            extracted_count = 0
            for index, row in failed_articles.iterrows():
                try:
                    result = self.extract_article_content(row['文章链接'], row['新闻源'])
                    if result:
                        # 更新DataFrame
                        df.at[index, 'HTML缓存路径'] = result['html_cache_path']
                        df.at[index, '栏目'] = result.get('section', '')
                        extracted_count += 1
                        
                        if extracted_count % 10 == 0:
                            print(f"  已重新提取 {extracted_count} 篇文章内容")
                            
                except Exception as e:
                    print(f"  重新提取文章内容失败: {row['文章链接']} - {e}")
                    continue
            
            # 保存更新后的DataFrame
            self.data_cache.save_articles_dataframe(df)
            print(f" 成功重新提取 {extracted_count} 篇文章内容")
            
            return True
            
        except Exception as e:
            print(f" 重新提取文章内容失败: {e}")
            return False

# 全局实例
webpage_extractor = WebpageExtractor()
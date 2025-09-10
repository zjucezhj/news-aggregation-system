from typing import List, Dict
from datetime import datetime
from jinja2 import Template
from data_cache import data_cache
import os

class WebReportGenerator:
    """网页报告生成器"""
    
    def __init__(self):
        self.template = self._load_report_template()
    
    def _load_report_template(self) -> Template:
        """加载报告模板"""
        template_str = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>新闻聚合报告 - {{ date }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            background: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #7f8c8d;
            font-size: 1.2em;
        }
        
        .stats-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #3498db;
            margin-bottom: 10px;
        }
        
        .stat-label {
            color: #7f8c8d;
            font-size: 1.1em;
        }
        
        .subscribers-section {
            margin-bottom: 30px;
        }
        
        .section-title {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .section-title h2 {
            color: #2c3e50;
            font-size: 2em;
        }
        
        .subscriber-card {
            background: white;
            margin-bottom: 30px;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .subscriber-header {
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            padding: 20px;
            text-align: center;
        }
        
        .subscriber-header h3 {
            font-size: 1.5em;
            margin-bottom: 5px;
        }
        
        .subscriber-info {
            display: flex;
            justify-content: space-around;
            background: rgba(255,255,255,0.1);
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
        }
        
        .subscriber-articles {
            padding: 20px;
        }
        
        .article-item {
            border: 1px solid #ecf0f1;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            transition: all 0.3s ease;
        }
        
        .article-item:hover {
            border-color: #3498db;
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.1);
        }
        
        .article-title {
            font-size: 1.3em;
            margin-bottom: 10px;
        }
        
        .article-title a {
            color: #2c3e50;
            text-decoration: none;
            font-weight: bold;
        }
        
        .article-title a:hover {
            color: #3498db;
        }
        
        .article-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            font-size: 0.9em;
            color: #7f8c8d;
        }
        
        .keywords {
            background: #e8f4fd;
            border: 1px solid #bee5eb;
            border-radius: 20px;
            padding: 8px 15px;
            display: inline-block;
            margin: 5px;
            font-size: 0.9em;
            color: #0c5460;
        }
        
        .keywords-container {
            margin-top: 10px;
        }
        
        .no-articles {
            text-align: center;
            padding: 40px;
            color: #7f8c8d;
            font-style: italic;
        }
        
        .footer {
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin-top: 30px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .footer p {
            color: #7f8c8d;
            margin: 5px 0;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .stats-container {
                grid-template-columns: 1fr;
            }
            
            .subscriber-info {
                flex-direction: column;
                gap: 10px;
            }
            
            .article-meta {
                flex-direction: column;
                align-items: flex-start;
                gap: 5px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 新闻聚合报告</h1>
            <p>生成时间: {{ date }} | 总计: {{ total_articles }} 篇文章</p>
        </div>
        
        <div class="stats-container">
            <div class="stat-card">
                <div class="stat-number">{{ total_articles }}</div>
                <div class="stat-label">总文章数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ matched_articles }}</div>
                <div class="stat-label">匹配文章</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ total_subscribers }}</div>
                <div class="stat-label">订阅者数量</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ total_sources }}</div>
                <div class="stat-label">新闻源数量</div>
            </div>
        </div>
        
        <div class="subscribers-section">
            <div class="section-title">
                <h2>👥 订阅者新闻详情</h2>
            </div>
            
            {% for subscriber in subscribers_data %}
            <div class="subscriber-card">
                <div class="subscriber-header">
                    <h3>订阅者 {{ subscriber.id }}</h3>
                    <p>{{ subscriber.email }}</p>
                    <div class="subscriber-info">
                        <span>📰 {{ subscriber.article_count }} 篇文章</span>
                        <span>🏷️ {{ subscriber.keyword_count }} 个关键词</span>
                        <span>📡 {{ subscriber.source_count }} 个新闻源</span>
                    </div>
                </div>
                
                <div class="subscriber-articles">
                    {% if subscriber.articles %}
                        {% for article in subscriber.articles %}
                        <div class="article-item">
                            <div class="article-title">
                                <a href="{{ article.url }}" target="_blank">{{ article.title }}</a>
                            </div>
                            <div class="article-meta">
                                <span>📰 {{ article.source }}</span>
                                <span>📅 {{ article.collect_date }}</span>
                            </div>
                            <div class="keywords-container">
                                {% for keyword in article.keywords_list %}
                                <span class="keywords">{{ keyword }}</span>
                                {% endfor %}
                            </div>
                        </div>
                        {% endfor %}
                    {% else %}
                        <div class="no-articles">
                            <p>暂无匹配的新闻文章</p>
                        </div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
        
        <div class="footer">
            <p>📧 由新闻聚合系统自动生成</p>
            <p>最后更新: {{ generation_time }}</p>
        </div>
    </div>
</body>
</html>
        """
        return Template(template_str)
    
    def generate_report(self, articles_data: List[Dict]) -> str:
        """生成网页报告"""
        try:
            # 统计数据
            total_articles = len(articles_data)
            matched_articles = len([a for a in articles_data if a.get('关键词') and a.get('关键词').strip() and a.get('关键词').strip() != '不匹配'])
            
            # 按订阅者分组
            subscribers_data = self._group_by_subscriber(articles_data)
            
            # 计算统计信息
            total_subscribers = len(subscribers_data)
            total_sources = len(set(article.get('新闻源') for article in articles_data))
            
            # 准备模板数据
            template_data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'total_articles': total_articles,
                'matched_articles': matched_articles,
                'total_subscribers': total_subscribers,
                'total_sources': total_sources,
                'subscribers_data': subscribers_data,
                'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 渲染模板
            html_content = self.template.render(**template_data)
            
            # 保存到文件
            filename = f'news_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
            filepath = os.path.join(data_cache.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"网页报告已生成: {filepath}")
            
            # 生成index.html（覆盖已存在的文件）
            self._generate_index_html(template_data)
            
            return filepath
            
        except Exception as e:
            print(f"生成网页报告失败: {e}")
            return ""
    
    def _group_by_subscriber(self, articles_data: List[Dict]) -> List[Dict]:
        """按订阅者分组数据"""
        from config import config
        
        subscribers_data = []
        
        for subscriber in config.subscribers:
            subscriber_id = subscriber['id']
            subscriber_email = subscriber['email']
            
            # 筛选该订阅者的文章（处理字符串和数字类型不匹配问题）
            subscriber_articles = [
                article for article in articles_data 
                if str(article.get('订阅者ID')) == str(subscriber_id)
            ]
            
            # 处理文章数据
            processed_articles = []
            for article in subscriber_articles:
                processed_article = {
                    'title': article.get('文章标题', '未知标题'),
                    'url': article.get('文章链接', ''),
                    'source': article.get('新闻源', '未知来源'),
                    'collect_date': article.get('采集日期', ''),
                    'keywords': article.get('关键词', ''),
                    'keywords_list': self._parse_keywords(article.get('关键词', ''))
                }
                processed_articles.append(processed_article)
            
            subscriber_data = {
                'id': subscriber_id,
                'email': subscriber_email,
                'article_count': len(subscriber_articles),
                'keyword_count': len(subscriber.get('keywords', [])),
                'source_count': len(subscriber.get('NEWS_SOURCES', [])),
                'articles': processed_articles
            }
            
            subscribers_data.append(subscriber_data)
        
        return subscribers_data
    
    def _parse_keywords(self, keywords_str: str) -> List[str]:
        """解析关键词字符串"""
        if not keywords_str or keywords_str.strip() == '' or keywords_str == '不匹配':
            return []
        
        # 按逗号分割关键词
        keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
        return keywords
    
    def _generate_index_html(self, template_data: Dict) -> None:
        """生成index.html文件（覆盖已存在的文件）"""
        try:
            # 创建index.html模板
            index_template = Template("""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>新闻聚合系统 - 首页</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .hero {
            text-align: center;
            background: white;
            padding: 60px 30px;
            border-radius: 20px;
            margin-bottom: 40px;
            box-shadow: 0 15px 40px rgba(0,0,0,0.1);
        }
        
        .hero h1 {
            color: #2c3e50;
            font-size: 3em;
            margin-bottom: 20px;
            font-weight: 700;
        }
        
        .hero p {
            color: #7f8c8d;
            font-size: 1.3em;
            margin-bottom: 30px;
        }
        
        .last-update {
            background: #ecf0f1;
            padding: 15px 30px;
            border-radius: 30px;
            display: inline-block;
            color: #34495e;
            font-weight: 500;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 25px;
            margin-bottom: 50px;
        }
        
        .stat-card {
            background: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #3498db, #2980b9);
        }
        
        .stat-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        }
        
        .stat-number {
            font-size: 3em;
            font-weight: bold;
            color: #3498db;
            margin-bottom: 10px;
        }
        
        .stat-label {
            color: #7f8c8d;
            font-size: 1.1em;
            font-weight: 500;
        }
        
        .section {
            background: white;
            padding: 40px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .section h2 {
            color: #2c3e50;
            font-size: 2.2em;
            margin-bottom: 25px;
            text-align: center;
            position: relative;
        }
        
        .section h2::after {
            content: '';
            position: absolute;
            bottom: -10px;
            left: 50%;
            transform: translateX(-50%);
            width: 60px;
            height: 3px;
            background: #3498db;
        }
        
        .latest-articles {
            display: grid;
            gap: 20px;
        }
        
        .article-preview {
            border: 1px solid #ecf0f1;
            border-radius: 10px;
            padding: 20px;
            transition: all 0.3s ease;
            background: #fafafa;
        }
        
        .article-preview:hover {
            border-color: #3498db;
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.1);
            background: white;
        }
        
        .article-title {
            font-size: 1.3em;
            margin-bottom: 10px;
            color: #2c3e50;
            font-weight: 600;
        }
        
        .article-title a {
            color: inherit;
            text-decoration: none;
        }
        
        .article-title a:hover {
            color: #3498db;
        }
        
        .article-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            font-size: 0.9em;
            color: #7f8c8d;
        }
        
        .keywords {
            background: #e8f4fd;
            border: 1px solid #bee5eb;
            border-radius: 20px;
            padding: 5px 12px;
            display: inline-block;
            margin: 3px;
            font-size: 0.85em;
            color: #0c5460;
        }
        
        .quick-links {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }
        
        .quick-link-card {
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            text-decoration: none;
            transition: all 0.3s ease;
        }
        
        .quick-link-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(52, 152, 219, 0.3);
            text-decoration: none;
            color: white;
        }
        
        .quick-link-card h3 {
            margin-bottom: 10px;
            font-size: 1.3em;
        }
        
        .quick-link-card p {
            opacity: 0.9;
            font-size: 0.95em;
        }
        
        .footer {
            background: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            margin-top: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .footer p {
            color: #7f8c8d;
            margin: 8px 0;
        }
        
        .system-info {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
            text-align: left;
        }
        
        .system-info h4 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        
        .system-info ul {
            list-style: none;
            padding-left: 0;
        }
        
        .system-info li {
            padding: 5px 0;
            color: #7f8c8d;
        }
        
        .system-info li::before {
            content: "✓ ";
            color: #27ae60;
            font-weight: bold;
            margin-right: 8px;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 15px;
            }
            
            .hero {
                padding: 40px 20px;
            }
            
            .hero h1 {
                font-size: 2.5em;
            }
            
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
            }
            
            .stat-card {
                padding: 20px;
            }
            
            .stat-number {
                font-size: 2.5em;
            }
            
            .section {
                padding: 25px;
            }
            
            .quick-links {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>📰 新闻聚合系统</h1>
            <p>智能化新闻抓取、筛选与推送平台</p>
            <div class="last-update">
                最后更新: {{ generation_time }}
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{{ total_articles }}</div>
                <div class="stat-label">总文章数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ matched_articles }}</div>
                <div class="stat-label">匹配文章</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ total_subscribers }}</div>
                <div class="stat-label">订阅者数量</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ total_sources }}</div>
                <div class="stat-label">新闻源数量</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 最新匹配文章</h2>
            <div class="latest-articles">
                {% for subscriber in subscribers_data %}
                    {% for article in subscriber.articles[:3] %}
                    <div class="article-preview">
                        <div class="article-title">
                            <a href="{{ article.url }}" target="_blank">{{ article.title }}</a>
                        </div>
                        <div class="article-meta">
                            <span>📰 {{ article.source }}</span>
                            <span>👤 订阅者{{ subscriber.id }}</span>
                            <span>📅 {{ article.collect_date }}</span>
                        </div>
                        <div>
                            {% for keyword in article.keywords_list %}
                            <span class="keywords">{{ keyword }}</span>
                            {% endfor %}
                        </div>
                    </div>
                    {% endfor %}
                {% endfor %}
            </div>
        </div>
        
        <div class="section">
            <h2>🚀 快速导航</h2>
            <div class="quick-links">
                <a href="#" class="quick-link-card">
                    <h3>📈 详细报告</h3>
                    <p>查看完整的新闻聚合报告和分析</p>
                </a>
                <a href="#" class="quick-link-card">
                    <h3>📧 邮件订阅</h3>
                    <p>管理您的新闻订阅和关键词设置</p>
                </a>
                <a href="#" class="quick-link-card">
                    <h3>⚙️ 系统配置</h3>
                    <p>配置新闻源和系统参数</p>
                </a>
                <a href="#" class="quick-link-card">
                    <h3>📋 数据导出</h3>
                    <p>导出Excel格式的文章数据</p>
                </a>
            </div>
        </div>
        
        <div class="section">
            <h2>🔧 系统信息</h2>
            <div class="system-info">
                <h4>系统特性</h4>
                <ul>
                    <li>三阶段流水线处理：网页爬取 → 网页摘取 → 关键词筛选</li>
                    <li>多新闻源支持：同时抓取多个新闻网站内容</li>
                    <li>智能关键词匹配：支持全词匹配和部分匹配</li>
                    <li>个性化订阅：为每个订阅者提供定制化的新闻推送</li>
                    <li>自动邮件通知：匹配结果自动发送到订阅者邮箱</li>
                    <li>数据持久化：支持JSON和Excel多种格式导出</li>
                    <li>增量爬取：避免重复处理已抓取的内容</li>
                    <li>错误处理：完善的异常处理和日志记录</li>
                </ul>
            </div>
        </div>
        
        <div class="footer">
            <p>📧 由新闻聚合系统自动生成</p>
            <p>🚀 基于Python、Playwright、BeautifulSoup构建</p>
            <p>© 2024 新闻聚合系统. 保留所有权利.</p>
        </div>
    </div>
    
    <script>
        // 添加一些交互效果
        document.addEventListener('DOMContentLoaded', function() {
            // 为统计卡片添加动画效果
            const statCards = document.querySelectorAll('.stat-card');
            statCards.forEach((card, index) => {
                card.style.animationDelay = `${index * 0.1}s`;
                card.style.animation = 'fadeInUp 0.6s ease forwards';
            });
            
            // 为文章预览添加点击效果
            const articlePreviews = document.querySelectorAll('.article-preview');
            articlePreviews.forEach(preview => {
                preview.addEventListener('click', function(e) {
                    if (!e.target.closest('a')) {
                        const link = this.querySelector('a');
                        if (link) {
                            window.open(link.href, '_blank');
                        }
                    }
                });
            });
        });
        
        // 添加CSS动画
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
        `;
        document.head.appendChild(style);
    </script>
</body>
</html>
            """)
            
            # 确保output目录存在
            os.makedirs(data_cache.output_dir, exist_ok=True)
            
            # 生成index.html文件路径
            index_filepath = os.path.join(data_cache.output_dir, 'index.html')
            
            # 渲染并保存index.html（覆盖已存在的文件）
            index_html = index_template.render(**template_data)
            with open(index_filepath, 'w', encoding='utf-8') as f:
                f.write(index_html)
            
            print(f"index.html已生成: {index_filepath}")
            
        except Exception as e:
            print(f"生成index.html失败: {e}")

# 全局实例
web_report_generator = WebReportGenerator()

def get_web_report_generator() -> WebReportGenerator:
    """获取网页报告生成器实例"""
    return web_report_generator
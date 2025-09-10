#!/usr/bin/env python3
"""
新闻聚合系统主程序
"""

import argparse
import sys
import signal
import pandas as pd
from datetime import datetime, date
from typing import List, Dict

# 导入项目模块
from config import config
from data_cache import data_cache, get_articles_dataframe, save_articles_dataframe
from scrapers.scraper_manager import scraper_manager
from processors.keyword_filter import keyword_filter
from processors.webpage_extractor import webpage_extractor
from outputs.email_sender import email_sender
from outputs.web_report import web_report_generator

class NewsAggregator:
    """新闻聚合器主类"""
    
    def __init__(self):
        self.config = config
        self.scraper_manager = scraper_manager
        self.keyword_filter = keyword_filter
        self.email_sender = email_sender
        self.web_report_generator = web_report_generator
        self.data_cache = data_cache
        self.webpage_extractor = webpage_extractor
        self.timeout_occurred = False
    
    def run_full_pipeline(self) -> bool:
        """运行完整的新闻聚合流程（等效于依次运行--crawl-only, --extract-only, --filter-only, --report-only, --email-only）"""
        print("=" * 50)
        print(" 开始新闻聚合完整流程")
        print("=" * 50)
        
        try:
            # 1. 网页爬取
            if not self.run_crawl_only():
                print(" 网页爬取失败")
                return False
            
            # 2. 网页内容提取
            if not self.run_extract_only():
                print(" 网页内容提取失败")
                return False
            
            # 3. 关键词筛选
            if not self.run_filter_only():
                print(" 关键词筛选失败")
                return False
            
            # 4. 生成报告网页
            if not self.run_report_only():
                print(" 生成报告网页失败")
                return False
            
            # 5. 邮件推送
            if not self.run_email_only():
                print(" 邮件推送失败")
                return False
            
            print("=" * 50)
            print(" 新闻聚合完整流程完成")
            print("=" * 50)
            return True
            
        except Exception as e:
            print(f" 新闻聚合完整流程失败: {e}")
            return False
    
    def run_crawl_only(self) -> bool:
        """仅运行爬取功能"""
        print(" 开始爬取新闻...")
        
        try:
            df = self._load_or_create_dataframe()
            new_articles = self._scrape_all_sources()
            
            if new_articles:
                df = self._merge_articles(df, new_articles)
                save_articles_dataframe(df)
                print(f" 成功爬取 {len(new_articles)} 篇文章")
            else:
                print(" 没有爬取到新文章")
            
            return True
            
        except Exception as e:
            print(f" 爬取失败: {e}")
            return False
    
    def run_extract_only(self) -> bool:
        """仅运行网页内容提取"""
        print(" 开始提取网页内容...")
        
        try:
            success = self.webpage_extractor.extract_all_articles()
            if success:
                print(" 网页内容提取完成")
            else:
                print(" 网页内容提取失败")
            return success
            
        except Exception as e:
            print(f" 网页内容提取失败: {e}")
            return False
    
    def run_filter_only(self) -> bool:
        """仅运行关键词筛选"""
        print(" 开始关键词筛选...")
        
        try:
            df = self._load_or_create_dataframe()
            df = self._filter_keywords(df)
            save_articles_dataframe(df)
            print(" 关键词筛选完成")
            
            return True
            
        except Exception as e:
            print(f" 关键词筛选失败: {e}")
            return False
    
    def run_report_only(self) -> bool:
        """仅生成报告网页"""
        print(" 开始生成报告网页...")
        
        try:
            df = self._load_or_create_dataframe()
            
            # 生成报告
            self._generate_reports(df)
            print(" 报告网页生成完成")
            
            return True
            
        except Exception as e:
            print(f" 报告网页生成失败: {e}")
            return False
    
    def run_email_only(self) -> bool:
        """仅发送邮件"""
        print(" 发送邮件通知...")
        
        try:
            df = self._load_or_create_dataframe()
            self._send_emails(df)
            print(" 邮件发送完成")
            
            return True
            
        except Exception as e:
            print(f" 邮件发送失败: {e}")
            return False
    
    def send_test_email(self, email: str = None) -> bool:
        """发送测试邮件"""
        if not email:
            email = self.config.sender_email
        
        print(f"发送测试邮件到: {email}")
        
        try:
            success = self.email_sender.send_test_email(email)
            if success:
                print(" 测试邮件发送成功")
            else:
                print(" 测试邮件发送失败")
            
            return success
            
        except Exception as e:
            print(f" 测试邮件发送失败: {e}")
            return False
    
    def _load_or_create_dataframe(self) -> pd.DataFrame:
        """加载或创建DataFrame"""
        if self.config.is_full_crawl_mode():
            print(" 全量模式：创建新的DataFrame")
            # 返回空DataFrame，让爬取阶段填充数据
            empty_df = pd.DataFrame(columns=[
                '采集日期', '文章标题', '文章链接', '缓存路径', '订阅者ID', 
                '新闻源', '关键词', '栏目', 'HTML缓存路径'
            ])
            return empty_df
        else:
            print(" 增量模式：加载现有DataFrame")
            df = get_articles_dataframe()
            print(f" 当前数据库中有 {len(df)} 篇文章")
            return df
    
    def _scrape_all_sources(self) -> List[Dict]:
        """爬取所有新闻源"""
        all_articles = []
        
        # 在增量模式下，获取已存在的文章链接以避免重复处理
        existing_urls = set()
        if not self.config.is_full_crawl_mode():
            try:
                df = get_articles_dataframe()
                if not df.empty:
                    existing_urls = set(df['文章链接'].tolist())
                    print(f" 已存在 {len(existing_urls)} 篇文章，将避免重复处理")
            except Exception as e:
                print(f" 获取现有文章失败: {e}")
        
        # 获取所有唯一的新闻源
        all_sources = self.config.get_all_news_sources()
        
        for source_url in all_sources:
            print(f" 爬取: {source_url}")
            
            # 获取订阅了该新闻源的所有订阅者ID
            subscriber_ids = []
            for subscriber in self.config.subscribers:
                if source_url in subscriber.get('NEWS_SOURCES', []):
                    subscriber_ids.append(subscriber['id'])
            
            # 如果有订阅者，爬取该新闻源一次，然后为每个订阅者创建文章记录
            if subscriber_ids:
                # 使用第一个订阅者ID爬取新闻源（避免重复爬取）
                first_subscriber_id = subscriber_ids[0]
                articles = self.scraper_manager.scrape_source(source_url, first_subscriber_id)
                
                # 过滤掉已存在的文章
                new_articles = []
                for article in articles:
                    if article['文章链接'] not in existing_urls:
                        new_articles.append(article)
                        existing_urls.add(article['文章链接'])  # 添加到已存在集合，避免同一批次内重复
                
                if new_articles:
                    print(f" 获取 {len(new_articles)} 篇新文章")
                    
                    # 为每个订阅者创建文章记录
                    for article in new_articles:
                        for subscriber_id in subscriber_ids:
                            # 复制文章数据，但分配给不同的订阅者
                            article_copy = article.copy()
                            article_copy['订阅者ID'] = subscriber_id
                            all_articles.append(article_copy)
                else:
                    print(f" 没有新文章")
        
        return all_articles
    
    def _merge_articles(self, df: pd.DataFrame, new_articles: List[Dict]) -> pd.DataFrame:
        """合并新文章到DataFrame"""
        if not new_articles:
            return df
        
        # 创建新文章的DataFrame
        new_df = pd.DataFrame(new_articles)
        
        # 合并数据
        if df.empty:
            print(f" 创建新的DataFrame，包含 {len(new_df)} 篇文章")
            return new_df
        
        # 去重：基于文章链接
        original_count = len(df)
        combined_df = pd.concat([df, new_df], ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=['文章链接'], keep='last')
        
        new_count = len(combined_df)
        added_count = new_count - original_count
        
        print(f" 合并后共有 {new_count} 篇文章 (新增 {added_count} 篇)")
        return combined_df
    
    def _filter_keywords(self, df: pd.DataFrame) -> pd.DataFrame:
        """关键词筛选"""
        if df.empty:
            return df
        
        filtered_df = df.copy()
        
        # 为每个订阅者进行关键词筛选
        for subscriber in self.config.subscribers:
            subscriber_id = subscriber['id']
            keywords = subscriber.get('keywords', [])
            
            if keywords:
                print(f" 为订阅者 {subscriber_id} 筛选关键词: {keywords}")
                
                # 筛选该订阅者的文章
                subscriber_articles = filtered_df[filtered_df['订阅者ID'] == subscriber_id]
                
                if not subscriber_articles.empty:
                    # 应用关键词筛选，强制重新处理以确保新关键词被匹配
                    filtered_articles = self.keyword_filter.filter_articles_by_keywords(
                        subscriber_articles, keywords, force_reprocess=True
                    )
                    
                    # 更新原DataFrame
                    filtered_df.update(filtered_articles)
        
        return filtered_df
    
    def _generate_reports(self, df: pd.DataFrame):
        """生成报告"""
        if df.empty:
            print(" 没有数据可生成报告")
            return
        
        # 准备报告数据
        today_articles = self.keyword_filter.get_today_articles(df)
        matched_articles = self.keyword_filter.get_matched_articles(today_articles)
        
        # 转换为报告格式
        report_data = []
        for _, article in matched_articles.iterrows():
            report_data.append({
                '文章标题': article.get('文章标题', ''),
                '文章链接': article.get('文章链接', ''),
                '新闻源': article.get('新闻源', ''),
                '采集日期': article.get('采集日期', ''),
                '关键词': article.get('关键词', ''),
                '订阅者ID': article.get('订阅者ID', '')
            })
        
        # 生成JSON报告
        self.data_cache.save_matched_news(report_data)
        
        # 生成网页报告
        report_path = self.web_report_generator.generate_report(report_data)
        
        # 显示统计信息
        stats = self.keyword_filter.get_statistics(df)
        print(f" 统计信息:")
        print(f"   总文章数: {stats['total_articles']}")
        print(f"   匹配文章: {stats['matched_articles']}")
        print(f"   今日文章: {stats['today_articles']}")
    
    def _send_emails(self, df: pd.DataFrame):
        """发送邮件"""
        if df.empty:
            print(" 没有数据可发送邮件")
            return
        
        # 检查是否启用了邮件通知
        if not self.config.enable_email_notifications:
            print(" 邮件通知已禁用，跳过邮件发送")
            return
        
        # 获取今天的匹配文章
        today_articles = self.keyword_filter.get_today_articles(df)
        matched_articles = self.keyword_filter.get_matched_articles(today_articles)
        
        if matched_articles.empty:
            print(" 今天没有匹配的文章，不发送邮件")
            return
        
        # 准备邮件数据
        email_data = []
        for _, article in matched_articles.iterrows():
            email_data.append({
                'title': article.get('文章标题', ''),
                'url': article.get('文章链接', ''),
                'source': article.get('新闻源', ''),
                'collect_date': article.get('采集日期', ''),
                'keywords': article.get('关键词', ''),
                'subscriber_id': article.get('订阅者ID', '')
            })
        
        # 发送邮件
        results = self.email_sender.send_news_to_all_subscribers(email_data)
        
        # 显示结果
        success_count = sum(1 for success in results.values() if success)
        print(f" 邮件发送结果: {success_count}/{len(results)} 成功")
        
        for subscriber_id, success in results.items():
            status = " 成功" if success else " 失败"
            print(f"   订阅者 {subscriber_id}: {status}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='新闻聚合系统')
    parser.add_argument('--full', action='store_true', help='运行完整流程（爬取+提取+筛选+报告+邮件）')
    parser.add_argument('--crawl-only', action='store_true', help='仅运行网页爬取')
    parser.add_argument('--extract-only', action='store_true', help='仅运行网页内容提取')
    parser.add_argument('--filter-only', action='store_true', help='仅运行关键词筛选')
    parser.add_argument('--report-only', action='store_true', help='仅生成报告网页')
    parser.add_argument('--email-only', action='store_true', help='仅发送邮件推送')
    parser.add_argument('--test-email', metavar='EMAIL', help='发送测试邮件到指定邮箱')
    
    args = parser.parse_args()
    
    # 创建新闻聚合器
    aggregator = NewsAggregator()
    
    # 对于测试邮件，可以不需要完整配置
    if args.test_email:
        success = aggregator.send_test_email(args.test_email)
        sys.exit(0 if success else 1)
    
    # 对于其他操作，需要验证配置
    if not aggregator.config.validate_config():
        print("程序终止")
        sys.exit(1)
    
    # 执行相应操作
    if args.full:
        success = aggregator.run_full_pipeline()
    elif args.crawl_only:
        success = aggregator.run_crawl_only()
    elif args.extract_only:
        success = aggregator.run_extract_only()
    elif args.filter_only:
        success = aggregator.run_filter_only()
    elif args.report_only:
        success = aggregator.run_report_only()
    elif args.email_only:
        success = aggregator.run_email_only()
    else:
        # 默认运行完整流程
        success = aggregator.run_full_pipeline()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
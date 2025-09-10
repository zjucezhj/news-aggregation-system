import os
import json
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

class Config:
    """配置管理类"""
    
    def __init__(self):
        # SMTP 配置
        self.smtp_host = os.getenv('SMTP_HOST')
        self.smtp_port = os.getenv('SMTP_PORT')
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.smtp_use_tls = os.getenv('SMTP_USE_TLS')
        
        # 邮件配置
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.recipient_email = os.getenv('RECIPIENT_EMAIL')
        
        # 订阅者配置
        self.subscribers = self._load_subscribers()
        
        # 爬取配置
        self.crawl_mode = os.getenv('CRAWL_MODE', 'incremental')
        
        # 系统设置（可选配置）
        self.max_articles_per_source = int(os.getenv('MAX_ARTICLES_PER_SOURCE', '50'))
        self.enable_email_notifications = os.getenv('ENABLE_EMAIL_NOTIFICATIONS', 'True').lower() == 'true'
        self.content_preview_length = int(os.getenv('CONTENT_PREVIEW_LENGTH', '500'))
        self.keyword_match_type = os.getenv('KEYWORD_MATCH_TYPE', 'whole_word')
        self.case_sensitive_matching = os.getenv('CASE_SENSITIVE_MATCHING', 'False').lower() == 'true'
        self.enable_debug_mode = os.getenv('ENABLE_DEBUG_MODE', 'False').lower() == 'true'
        self.output_file_prefix = os.getenv('OUTPUT_FILE_PREFIX', 'news_aggregation')
    
    def _load_subscribers(self) -> List[Dict]:
        """加载订阅者配置"""
        subscribers_str = os.getenv('SUBSCRIBERS')
        if not subscribers_str:
            return []
        
        try:
            subscribers = json.loads(subscribers_str)
            if isinstance(subscribers, list):
                return subscribers
        except json.JSONDecodeError:
            print("错误: SUBSCRIBERS 配置格式错误，请检查JSON格式")
        
        return []
    
    def get_smtp_config(self) -> Dict:
        """获取SMTP配置"""
        return {
            'host': self.smtp_host,
            'port': self.smtp_port,
            'username': self.smtp_username,
            'password': self.smtp_password,
            'use_tls': self.smtp_use_tls,
            'sender_email': self.sender_email
        }
    
    def get_subscriber_by_id(self, subscriber_id: str) -> Dict:
        """根据ID获取订阅者信息"""
        for subscriber in self.subscribers:
            if subscriber['id'] == subscriber_id:
                return subscriber
        return None
    
    def get_all_news_sources(self) -> List[str]:
        """获取所有新闻源"""
        sources = set()
        for subscriber in self.subscribers:
            if 'NEWS_SOURCES' in subscriber:
                sources.update(subscriber['NEWS_SOURCES'])
        return list(sources)
    
    def is_full_crawl_mode(self) -> bool:
        """是否为全量爬取模式"""
        return self.crawl_mode.lower() == 'full'
    
    def validate_config(self) -> bool:
        """验证配置是否有效"""
        # 检查订阅者配置
        if not self.subscribers:
            print("错误: 未配置订阅者")
            print("请在 .env 文件中设置 SUBSCRIBERS 变量")
            print("示例格式:")
            print('SUBSCRIBERS=[{"id":"1","email":"user@example.com","keywords":["关键词1","关键词2"],"NEWS_SOURCES":["https://example.com"]}]')
            return False
        
        # 检查邮件配置（仅在有订阅者时检查）
        required_fields = ['smtp_username', 'smtp_password', 'sender_email']
        missing_fields = []
        
        for field in required_fields:
            if not getattr(self, field):
                missing_fields.append(field)
        
        if missing_fields:
            print("错误: 缺少邮件配置")
            for field in missing_fields:
                print(f"  - {field}")
            print("请在 .env 文件中设置邮件相关配置")
            return False
        
        return True

# 全局配置实例
config = Config()

def get_config() -> Config:
    """获取配置实例的便捷函数"""
    return config
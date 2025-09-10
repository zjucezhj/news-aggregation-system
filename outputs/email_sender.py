import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Optional
import json
from datetime import datetime
from config import config
from data_cache import data_cache
from jinja2 import Template

class EmailSender:
    """邮件发送器"""
    
    def __init__(self):
        self.smtp_config = config.get_smtp_config()
        self.template = self._load_email_template()
    
    def _load_email_template(self) -> Template:
        """加载邮件模板"""
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>新闻推送</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f4f4f4;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #007bff;
        }
        .header h1 {
            color: #007bff;
            margin: 0;
            font-size: 28px;
        }
        .header p {
            color: #666;
            margin: 10px 0 0 0;
            font-size: 14px;
        }
        .article {
            margin-bottom: 25px;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 8px;
            background-color: #f9f9f9;
        }
        .article h3 {
            margin: 0 0 10px 0;
            color: #333;
            font-size: 18px;
        }
        .article h3 a {
            color: #007bff;
            text-decoration: none;
        }
        .article h3 a:hover {
            text-decoration: underline;
        }
        .keywords {
            margin: 10px 0;
            padding: 8px 12px;
            background-color: #e7f3ff;
            border-radius: 4px;
            font-size: 14px;
        }
        .keywords strong {
            color: #007bff;
        }
        .source {
            color: #666;
            font-size: 14px;
            margin-top: 10px;
        }
        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
            font-size: 12px;
        }
        .stats {
            background-color: #f0f8ff;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 今日新闻推送</h1>
            <p>{{ date }} - 为您推送 {{ subscriber_id }} 的相关新闻</p>
        </div>
        
        <div class="stats">
            <strong>📊 统计信息</strong><br>
            共找到 {{ total_articles }} 篇文章，其中 {{ matched_articles }} 篇匹配您的关键词
        </div>
        
        {% for article in articles %}
        <div class="article">
            <h3><a href="{{ article.url }}" target="_blank">{{ article.title }}</a></h3>
            <div class="keywords">
                <strong>🏷️ 匹配关键词:</strong> {{ article.keywords }}
            </div>
            <div class="source">
                <strong>📰 新闻源:</strong> {{ article.source }} | 
                <strong>📅 采集日期:</strong> {{ article.collect_date }}
            </div>
        </div>
        {% endfor %}
        
        {% if not articles %}
        <div class="article">
            <h3>暂无匹配的新闻</h3>
            <p>今天没有找到与您的关键词匹配的新闻，请明天再试。</p>
        </div>
        {% endif %}
        
        <div class="footer">
            <p>📧 此邮件由新闻聚合系统自动发送</p>
            <p>如有问题，请联系: {{ sender_email }}</p>
        </div>
    </div>
</body>
</html>
        """
        return Template(template_str)
    
    def send_news_email(self, subscriber_email: str, subscriber_id: str, articles: List[Dict]) -> bool:
        """发送新闻邮件"""
        try:
            # 准备邮件内容
            subject = f"📰 今日新闻推送 - {datetime.now().strftime('%Y-%m-%d')}"
            
            # 准备模板数据
            template_data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'subscriber_id': subscriber_id,
                'total_articles': len(articles),
                'matched_articles': len([a for a in articles if a.get('keywords')]),
                'articles': articles,
                'sender_email': self.smtp_config['sender_email']
            }
            
            # 渲染HTML内容
            html_content = self.template.render(**template_data)
            
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_config['sender_email']
            msg['To'] = subscriber_email
            
            # 添加HTML内容
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 发送邮件
            return self._send_email(msg, subscriber_email)
            
        except Exception as e:
            print(f"发送新闻邮件失败: {e}")
            return False
    
    def send_test_email(self, to_email: str) -> bool:
        """发送测试邮件"""
        try:
            subject = "📧 新闻聚合系统测试邮件"
            
            html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>测试邮件</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f4f4f4;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        .success {
            color: #28a745;
            font-size: 48px;
            margin-bottom: 20px;
        }
        h1 {
            color: #007bff;
            margin-bottom: 20px;
        }
        .info {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="success">✅</div>
        <h1>新闻聚合系统测试邮件</h1>
        <p>恭喜！您的邮件配置正常工作。</p>
        <div class="info">
            <strong>发送时间:</strong> {{ datetime }}<br>
            <strong>收件人:</strong> {{ email }}<br>
            <strong>发件人:</strong> {{ sender_email }}
        </div>
        <p>如果您收到此邮件，说明邮件发送功能已配置正确。</p>
    </div>
</body>
</html>
            """
            
            template = Template(html_content)
            rendered_content = template.render(
                datetime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                email=to_email,
                sender_email=self.smtp_config['sender_email']
            )
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_config['sender_email']
            msg['To'] = to_email
            
            html_part = MIMEText(rendered_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            return self._send_email(msg, to_email)
            
        except Exception as e:
            print(f"发送测试邮件失败: {e}")
            return False
    
    def _send_email(self, msg: MIMEMultipart, to_email: str) -> bool:
        """发送邮件的底层方法"""
        try:
            # 连接SMTP服务器
            if self.smtp_config['use_tls']:
                server = smtplib.SMTP_SSL(self.smtp_config['host'], self.smtp_config['port'])
            else:
                server = smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port'])
            
            # 登录
            server.login(self.smtp_config['username'], self.smtp_config['password'])
            
            # 发送邮件
            text = msg.as_string()
            server.sendmail(self.smtp_config['sender_email'], to_email, text)
            
            # 关闭连接
            server.quit()
            
            print(f"邮件发送成功: {to_email}")
            return True
            
        except Exception as e:
            print(f"邮件发送失败: {e}")
            return False
    
    def send_news_to_all_subscribers(self, matched_articles: List[Dict]) -> Dict[str, bool]:
        """向所有订阅者发送新闻"""
        results = {}
        
        for subscriber in config.subscribers:
            subscriber_id = subscriber['id']
            subscriber_email = subscriber['email']
            
            # 筛选该订阅者的文章
            subscriber_articles = [
                article for article in matched_articles 
                if article.get('subscriber_id') == subscriber_id
            ]
            
            if subscriber_articles:
                success = self.send_news_email(subscriber_email, subscriber_id, subscriber_articles)
                results[subscriber_id] = success
            else:
                print(f"订阅者 {subscriber_id} 没有匹配的文章")
                results[subscriber_id] = True  # 没有文章也算成功
        
        return results

# 全局实例
email_sender = EmailSender()

def get_email_sender() -> EmailSender:
    """获取邮件发送器实例"""
    return email_sender
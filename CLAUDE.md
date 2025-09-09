# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个新闻聚合和推送系统，主要功能包括：
- 从多个新闻源自动抓取新闻内容
- 基于用户定义的关键词进行新闻筛选
- 向订阅者发送邮件提醒
- 生成精美的网页报告展示匹配结果

## 核心架构

### 配置系统
- **环境变量**: 从`.env`文件读取SMTP设置、订阅者信息和爬取模式
- **订阅者配置**: 每个订阅者包含ID、邮箱、关键词列表和新闻源列表
- **爬取模式**: 支持全量(full)和增量(incremental)两种模式

### 数据管理
- **数据存储**: 使用pandas DataFrame存储文章元数据
- **缓存机制**: HTML文件保存在`cache/`目录，保留原始网站格式
- **持久化**: 使用`data_cache.py`中的`save_data`和`load_data`函数
- **输出格式**: JSON格式的匹配结果和Excel格式的数据文件

### 模块设计
1. **配置读取模块**: 从.env文件读取系统设置
2. **网页爬取模块**: 
   - 使用Playwright实现新闻网站爬取
   - 使用BeautifulSoup提取标题和正文
   - 为每个新闻源创建专门的爬取类
3. **关键词筛选模块**: 
   - 解析HTML内容，匹配用户关键词
   - 支持跳过已处理的文章
   - 按日期和关键词匹配度筛选
4. **网页展示模块**: 生成统一的HTML报告样式
5. **邮件提醒模块**: SMTP自动发送匹配内容

## 目录结构

```
news/
├── .env                    # 环境变量配置
├── .env.sample            # 环境变量模板
├── .gitignore             # Git忽略文件
├── data_cache.py          # 数据缓存工具函数
├── requirements.txt       # Python依赖包
├── main.py               # 主程序入口
├── config.py             # 配置管理
├── scrapers/             # 网站爬取模块
│   ├── __init__.py
│   ├── base_scraper.py   # 基础爬取类
│   └── source_scrapers/  # 各新闻源专用爬取类
├── processors/           # 数据处理模块
│   ├── __init__.py
│   ├── keyword_filter.py # 关键词筛选
│   └── content_parser.py # 内容解析
├── outputs/              # 输出模块
│   ├── __init__.py
│   ├── web_report.py     # 网页报告生成
│   └── email_sender.py   # 邮件发送
├── cache/                # HTML缓存目录
└── output/               # 结果输出目录
    ├── matched_news.json # 匹配的新闻JSON
    └── articles_data.xlsx # 文章数据Excel
```

## 开发命令

### 环境设置
```bash
# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/MacOS:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install
```

### 运行系统
```bash
# 运行完整新闻聚合流程
python main.py

# 仅运行新闻爬取
python main.py --crawl-only

# 仅运行关键词筛选
python main.py --filter-only

# 仅发送邮件通知
python main.py --email-only
```

### 测试命令
```bash
# 测试单个新闻源爬取
python -m scrapers.test_source thisdaylive

# 测试关键词筛选
python -m processors.test_keyword_filter

# 测试邮件发送
python -m outputs.test_email
```

## 数据流程

### 爬取阶段
1. 读取配置中的新闻源列表
2. 为每个新闻源创建专用爬取类
3. 爬取文章列表(采集日期、标题、链接)
4. 提取正文内容，保存HTML到cache目录
5. 记录元数据到DataFrame

### 筛选阶段
1. 从cache目录读取HTML文件
2. 解析标题和正文内容
3. 匹配用户关键词列表
4. 更新DataFrame的关键词列
5. 筛选当天匹配的文章

### 输出阶段
1. 生成JSON格式的匹配结果
2. 保存DataFrame到Excel文件
3. 生成HTML网页报告
4. 发送邮件通知

## 关键技术点

### 爬取策略
- 使用Playwright处理动态加载内容
- 保留原始HTML格式便于后续分析
- 实现增量爬取避免重复处理

### 关键词匹配
- 支持多关键词同时匹配
- 智能跳过已处理文章
- 记录匹配到的具体关键词

### 多订阅者支持
- 统一的处理逻辑
- 订阅者特定的关键词和新闻源
- 统一的网页报告样式

### 数据持久化
- DataFrame作为主要数据结构
- Excel文件便于人工查看和编辑
- JSON格式用于程序间数据交换

## 配置说明

### 环境变量
- `SMTP_*`: 邮件服务器配置
- `SUBSCRIBERS`: 订阅者信息JSON数组
- `CRAWL_MODE`: 爬取模式(full/incremental)

### 订阅者格式
```json
{
  "id": "1",
  "email": "user@example.com", 
  "keywords": ["关键词1", "关键词2"],
  "NEWS_SOURCES": ["https://source1.com", "https://source2.com"]
}
```

## 注意事项

- 确保网络连接稳定，某些新闻源可能有访问限制
- 定期清理cache目录避免占用过多磁盘空间
- 邮件发送功能需要正确配置SMTP服务器
- 增量模式适合日常使用，全量模式适合首次运行或数据重置
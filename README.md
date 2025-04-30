# 财经新闻分析邮件系统

一个基于Python的自动化财经新闻分析工具，能够获取最新的财经新闻，使用大语言模型进行分析，并以邮件形式发送分析报告。
**本程序百分之90%的代码都是由Cursor生成的，不能保证程序的可靠性，仅供学习与参考**

## 功能特点

* 自动从新浪财经获取最新的财经新闻
* 使用大语言模型(目前支持Deepseek)分析新闻的市场影响
* 对新闻进行评分(市场影响力、政策相关性、时效紧迫性)
* 生成市场总结和投资建议
* 以HTML格式的邮件发送分析报告
* 支持自定义邮件模板和提示词模板
* 完整的日志记录系统

## 系统架构

```
src/
├── main.py                 # 主程序
├── config.py               # 配置类定义
├── llm_providers/          # LLM提供商接口
│   ├── __init__.py         # 提供商初始化
│   ├── base.py             # 基础LLM提供商类
│   └── deepseek.py         # Deepseek实现
├── templates/              # 模板管理
│   ├── __init__.py         # 模板管理器
│   ├── emails/             # 邮件模板
│   │   └── default.yaml    # 默认邮件模板
│   └── prompts/            # 提示词模板
│       └── default.yaml    # 默认提示词模板
├── .env                    # 环境变量文件(需自行创建)
└── financial_news.log      # 日志文件(运行时生成)
```

## 核心组件

* **FinancialNewsAnalyzer**: 主要分析器类，负责获取新闻、分析和发送邮件
* **AppConfig**: 管理应用配置，包括LLM、邮件和新闻设置
* **TemplateManager**: 管理邮件和提示词模板
* **LLM提供商**: 封装了与大语言模型API的交互

## 安装步骤

1. **克隆仓库(如适用)**:
   ```bash
   git clone <仓库地址>
   cd <项目目录>
   ```

2. **安装依赖**:
   ```bash
   pip install requests python-dotenv pyyaml
   ```

3. **创建环境变量文件**:
   在项目根目录创建`.env`文件，包含以下内容:

   ```
   # LLM API配置
   DEEPSEEK_API_KEY=your_deepseek_api_key
   
   # 邮件配置
   EMAIL_USER=your_email@example.com
   EMAIL_PASSWORD=your_email_password
   RECIPIENT_EMAIL=recipient@example.com
   
   # 可选: SMTP配置(默认为163邮箱)
   # SMTP_SERVER=smtp.163.com
   # SMTP_PORT=25
   
   # 可选: 日志配置
   # LOG_LEVEL=INFO
   # LOG_FILE=financial_news.log
   ```

## 使用方法

1. **确保环境变量已正确配置**

2. **运行主程序**:
   ```bash
   python main.py
   ```

3. **执行流程**:
   * 程序将从新浪财经获取最新的财经新闻
   * 使用配置的LLM(默认为Deepseek)分析新闻
   * 根据邮件模板生成HTML格式的分析报告
   * 将报告发送到配置的收件人邮箱
   * 分析结果会保存在`analysis_result.json`文件中

## 配置说明

### LLM配置 (LLMConfig)
* `provider`: LLM提供商，目前支持"deepseek"
* `model`: 模型名称，默认为"deepseek-chat"
* `temperature`: 温度参数，控制生成的随机性
* `max_tokens`: 最大令牌数

### 邮件配置 (EmailConfig)
* `smtp_server`: SMTP服务器地址
* `smtp_port`: SMTP服务器端口
* `sender_email`: 发件人邮箱
* `sender_password`: 发件人邮箱密码或授权码
* `recipient_email`: 收件人邮箱

### 新闻配置 (NewsConfig)
* `news_count`: 获取的新闻数量
* `news_source`: 新闻来源，目前支持"sina"
* `news_categories`: 新闻类别列表

## 自定义模板

### 提示词模板
提示词模板(`templates/prompts/default.yaml`)定义了发送给LLM的提示词结构，包含:
* `system_prompt`: 系统提示
* `analysis_steps`: 分析步骤
* `output_format`: 输出格式

### 邮件模板
邮件模板(`templates/emails/default.yaml`)定义了邮件的HTML结构和样式，包含:
* `subject`: 邮件主题
* `styles`: CSS样式
* `sections`: 邮件各部分的内容模板

## 日志系统

程序使用Python的logging模块记录运行信息，日志同时输出到控制台和日志文件。
可通过环境变量`LOG_LEVEL`和`LOG_FILE`配置日志级别和文件路径。 
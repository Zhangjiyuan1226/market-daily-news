from dataclasses import dataclass
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

@dataclass
class LLMConfig:
    """LLM配置"""
    provider: str = "deepseek"  # deepseek 或 openai
    model: str = "deepseek-chat"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 12000
    
    def __post_init__(self):
        """初始化后处理"""
        # 从环境变量获取API密钥
        if not self.api_key:
            if self.provider == "deepseek":
                self.api_key = os.getenv("DEEPSEEK_API_KEY")
            elif self.provider == "openai":
                self.api_key = os.getenv("OPENAI_API_KEY")
        
        # 设置默认API基础URL
        if not self.api_base:
            if self.provider == "deepseek":
                # 尝试从环境变量获取API基础URL
                api_base_env = os.getenv("DEEPSEEK_API_BASE")
                if api_base_env:
                    self.api_base = api_base_env
                else:
                    # 默认使用官方API
                    self.api_base = "https://api.deepseek.com/v1"
            elif self.provider == "openai":
                self.api_base = os.getenv("OPENAI_API_BASE") or "https://api.openai.com/v1"

@dataclass
class EmailConfig:
    """邮件配置"""
    smtp_server: str = "smtp.163.com"
    smtp_port: int = 25
    sender_email: Optional[str] = None
    sender_password: Optional[str] = None
    recipient_email: Optional[str] = None
    
    def __post_init__(self):
        """初始化后处理"""
        # 从环境变量获取邮件配置
        if not self.sender_email:
            self.sender_email = os.getenv("EMAIL_USER")
        if not self.sender_password:
            self.sender_password = os.getenv("EMAIL_PASSWORD")
        if not self.recipient_email:
            self.recipient_email = os.getenv("RECIPIENT_EMAIL")

@dataclass
class NewsConfig:
    """新闻配置"""
    news_count: int = 5
    news_source: str = "sina"
    news_categories: list = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.news_categories is None:
            self.news_categories = ["finance", "stock", "economy"]

@dataclass
class AppConfig:
    """应用配置"""
    llm: LLMConfig = None
    email: EmailConfig = None
    news: NewsConfig = None
    log_level: str = "INFO"
    log_file: str = "financial_news.log"
    
    def __post_init__(self):
        """初始化后处理"""
        if self.llm is None:
            self.llm = LLMConfig()
        if self.email is None:
            self.email = EmailConfig()
        if self.news is None:
            self.news = NewsConfig()
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'AppConfig':
        """从字典创建配置"""
        llm_config = LLMConfig(**config_dict.get("llm", {}))
        email_config = EmailConfig(**config_dict.get("email", {}))
        news_config = NewsConfig(**config_dict.get("news", {}))
        
        return cls(
            llm=llm_config,
            email=email_config,
            news=news_config,
            log_level=config_dict.get("log_level", "INFO"),
            log_file=config_dict.get("log_file", "financial_news.log")
        ) 
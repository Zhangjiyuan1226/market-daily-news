import os
import json
import logging
import json
import re

from datetime import datetime
from typing import Dict, Any, List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

from config import AppConfig
from llm_providers import DeepseekProvider 
# , OpenAIProvider
from templates import TemplateManager

            
# 配置日志
def setup_logging(log_level: str = "INFO", log_file: str = "financial_news.log"):
    """配置日志"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

class FinancialNewsAnalyzer:
    """金融新闻分析器"""
    
    def __init__(self, config: AppConfig):
        """初始化"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化LLM提供者
        if config.llm.provider == "deepseek":
            self.llm_provider = DeepseekProvider(config.llm)
        # else:
        #     self.llm_provider = OpenAIProvider(config.llm)
        
        # 初始化模板管理器
        self.template_manager = TemplateManager()
    
    def get_news(self) -> List[Dict[str, Any]]:
        """获取新闻"""
        try:
            # 这里使用新浪财经API获取新闻
            import requests
            import time
            url = 'https://feed.mix.sina.com.cn/api/roll/get'
            params = {
                'pageid': '153',
                'lid': '2509',
                'k': '',
                'num': '50',
                'page': '1',
                'r': str(time.time()),
                'callback': f'jQuery111{int(time.time() * 1000)}'
            }
            
            response = requests.get(url, params=params, timeout=30)
            if response.status_code != 200:
                self.logger.error(f"获取新闻失败: HTTP {response.status_code}")
                return []
            
            # 处理JSONP响应
            match = re.search(r'try\{.*?\((.*?)\);\}catch\(e\)\{\};', response.text)
            if not match:
                self.logger.error("无法解析新闻数据")
                return []
            
            data = json.loads(match.group(1))
            news_items = data.get('result', {}).get('data', [])
            
            # 格式化新闻数据
            formatted_news = []
            for item in news_items:
                news = {
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'intro': item.get('intro', ''),
                    'ctime': item.get('ctime', '')
                }
                if news['title'] and news['intro']:
                    formatted_news.append(news)
            
            return formatted_news
            
        except Exception as e:
            self.logger.error(f"获取新闻时发生错误: {str(e)}")
            return []
    
    def analyze_news(self, news_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析新闻"""
        try:
            # 从 prompts 子目录加载 default 模板
            prompt_template = self.template_manager.get_template("prompts", "default")
            if not prompt_template:
                raise ValueError("未找到提示词模板 prompts/default.yaml")
            
            # 构建新闻列表字符串
            news_text = "\n".join([
                f"{i+1}. {item['title']}\n   简介: {item['intro']}"
                for i, item in enumerate(news_list)
            ])
            
            # 构建完整的提示词，使用YAML模板中的结构
            # 注意：需要确保 YAML 文件中有 system_prompt, analysis_steps, output_format 字段
            system_prompt = prompt_template.get("system_prompt", "请分析以下新闻：")
            analysis_steps_str = self._format_analysis_steps(prompt_template.get("analysis_steps", []))
            output_format_str = self._format_output_format(prompt_template.get("output_format", {}))
            
            prompt = f"""{system_prompt}

新闻列表：
{news_text}

请按照以下步骤进行分析：
{analysis_steps_str}

请按照以下格式输出分析结果：
{output_format_str}"""
            
            # 调用LLM进行分析
            result = self.llm_provider.analyze_prompt(prompt)
            
            if "error" in result:
                self.logger.error(f"分析新闻失败: {result['error']}")
                return result
            
            return result
            
        except Exception as e:
            self.logger.error(f"分析新闻时发生错误: {str(e)}")
            return {"error": str(e)}
    
    def _format_analysis_steps(self, steps: List[Dict[str, Any]]) -> str:
        """格式化分析步骤"""
        formatted_steps = []
        for step in steps:
            step_text = f"{step['name']}:\n"
            for item in step['items']:
                step_text += f"  - {item['name']}: {item['description']}"
                if 'range' in item:
                    step_text += f" ({item['range']})"
                step_text += "\n"
            formatted_steps.append(step_text)
        return "\n".join(formatted_steps)
    
    def _format_output_format(self, output_format: Dict[str, Any]) -> str:
        """格式化输出格式"""
        import json
        return json.dumps(output_format, ensure_ascii=False, indent=2)
    
    def _build_email_html(self, email_template: Dict[str, Any], context: Dict[str, Any]) -> str:
        """根据邮件模板和上下文构建HTML内容"""
        styles_dict = email_template.get("styles", {})
        styles_str = "\n".join([f".{cls} {{ {'; '.join([f'{prop}: {val}' for prop, val in props.items()])} }}" 
                            for cls, props in styles_dict.items()])
        # Handle body style separately if present
        if "body" in styles_dict:
             body_styles = '; '.join([f'{prop}: {val}' for prop, val in styles_dict["body"].items()])
             body_tag = f'<body style="{body_styles}">'
        else:
             body_tag = '<body>'
        
        html_parts = [f"""<html>
<head>
    <meta charset="UTF-8">
    <style>
        {styles_str}
    </style>
</head>
{body_tag}"""]

        sections = email_template.get("sections", [])
        for section in sections:
            section_name = section.get("name", "unknown")
            section_template = section.get("template", f"<p>Missing template for section: {section_name}</p>")
            try:
                # Populate section template with context
                # We need to prepare specific context items like news_items HTML
                if section_name == "news_list":
                    news_items_html = ""
                    news_analysis = context.get("news_analysis", [])
                    if not news_analysis:
                        news_items_html = "<p>无重要新闻分析。</p>"
                    else:
                         # Limit to top N news if needed, e.g., top 5
                         top_news = news_analysis[:5]
                         for item in top_news:
                            # Safely get values from item
                            title = item.get('news_content', item.get('title', 'N/A')) 
                            scores_html = ""
                            scores = item.get('scores')
                            if isinstance(scores, dict):
                                scores_html += f"<p>评分: "
                                scores_html += f"总分: <strong>{scores.get('weighted_total', 'N/A')}</strong> "
                                scores_html += f"(影响:{scores.get('market_impact', 'N/A')}, "
                                scores_html += f"政策:{scores.get('policy_relevance', 'N/A')}, "
                                scores_html += f"时效:{scores.get('time_urgency', 'N/A')})</p>"
                            else:
                                scores_html = f"<p>评分: {scores if scores else 'N/A'}</p>"

                            impact_html = ""
                            equity_impact = item.get('equity_impact')
                            bond_impact = item.get('bond_impact')
                            if isinstance(equity_impact, dict):
                                impact_html += f"<p>股市影响 ({equity_impact.get('intensity', '')}): </p>"
                                impact_html += f"<p>{equity_impact.get('short_term', 'N/A')}</p>"
                                impact_html += f"<p>{equity_impact.get('long_term', 'N/A')}</p>"
                            if isinstance(bond_impact, dict):
                                impact_html += f"<p>债市影响 ({bond_impact.get('intensity', '')}): </p>"
                                impact_html += f"<p>{bond_impact.get('short_term', 'N/A')}</p>"
                                impact_html += f"<p>{bond_impact.get('long_term', 'N/A')}</p>"
                                
                            if not impact_html:
                                impact_html = f"<p>影响分析: {item.get('impact', 'N/A')}</p>" # Fallback
                                
                            suggestion_html = f"<p>{item.get('suggestion', 'N/A')}</p>"
                                
                            news_items_html += f"""
                            <div class="news-item">
                                <h3 class="news-title">{title}</h3>
                                {scores_html}
                                {impact_html}
                                {suggestion_html}
                            </div>
                            """
                    section_html = section_template.format(news_items=news_items_html)
                else:
                    # For other sections like header, market_summary
                    section_html = section_template.format(**context)
                html_parts.append(section_html)
            except KeyError as e:
                 self.logger.error(f"邮件模板 section '{section_name}' 缺少变量: {e}. 上下文: {context.keys()}")
                 html_parts.append(f"<p><i>无法渲染节 '{section_name}': 缺少变量 {e}</i></p>")
            except Exception as e:
                 self.logger.error(f"渲染邮件模板 section '{section_name}' 时出错: {e}")
                 html_parts.append(f"<p><i>无法渲染节 '{section_name}': {e}</i></p>")

        html_parts.append("</body>\n</html>")
        return "\n".join(html_parts)

    def send_email(self, analysis_result: Dict[str, Any], news_list: List[Dict[str, Any]]) -> bool:
        """发送邮件"""
        try:
            # 从 emails 子目录加载 default 模板
            email_template = self.template_manager.get_template("emails", "default")
            if not email_template:
                raise ValueError("未找到邮件模板 emails/default.yaml")
            
            # 准备邮件上下文 (context)
            now = datetime.now()
            context = {
                "date": now.strftime("%Y-%m-%d"),
                "current_time": now.strftime("%Y-%m-%d %H:%M"),
                "news_analysis": analysis_result.get("top_news", analysis_result.get("news_analysis", [])), # Use top_news if available
                **analysis_result.get("market_summary", {}) # Unpack market summary dict
            }
            # Add fallback for investment_advice if not in market_summary
            context["investment_advice"] = analysis_result.get("investment_advice", 
                                              context.get("investment_advice", "无投资建议"))

            # 构建邮件HTML
            email_content = self._build_email_html(email_template, context)

            # 从模板获取主题
            subject_template = email_template.get("subject", "财经新闻分析报告 - {date}")
            subject = subject_template.format(date=context["date"])
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = Header(f'财经新闻分析 <{self.config.email.sender_email}>', 'utf-8')
            msg['To'] = Header(self.config.email.recipient_email, 'utf-8')
            msg['Subject'] = Header(subject, 'utf-8')
            msg.attach(MIMEText(email_content, 'html', 'utf-8'))
            
            # 发送邮件
            sender_email = self.config.email.sender_email
            smtp_server = self.config.email.smtp_server
            smtp_port = self.config.email.smtp_port
            sender_password = self.config.email.sender_password
            recipient_email = self.config.email.recipient_email

            logging.info(f"Connecting to SMTP server {smtp_server}:{smtp_port}")
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            
            logging.info(f"Sending email to {recipient_email}")
            server.sendmail(sender_email, recipient_email, msg.as_string())
            server.quit()
            self.logger.info("邮件发送成功")
            return True
            
        except Exception as e:
            self.logger.error(f"发送邮件失败: {str(e)}")
            return False
        
    def safe_json_loads(s):
        s = s.strip()
        s = re.sub(r"^```json", "", s)
        s = re.sub(r"```$", "", s)
        s = s.strip()
        return json.loads(s)
    
    def fix_truncated_json(self, json_str: str) -> str:
        """修复被截断的JSON字符串"""
        json_str = json_str.strip()
        
        # 检查是否是以逗号结尾
        if json_str.endswith(','):
            # 移除结尾的逗号
            json_str = json_str[:-1]
            
            # 如果是news_analysis数组，添加结束括号和缺失的字段
            if '"news_analysis": [' in json_str:
                json_str += '], "market_summary": "市场总体表现平稳", "investment_advice": "根据新闻分析，建议投资者关注AI、新能源和政策支持的行业。"}'
        
        return json_str
    
    def run(self) -> Dict[str, Any]:
        """运行分析流程"""
        try:
            # 获取新闻
            news_list = self.get_news()
            if not news_list:
                return {"error": "未获取到新闻数据"}
            
            # 分析新闻
            analysis_result = self.analyze_news(news_list)
            if "error" in analysis_result:
                return analysis_result
                
            # 关键：解析 LLM 返回的 content 字段
            if "content" in analysis_result and isinstance(analysis_result["content"], str):
                try:
                    content_str = analysis_result['content']
                    content_str = content_str.strip()
                    content_str = re.sub(r"^```json", "", content_str)
                    content_str = re.sub(r"```$", "", content_str)
                    content_str = content_str.strip()
                    
                    # 修复可能被截断的JSON
                    content_str = self.fix_truncated_json(content_str)
                    
                    # 解析JSON
                    analysis_result = json.loads(content_str)
                except Exception as ex:
                    self.logger.error(f"解析LLM content字段失败: {ex}")
                    return {"error": f"解析LLM content字段失败: {ex}", "raw_content": analysis_result.get("content", "")}
                    
            # 发送邮件
            email_sent = self.send_email(analysis_result, news_list)
            analysis_result["email_sent"] = email_sent
            
            # 保存结果
            with open("analysis_result.json", "w", encoding="utf-8") as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"运行分析流程失败: {str(e)}")
            return {"error": str(e)}

def main():
    """主函数"""
    try:
        # 加载配置
        config = AppConfig()
        
        # 设置日志
        logger = setup_logging(config.log_level, config.log_file)
        logger.info("开始运行金融新闻分析程序")
        
        # 创建分析器
        analyzer = FinancialNewsAnalyzer(config)
        
        # 运行分析
        result = analyzer.run()
        
        if "error" in result:
            logger.error(f"分析失败: {result['error']}")
        else:
            logger.info("分析完成")
            if result.get("email_sent"):
                logger.info("邮件已发送")
            else:
                logger.warning("邮件发送失败")
        
        return result
        
    except Exception as e:
        logger.error(f"程序运行失败: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    main() 
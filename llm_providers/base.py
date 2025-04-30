from abc import ABC, abstractmethod
from typing import Dict, Any
import logging
import json
import requests
from config import LLMConfig

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """LLM提供者基类"""
    
    def __init__(self, config: LLMConfig):
        """初始化"""
        self.config = config
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}"
        }
    
    @abstractmethod
    def analyze_prompt(self, prompt: str) -> Dict[str, Any]:
        """分析提示词"""
        pass
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """处理API响应"""
        try:
            response.raise_for_status()
            result = response.json()
            
            # 记录响应信息
            logger.debug(f"API响应状态码: {response.status_code}")
            logger.debug(f"API响应头: {dict(response.headers)}")
            logger.debug(f"API响应内容: {result}")
            
            # 检查响应格式
            if not isinstance(result, dict):
                logger.error(f"API响应格式错误: {result}")
                return {"error": "API响应格式错误"}
            
            # 提取内容
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0].get("message", {}).get("content", "")
                try:
                    # 尝试解析JSON
                    return json.loads(content)
                except json.JSONDecodeError:
                    # 如果不是JSON，返回原始内容
                    return {"content": content}
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {str(e)}")
            return {"error": f"API请求失败: {str(e)}"}
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}")
            return {"error": f"JSON解析失败: {str(e)}"}
        except Exception as e:
            logger.error(f"处理响应时发生错误: {str(e)}")
            return {"error": f"处理响应时发生错误: {str(e)}"} 
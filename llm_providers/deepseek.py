import json
import logging
import requests
import time
from typing import Dict, Any, List
from .base import LLMProvider
from config import LLMConfig

logger = logging.getLogger(__name__)

class DeepseekProvider(LLMProvider):
    """Deepseek API提供者"""

    # 定义备用API基础URL列表
    BACKUP_API_BASES = [
        "https://api.deepseek.com/v1",  # 官方API (优先)
        "https://api.deerapi.com/v1"    # 第三方API服务 (备用)
    ]

    def __init__(self, config: LLMConfig):
        """初始化"""
        super().__init__(config)
        # 设置API基础URL列表，用户配置的优先，然后是备用列表
        if config.api_base:
            self.api_bases = [config.api_base] + [b for b in self.BACKUP_API_BASES if b != config.api_base]
        else:
            self.api_bases = self.BACKUP_API_BASES.copy()
        logger.info(f"DeepseekProvider初始化，将尝试以下API基础URL: {self.api_bases}")

    def analyze_prompt(self, prompt: str, max_retries_per_url: int = 2, retry_delay: int = 5) -> Dict[str, Any]:
        """分析提示词，支持自动切换API基础URL和重试"""
        errors = []

        for api_base in self.api_bases:
            logger.info(f"尝试使用API基础URL: {api_base}")
            for attempt in range(1, max_retries_per_url + 1):
                try:
                    data = {
                        "model": self.config.model,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens,
                        "stream": False
                    }

                    logger.info(f"发送请求到Deepseek API ({api_base}), 尝试 {attempt}/{max_retries_per_url}")
                    response = requests.post(
                        f"{api_base}/chat/completions",
                        headers=self.headers,
                        json=data,
                        timeout=60
                    )

                    if response.status_code >= 500 and attempt < max_retries_per_url:
                        logger.warning(f"收到服务器错误 {response.status_code} (API: {api_base})，等待 {retry_delay} 秒后重试...")
                        time.sleep(retry_delay)
                        continue

                    response.raise_for_status()
                    logger.info(f"成功从 {api_base} 获取响应")
                    # 使用基类的 _handle_response 处理响应
                    return self._handle_response(response)

                except requests.exceptions.HTTPError as e:
                    error_msg = f"HTTP错误: {e} (API: {api_base}, 尝试: {attempt}/{max_retries_per_url})"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    # Check if response object exists before accessing status_code
                    status_code = e.response.status_code if e.response is not None else None
                    if status_code is not None:
                        if 400 <= status_code < 500:
                             logger.warning(f"收到客户端错误 {status_code} (API: {api_base})，将尝试下一个API URL (如果可用)")
                             break # Try next api_base
                        if status_code >= 500 and attempt == max_retries_per_url:
                            logger.error(f"达到最大重试次数 ({max_retries_per_url})，服务器错误依旧 (API: {api_base})")
                            break # Try next api_base
                    else: # If no response object (e.g., connection error before response)
                         break # Try next api_base
                except requests.exceptions.Timeout as e:
                    error_msg = f"请求超时: {e} (API: {api_base}, 尝试: {attempt}/{max_retries_per_url})"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    if attempt < max_retries_per_url:
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"达到最大重试次数 ({max_retries_per_url})，请求依旧超时 (API: {api_base})")
                        break
                except requests.exceptions.RequestException as e:
                    error_msg = f"请求异常: {e} (API: {api_base}, 尝试: {attempt}/{max_retries_per_url})"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    break
                except Exception as e:
                    error_msg = f"处理请求时发生未知错误: {e} (API: {api_base}, 尝试: {attempt}/{max_retries_per_url})"
                    logger.error(error_msg, exc_info=True)
                    errors.append(error_msg)
                    break

        combined_errors = "; ".join(errors)
        logger.error(f"所有Deepseek API访问尝试均失败: {combined_errors}")
        return {
            "error": f"无法连接到Deepseek API服务。详细错误: {combined_errors}"
        } 
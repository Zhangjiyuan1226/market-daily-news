import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class TemplateManager:
    """模板管理器"""
    
    def __init__(self, base_dir: str = "templates"):
        """初始化，从子目录加载模板"""
        self.base_dir = Path(base_dir)
        self.prompts_dir = self.base_dir / "prompts"
        self.emails_dir = self.base_dir / "emails"
        self.templates: Dict[str, Dict[str, Any]] = {
            "prompts": {},
            "emails": {}
        }
        self._load_all_templates()
    
    def _load_templates_from_dir(self, directory: Path, template_type: str):
        """从指定目录加载模板"""
        try:
            if not directory.is_dir():
                logger.warning(f"模板目录 {directory} 不存在或不是一个目录，跳过加载 {template_type} 模板。")
                directory.mkdir(parents=True, exist_ok=True) # Ensure dir exists
                return

            for file in directory.glob("*.yaml"):
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        template_data = yaml.safe_load(f)
                        if template_data:
                            # 使用文件名（不含扩展名）作为模板名称
                            template_name = file.stem
                            self.templates[template_type][template_name] = template_data
                            logger.info(f"加载 {template_type} 模板: {template_name} 从 {file}")
                        else:
                            logger.warning(f"模板文件 {file} 为空或格式无效，已跳过。")
                except yaml.YAMLError as e:
                    logger.error(f"解析模板文件 {file} 失败: {e}")
                except Exception as e:
                    logger.error(f"加载模板文件 {file} 时发生错误: {e}")

        except Exception as e:
            logger.error(f"加载 {template_type} 模板时发生错误: {e}")

    def _load_all_templates(self):
        """加载所有类型的模板"""
        self._load_templates_from_dir(self.prompts_dir, "prompts")
        self._load_templates_from_dir(self.emails_dir, "emails")

        # 可选：检查是否至少加载了一个prompt和一个email模板
        if not self.templates["prompts"]:
            logger.warning("未找到或加载任何 prompt 模板。")
        if not self.templates["emails"]:
            logger.warning("未找到或加载任何 email 模板。")
    
    def get_template(self, template_type: str, name: str) -> Optional[Dict[str, Any]]:
        """获取指定类型的模板"""
        if template_type not in self.templates:
            logger.error(f"无效的模板类型: {template_type}. 可用类型: {list(self.templates.keys())}")
            return None
        
        template = self.templates[template_type].get(name)
        if not template:
             logger.warning(f"在类型 '{template_type}' 中未找到名为 '{name}' 的模板.")
        return template
    
    # 注意：add/update/delete 方法与当前基于目录的加载逻辑不兼容，已移除
    # 如果需要动态增删改模板，需要不同的实现方式 (e.g., direct file writing) 
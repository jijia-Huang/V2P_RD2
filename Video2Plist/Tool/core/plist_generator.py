# -*- coding: utf-8 -*-
"""
Plist 檔案生成器
生成 Cocos2d-x 相容的 plist 格式檔案
"""
import os
import logging
import xml.etree.ElementTree as ET
from typing import Dict, Tuple
from xml.dom import minidom


class PlistGenerator:
    """Plist 檔案生成器"""
    
    def __init__(self):
        """初始化生成器"""
        logging.debug("初始化 Plist 生成器")
    
    def generate_plist(self, frames_data: Dict, texture_filename: str, 
                      texture_size: Tuple[int, int], output_path: str):
        """
        生成 plist 檔案
        
        Args:
            frames_data: 影格資料字典
            texture_filename: 材質檔案名稱
            texture_size: 材質尺寸 (width, height)
            output_path: 輸出檔案路徑
        """
        try:
            # 建立 XML 結構
            root = self._create_plist_root()
            
            # 建立主字典
            main_dict = ET.SubElement(root, "dict")
            
            # 添加 frames 字典
            self._add_frames_dict(main_dict, frames_data)
            
            # 添加 metadata 字典
            self._add_metadata_dict(main_dict, texture_filename, texture_size)
            
            # 格式化並保存 XML
            self._save_formatted_xml(root, output_path)
            
            logging.debug(f"生成 plist 檔案: {output_path}")
            
        except Exception as e:
            logging.error(f"生成 plist 檔案失敗: {str(e)}", exc_info=True)
            raise
    
    def _create_plist_root(self) -> ET.Element:
        """建立 plist 根元素"""
        root = ET.Element("plist")
        root.set("version", "1.0")
        return root
    
    def _add_frames_dict(self, parent: ET.Element, frames_data: Dict):
        """添加 frames 字典"""
        # frames key
        frames_key = ET.SubElement(parent, "key")
        frames_key.text = "frames"
        
        # frames dict
        frames_dict = ET.SubElement(parent, "dict")
        
        # 為每個影格添加資料
        for frame_name, frame_data in frames_data.items():
            self._add_frame_entry(frames_dict, frame_name, frame_data)
    
    def _add_frame_entry(self, frames_dict: ET.Element, frame_name: str, frame_data: Dict):
        """添加單個影格條目"""
        # 影格名稱 key
        frame_key = ET.SubElement(frames_dict, "key")
        frame_key.text = f"{frame_name}.png"  # 確保有 .png 副檔名
        
        # 影格資料 dict
        frame_dict = ET.SubElement(frames_dict, "dict")
        
        # aliases (空陣列)
        self._add_key_value(frame_dict, "aliases", "array", None)
        
        # spriteOffset
        offset_x = frame_data.get("offset_x", 0)
        offset_y = frame_data.get("offset_y", 0)
        self._add_key_value(frame_dict, "spriteOffset", "string", f"{{{offset_x},{offset_y}}}")
        
        # spriteSize
        width = frame_data["width"]
        height = frame_data["height"]
        self._add_key_value(frame_dict, "spriteSize", "string", f"{{{width},{height}}}")
        
        # spriteSourceSize (與 spriteSize 相同)
        self._add_key_value(frame_dict, "spriteSourceSize", "string", f"{{{width},{height}}}")
        
        # textureRect
        x = frame_data["x"]
        y = frame_data["y"]
        self._add_key_value(frame_dict, "textureRect", "string", f"{{{{{x},{y}}},{{{width},{height}}}}}")
        
        # textureRotated
        rotated = frame_data.get("rotated", False)
        self._add_key_value(frame_dict, "textureRotated", "true" if rotated else "false", None)
    
    def _add_metadata_dict(self, parent: ET.Element, texture_filename: str, texture_size: Tuple[int, int]):
        """添加 metadata 字典"""
        # metadata key
        metadata_key = ET.SubElement(parent, "key")
        metadata_key.text = "metadata"
        
        # metadata dict
        metadata_dict = ET.SubElement(parent, "dict")
        
        # format
        self._add_key_value(metadata_dict, "format", "integer", "3")
        
        # pixelFormat
        self._add_key_value(metadata_dict, "pixelFormat", "string", "RGBA8888")
        
        # premultiplyAlpha
        self._add_key_value(metadata_dict, "premultiplyAlpha", "false", None)
        
        # realTextureFileName
        self._add_key_value(metadata_dict, "realTextureFileName", "string", texture_filename)
        
        # size
        width, height = texture_size
        self._add_key_value(metadata_dict, "size", "string", f"{{{width},{height}}}")
        
        # smartupdate (使用簡化的版本)
        smartupdate = f"$TexturePacker:SmartUpdate:PythonPacker:Generated:{texture_filename}$"
        self._add_key_value(metadata_dict, "smartupdate", "string", smartupdate)
        
        # textureFileName
        self._add_key_value(metadata_dict, "textureFileName", "string", texture_filename)
    
    def _add_key_value(self, parent: ET.Element, key_name: str, value_type: str, value: str):
        """添加 key-value 對"""
        # key 元素
        key_elem = ET.SubElement(parent, "key")
        key_elem.text = key_name
        
        # value 元素
        if value_type == "array":
            # 空陣列
            ET.SubElement(parent, "array")
        elif value_type in ["true", "false"]:
            # 布林值
            ET.SubElement(parent, value_type)
        elif value_type == "integer":
            # 整數
            int_elem = ET.SubElement(parent, "integer")
            int_elem.text = value
        elif value_type == "string":
            # 字串
            string_elem = ET.SubElement(parent, "string")
            string_elem.text = value
    
    def _save_formatted_xml(self, root: ET.Element, output_path: str):
        """格式化並保存 XML 檔案"""
        # 建立 XML 聲明和 DOCTYPE
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
        doctype = '<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        
        # 轉換為字串並格式化
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        
        # 獲取格式化的 XML（跳過第一行的 XML 聲明）
        formatted_xml = reparsed.toprettyxml(indent="    ", encoding=None)
        lines = formatted_xml.split('\n')
        formatted_content = '\n'.join(lines[1:])  # 跳過自動生成的 XML 聲明
        
        # 組合最終內容
        final_content = xml_declaration + doctype + formatted_content
        
        # 清理多餘的空行
        final_content = self._clean_xml_formatting(final_content)
        
        # 保存到檔案
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
    
    def _clean_xml_formatting(self, xml_content: str) -> str:
        """清理 XML 格式化"""
        lines = xml_content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # 移除完全空白的行
            if line.strip():
                cleaned_lines.append(line)
            elif cleaned_lines and cleaned_lines[-1].strip():
                # 保留有意義的空行（在非空行後）
                cleaned_lines.append('')
        
        # 確保檔案以換行結尾
        result = '\n'.join(cleaned_lines)
        if not result.endswith('\n'):
            result += '\n'
        
        return result
    
    def validate_plist_structure(self, plist_path: str) -> bool:
        """
        驗證 plist 檔案結構
        
        Args:
            plist_path: plist 檔案路徑
            
        Returns:
            bool: 驗證是否通過
        """
        try:
            if not os.path.exists(plist_path):
                logging.error(f"Plist 檔案不存在: {plist_path}")
                return False
            
            # 解析 XML
            tree = ET.parse(plist_path)
            root = tree.getroot()
            
            # 檢查根元素
            if root.tag != "plist":
                logging.error("根元素不是 plist")
                return False
            
            # 檢查版本
            if root.get("version") != "1.0":
                logging.error("plist 版本不是 1.0")
                return False
            
            # 檢查主字典
            main_dict = root.find("dict")
            if main_dict is None:
                logging.error("找不到主字典")
                return False
            
            # 檢查 frames 和 metadata
            has_frames = False
            has_metadata = False
            
            keys = main_dict.findall("key")
            for key in keys:
                if key.text == "frames":
                    has_frames = True
                elif key.text == "metadata":
                    has_metadata = True
            
            if not has_frames:
                logging.error("找不到 frames 字典")
                return False
            
            if not has_metadata:
                logging.error("找不到 metadata 字典")
                return False
            
            logging.debug(f"Plist 結構驗證通過: {plist_path}")
            return True
            
        except Exception as e:
            logging.error(f"Plist 驗證失敗: {str(e)}", exc_info=True)
            return False

# -*- coding: utf-8 -*-
"""
圖像處理工具
提供圖像載入、處理和優化功能
"""
import os
import logging
from typing import List, Tuple, Optional
from PIL import Image, ImageOps
from .exceptions import FileError, ConversionError


class ImageProcessor:
    """圖像處理器"""
    
    def __init__(self):
        """初始化處理器"""
        self.supported_formats = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}
        logging.debug("初始化圖像處理器")
    
    def validate_image_files(self, image_paths: List[str]) -> List[str]:
        """
        驗證圖像檔案
        
        Args:
            image_paths: 圖像檔案路徑列表
            
        Returns:
            List[str]: 有效的圖像檔案路徑列表
            
        Raises:
            FileError: 檔案不存在或格式不支援
        """
        valid_paths = []
        
        for path in image_paths:
            if not os.path.exists(path):
                raise FileError(f"圖像檔案不存在: {path}")
            
            # 檢查檔案副檔名
            ext = os.path.splitext(path)[1].lower()
            if ext not in self.supported_formats:
                logging.warning(f"不支援的圖像格式: {path}")
                continue
            
            # 嘗試載入圖像以驗證格式
            try:
                with Image.open(path) as img:
                    # 檢查圖像是否有效
                    img.verify()
                valid_paths.append(path)
                
            except Exception as e:
                logging.error(f"無效的圖像檔案 {path}: {str(e)}")
                raise FileError(f"無效的圖像檔案: {path}")
        
        logging.info(f"驗證完成: {len(valid_paths)}/{len(image_paths)} 個有效圖像")
        return valid_paths
    
    def get_image_info(self, image_path: str) -> dict:
        """
        獲取圖像資訊
        
        Args:
            image_path: 圖像檔案路徑
            
        Returns:
            dict: 圖像資訊
        """
        try:
            with Image.open(image_path) as img:
                return {
                    "path": image_path,
                    "filename": os.path.basename(image_path),
                    "size": img.size,
                    "width": img.size[0],
                    "height": img.size[1],
                    "mode": img.mode,
                    "format": img.format,
                    "has_transparency": self._has_transparency(img)
                }
        except Exception as e:
            logging.error(f"獲取圖像資訊失敗 {image_path}: {str(e)}")
            raise FileError(f"獲取圖像資訊失敗: {image_path}")
    
    def _has_transparency(self, img: Image.Image) -> bool:
        """檢查圖像是否有透明度"""
        return (
            img.mode in ('RGBA', 'LA') or 
            (img.mode == 'P' and 'transparency' in img.info)
        )
    
    def optimize_image(self, image_path: str, output_path: str, 
                      quality: int = 95, optimize: bool = True) -> bool:
        """
        優化圖像
        
        Args:
            image_path: 輸入圖像路徑
            output_path: 輸出圖像路徑
            quality: JPEG 品質 (1-100)
            optimize: 是否優化
            
        Returns:
            bool: 是否成功
        """
        try:
            with Image.open(image_path) as img:
                # 確保輸出目錄存在
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # 根據輸出格式處理
                output_ext = os.path.splitext(output_path)[1].lower()
                
                if output_ext in ['.jpg', '.jpeg']:
                    # JPEG 不支援透明度，轉換為 RGB
                    if img.mode in ('RGBA', 'LA', 'P'):
                        # 創建白色背景
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                        img = background
                    
                    img.save(output_path, 'JPEG', quality=quality, optimize=optimize)
                    
                elif output_ext == '.png':
                    # PNG 支援透明度
                    if img.mode not in ('RGBA', 'RGB', 'L', 'LA'):
                        img = img.convert('RGBA')
                    
                    img.save(output_path, 'PNG', optimize=optimize)
                
                else:
                    # 其他格式直接保存
                    img.save(output_path, optimize=optimize)
                
                logging.debug(f"圖像優化完成: {output_path}")
                return True
                
        except Exception as e:
            logging.error(f"圖像優化失敗 {image_path}: {str(e)}")
            return False
    
    def resize_image(self, image_path: str, output_path: str, 
                    size: Tuple[int, int], resample: int = Image.LANCZOS) -> bool:
        """
        調整圖像大小
        
        Args:
            image_path: 輸入圖像路徑
            output_path: 輸出圖像路徑
            size: 目標尺寸 (width, height)
            resample: 重採樣方法
            
        Returns:
            bool: 是否成功
        """
        try:
            with Image.open(image_path) as img:
                # 調整大小
                resized_img = img.resize(size, resample)
                
                # 確保輸出目錄存在
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # 保存
                resized_img.save(output_path)
                
                logging.debug(f"圖像調整大小完成: {output_path} ({size})")
                return True
                
        except Exception as e:
            logging.error(f"圖像調整大小失敗 {image_path}: {str(e)}")
            return False
    
    def crop_image(self, image_path: str, output_path: str, 
                  box: Tuple[int, int, int, int]) -> bool:
        """
        裁剪圖像
        
        Args:
            image_path: 輸入圖像路徑
            output_path: 輸出圖像路徑
            box: 裁剪區域 (left, top, right, bottom)
            
        Returns:
            bool: 是否成功
        """
        try:
            with Image.open(image_path) as img:
                # 裁剪
                cropped_img = img.crop(box)
                
                # 確保輸出目錄存在
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # 保存
                cropped_img.save(output_path)
                
                logging.debug(f"圖像裁剪完成: {output_path}")
                return True
                
        except Exception as e:
            logging.error(f"圖像裁剪失敗 {image_path}: {str(e)}")
            return False
    
    def rotate_image(self, image_path: str, output_path: str, 
                    angle: float, expand: bool = True) -> bool:
        """
        旋轉圖像
        
        Args:
            image_path: 輸入圖像路徑
            output_path: 輸出圖像路徑
            angle: 旋轉角度（逆時針）
            expand: 是否擴展畫布以容納旋轉後的圖像
            
        Returns:
            bool: 是否成功
        """
        try:
            with Image.open(image_path) as img:
                # 旋轉
                rotated_img = img.rotate(angle, expand=expand, fillcolor=(0, 0, 0, 0))
                
                # 確保輸出目錄存在
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # 保存
                rotated_img.save(output_path)
                
                logging.debug(f"圖像旋轉完成: {output_path} ({angle}°)")
                return True
                
        except Exception as e:
            logging.error(f"圖像旋轉失敗 {image_path}: {str(e)}")
            return False
    
    def convert_format(self, image_path: str, output_path: str, 
                      target_format: str = "PNG") -> bool:
        """
        轉換圖像格式
        
        Args:
            image_path: 輸入圖像路徑
            output_path: 輸出圖像路徑
            target_format: 目標格式 (PNG, JPEG, etc.)
            
        Returns:
            bool: 是否成功
        """
        try:
            with Image.open(image_path) as img:
                # 確保輸出目錄存在
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # 根據目標格式處理
                if target_format.upper() in ['JPG', 'JPEG']:
                    # JPEG 不支援透明度
                    if img.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                        img = background
                    
                    img.save(output_path, 'JPEG', quality=95)
                    
                elif target_format.upper() == 'PNG':
                    # PNG 支援透明度
                    if img.mode not in ('RGBA', 'RGB', 'L', 'LA'):
                        img = img.convert('RGBA')
                    
                    img.save(output_path, 'PNG')
                
                else:
                    # 其他格式
                    img.save(output_path, target_format.upper())
                
                logging.debug(f"格式轉換完成: {output_path} ({target_format})")
                return True
                
        except Exception as e:
            logging.error(f"格式轉換失敗 {image_path}: {str(e)}")
            return False
    
    def get_batch_info(self, image_paths: List[str]) -> dict:
        """
        獲取批次圖像資訊
        
        Args:
            image_paths: 圖像檔案路徑列表
            
        Returns:
            dict: 批次資訊統計
        """
        stats = {
            "total_count": len(image_paths),
            "valid_count": 0,
            "total_size": 0,
            "size_range": {"min": None, "max": None},
            "formats": {},
            "has_transparency": 0,
            "average_size": (0, 0)
        }
        
        valid_images = []
        total_width = 0
        total_height = 0
        
        for path in image_paths:
            try:
                info = self.get_image_info(path)
                valid_images.append(info)
                stats["valid_count"] += 1
                
                # 檔案大小
                file_size = os.path.getsize(path)
                stats["total_size"] += file_size
                
                # 尺寸範圍
                width, height = info["size"]
                area = width * height
                
                if stats["size_range"]["min"] is None or area < stats["size_range"]["min"]:
                    stats["size_range"]["min"] = area
                
                if stats["size_range"]["max"] is None or area > stats["size_range"]["max"]:
                    stats["size_range"]["max"] = area
                
                # 格式統計
                format_name = info["format"] or "Unknown"
                stats["formats"][format_name] = stats["formats"].get(format_name, 0) + 1
                
                # 透明度統計
                if info["has_transparency"]:
                    stats["has_transparency"] += 1
                
                # 平均尺寸
                total_width += width
                total_height += height
                
            except Exception as e:
                logging.warning(f"跳過無效圖像 {path}: {str(e)}")
        
        # 計算平均尺寸
        if stats["valid_count"] > 0:
            stats["average_size"] = (
                total_width // stats["valid_count"],
                total_height // stats["valid_count"]
            )
        
        logging.info(f"批次圖像分析完成: {stats['valid_count']}/{stats['total_count']} 個有效圖像")
        return stats

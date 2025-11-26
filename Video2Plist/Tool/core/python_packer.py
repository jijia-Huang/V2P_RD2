# -*- coding: utf-8 -*-
"""
Python 原生材質打包器
作為 TexturePacker 的備選方案，實現材質集打包功能
"""
import os
import logging
import time
from typing import List, Dict, Tuple, Optional
from PIL import Image
from .maxrects_algorithm import MaxRectsPacker, Rect
from .plist_generator import PlistGenerator
from .image_processor import ImageProcessor
from .exceptions import ConversionError, FileError


class PythonTexturePacker:
    """Python 原生材質打包器"""
    
    def __init__(self, max_width: int = 2048, max_height: int = 2048, output_format: str = "PNG"):
        """
        初始化打包器
        
        Args:
            max_width: 材質集最大寬度
            max_height: 材質集最大高度
            output_format: 輸出格式 (PNG/JPG)
        """
        self.max_width = max_width
        self.max_height = max_height
        self.output_format = output_format.upper()
        self.image_processor = ImageProcessor()
        self.plist_generator = PlistGenerator()
        
        logging.info(f"初始化 Python 打包器 - 尺寸: {max_width}x{max_height}, 格式: {output_format}")
    
    def pack_images(self, image_paths: List[str], output_dir: str, output_name: str) -> Dict:
        """
        打包圖像序列
        
        Args:
            image_paths: 圖像檔案路徑列表
            output_dir: 輸出目錄
            output_name: 輸出名稱
            
        Returns:
            Dict: 打包結果資訊
            
        Raises:
            FileError: 圖像檔案不存在
            ConversionError: 打包過程失敗
        """
        start_time = time.time()
        
        try:
            # 驗證輸入
            self._validate_inputs(image_paths, output_dir, output_name)
            
            # 載入圖像資訊
            logging.info(f"載入 {len(image_paths)} 個圖像檔案...")
            image_rects = self._load_image_info(image_paths)
            
            # 執行打包
            logging.info("開始執行矩形打包演算法...")
            packed_sheets = self._pack_rects(image_rects)
            
            # 生成材質集圖片和 plist 檔案
            logging.info(f"生成 {len(packed_sheets)} 個材質集...")
            result = self._generate_output(packed_sheets, output_dir, output_name)
            
            elapsed_time = time.time() - start_time
            logging.info(f"Python 打包器完成 - 耗時: {elapsed_time:.2f}s")
            
            return {
                "success": True,
                "sheets_count": len(packed_sheets),
                "total_frames": len(image_paths),
                "elapsed_time": elapsed_time,
                "output_files": result["output_files"]
            }
            
        except Exception as e:
            logging.error(f"Python 打包器執行失敗: {str(e)}", exc_info=True)
            raise ConversionError("Python 打包器執行失敗", details=str(e))
    
    def _validate_inputs(self, image_paths: List[str], output_dir: str, output_name: str):
        """驗證輸入參數"""
        if not image_paths:
            raise FileError("沒有提供圖像檔案")
        
        if not output_dir:
            raise FileError("未指定輸出目錄")
        
        if not output_name:
            raise FileError("未指定輸出名稱")
        
        # 檢查圖像檔案是否存在
        for image_path in image_paths:
            if not os.path.exists(image_path):
                raise FileError(f"找不到圖像檔案: {image_path}")
        
        # 確保輸出目錄存在
        os.makedirs(output_dir, exist_ok=True)
    
    def _load_image_info(self, image_paths: List[str]) -> List[Rect]:
        """載入圖像資訊並創建矩形物件"""
        image_rects = []
        # 重新掃描影格目錄，優先使用 filter_ 前綴的去背圖像
        frames_dir = os.path.dirname(image_paths[0]) if image_paths else ""
        if frames_dir:
            import glob
            
            # 先檢查是否有 filter_ 前綴的圖片（去背圖片）
            filter_image_paths = sorted(glob.glob(os.path.join(frames_dir, "filter_*.png")))
            if filter_image_paths:
                logging.info(f"檢測到 {len(filter_image_paths)} 個去背的圖片，使用去背圖片進行打包")
                image_paths = filter_image_paths
            else:
                # 如果沒有去背圖片，使用原始圖片
                actual_image_paths = sorted(glob.glob(os.path.join(frames_dir, "*.png")))
                if actual_image_paths:
                    logging.info(f"未檢測到去背圖片，使用原始影格進行打包，共 {len(actual_image_paths)} 個")
                    image_paths = actual_image_paths
        
        for i, image_path in enumerate(image_paths):
            try:
                # 檢查檔案修改時間
                import time
                file_mtime = os.path.getmtime(image_path)
                file_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_mtime))
                logging.debug(f"載入圖像進行打包: {image_path} (修改時間: {file_time_str})")
                with Image.open(image_path) as img:
                    width, height = img.size
                    
                    # 創建矩形物件
                    rect = Rect(0, 0, width, height)
                    rect.image_path = image_path
                    
                    # 設定 frame_name，移除 filter_ 前綴（如果有的話）
                    base_name = os.path.splitext(os.path.basename(image_path))[0]
                    if base_name.startswith("filter_"):
                        base_name = base_name[7:]  # 移除 "filter_" 前綴 (7 個字元)
                    rect.frame_name = base_name
                    
                    rect.original_size = (width, height)
                    
                    image_rects.append(rect)
                    
            except Exception as e:
                logging.error(f"載入圖像失敗 {image_path}: {str(e)}")
                raise FileError(f"載入圖像失敗: {image_path}")
        
        logging.info(f"載入完成 - 總計 {len(image_rects)} 個圖像")
        return image_rects
    
    def _pack_rects(self, image_rects: List[Rect]) -> List[Dict]:
        """執行矩形打包演算法"""
        packed_sheets = []
        remaining_rects = image_rects.copy()
        sheet_index = 0
        
        while remaining_rects:
            # 為當前材質集創建打包器
            packer = MaxRectsPacker(self.max_width, self.max_height)
            
            # 嘗試打包剩餘的矩形
            packed_rects = packer.pack_rects(remaining_rects.copy())
            
            if not packed_rects:
                # 如果沒有任何矩形能被打包，說明單個圖像太大
                largest_rect = max(remaining_rects, key=lambda r: r.width * r.height)
                logging.error(f"圖像過大無法打包: {largest_rect.frame_name} ({largest_rect.width}x{largest_rect.height})")
                raise ConversionError(f"圖像過大: {largest_rect.frame_name}")
            
            # 記錄打包結果
            packed_sheets.append({
                "index": sheet_index,
                "rects": packed_rects,
                "width": self.max_width,
                "height": self.max_height
            })
            
            # 從剩餘列表中移除已打包的矩形
            packed_paths = {rect.image_path for rect in packed_rects}
            remaining_rects = [rect for rect in remaining_rects if rect.image_path not in packed_paths]
            
            logging.debug(f"材質集 {sheet_index}: 打包 {len(packed_rects)} 個圖像，剩餘 {len(remaining_rects)} 個")
            sheet_index += 1
        
        return packed_sheets
    
    def _generate_output(self, packed_sheets: List[Dict], output_dir: str, output_name: str) -> Dict:
        """生成輸出檔案"""
        output_files = []
        
        for sheet in packed_sheets:
            sheet_index = sheet["index"]
            
            # 生成材質集圖片
            texture_path = os.path.join(output_dir, f"{output_name}_{sheet_index}.{self.output_format.lower()}")
            self._generate_texture_image(sheet, texture_path)
            output_files.append(texture_path)
            
            # 生成 plist 檔案
            plist_path = os.path.join(output_dir, f"{output_name}_{sheet_index}.plist")
            self._generate_plist_file(sheet, plist_path, os.path.basename(texture_path))
            output_files.append(plist_path)
        
        return {"output_files": output_files}
    
    def _generate_texture_image(self, sheet: Dict, output_path: str):
        """生成材質集圖片"""
        # 創建空白畫布
        texture = Image.new("RGBA", (sheet["width"], sheet["height"]), (0, 0, 0, 0))
        
        for rect in sheet["rects"]:
            try:
                # 載入圖像（應該是去背後的圖像）
                with Image.open(rect.image_path) as img:
                    # 如果需要旋轉
                    if getattr(rect, 'rotated', False):
                        img = img.rotate(-90, expand=True)
                    
                    # 貼到材質集上
                    texture.paste(img, (rect.x, rect.y))
                    
            except Exception as e:
                logging.error(f"貼圖失敗 {rect.image_path}: {str(e)}")
                raise ConversionError(f"貼圖失敗: {rect.frame_name}")
        
        # 保存材質集
        if self.output_format == "JPG":
            # JPG 不支援透明度，轉換為 RGB
            rgb_texture = Image.new("RGB", texture.size, (255, 255, 255))
            rgb_texture.paste(texture, mask=texture.split()[-1] if texture.mode == "RGBA" else None)
            rgb_texture.save(output_path, "JPEG", quality=95)
        else:
            texture.save(output_path, "PNG")
        
        logging.debug(f"生成材質集圖片: {output_path}")
    
    def _generate_plist_file(self, sheet: Dict, plist_path: str, texture_filename: str):
        """生成 plist 檔案"""
        frames_data = {}
        
        for rect in sheet["rects"]:
            frame_data = {
                "x": rect.x,
                "y": rect.y,
                "width": rect.width,
                "height": rect.height,
                "original_width": rect.original_size[0],
                "original_height": rect.original_size[1],
                "offset_x": 0,  # 暫時設為 0，後續可根據需要調整
                "offset_y": 0,
                "rotated": getattr(rect, 'rotated', False)
            }
            frames_data[rect.frame_name] = frame_data
        
        # 生成 plist
        self.plist_generator.generate_plist(
            frames_data=frames_data,
            texture_filename=texture_filename,
            texture_size=(sheet["width"], sheet["height"]),
            output_path=plist_path
        )
        
        logging.debug(f"生成 plist 檔案: {plist_path}")

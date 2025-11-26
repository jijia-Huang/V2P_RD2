# -*- coding: utf-8 -*-
"""
MaxRects 矩形打包演算法實現
基於 Jukka Jylänki 的 MaxRects 演算法
"""
import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Rect:
    """矩形類別"""
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    
    def __post_init__(self):
        """初始化後處理"""
        # 額外屬性
        self.rotated = False
        self.image_path = ""
        self.frame_name = ""
        self.original_size = (0, 0)
    
    @property
    def area(self) -> int:
        """計算面積"""
        return self.width * self.height
    
    @property
    def right(self) -> int:
        """右邊界"""
        return self.x + self.width
    
    @property
    def bottom(self) -> int:
        """下邊界"""
        return self.y + self.height
    
    def contains(self, other: 'Rect') -> bool:
        """檢查是否包含另一個矩形"""
        return (self.x <= other.x and 
                self.y <= other.y and 
                self.right >= other.right and 
                self.bottom >= other.bottom)
    
    def intersects(self, other: 'Rect') -> bool:
        """檢查是否與另一個矩形相交"""
        return not (self.right <= other.x or 
                   other.right <= self.x or 
                   self.bottom <= other.y or 
                   other.bottom <= self.y)
    
    def __str__(self) -> str:
        return f"Rect({self.x}, {self.y}, {self.width}, {self.height})"


class MaxRectsPacker:
    """MaxRects 矩形打包器"""
    
    def __init__(self, width: int, height: int):
        """
        初始化打包器
        
        Args:
            width: 容器寬度
            height: 容器高度
        """
        self.width = width
        self.height = height
        self.free_rects = [Rect(0, 0, width, height)]
        self.used_rects = []
        
        logging.debug(f"初始化 MaxRects 打包器: {width}x{height}")
    
    def pack_rects(self, rects: List[Rect]) -> List[Rect]:
        """
        打包矩形列表
        
        Args:
            rects: 要打包的矩形列表
            
        Returns:
            List[Rect]: 成功打包的矩形列表
        """
        # 按面積排序（大矩形優先）
        rects_to_pack = sorted(rects, key=lambda r: r.area, reverse=True)
        packed_rects = []
        
        logging.debug(f"開始打包 {len(rects_to_pack)} 個矩形")
        
        for rect in rects_to_pack:
            # 嘗試不旋轉和旋轉兩種方式
            best_position = None
            best_rotated = False
            best_score = float('inf')
            
            # 嘗試不旋轉
            position = self._find_best_position(rect.width, rect.height)
            if position:
                score = self._calculate_score(position, rect.width, rect.height)
                if score < best_score:
                    best_position = position
                    best_rotated = False
                    best_score = score
            
            # 嘗試旋轉（如果寬高不同）
            if rect.width != rect.height:
                position = self._find_best_position(rect.height, rect.width)
                if position:
                    score = self._calculate_score(position, rect.height, rect.width)
                    if score < best_score:
                        best_position = position
                        best_rotated = True
                        best_score = score
            
            # 如果找到位置，放置矩形
            if best_position:
                if best_rotated:
                    rect.width, rect.height = rect.height, rect.width
                    rect.rotated = True
                
                rect.x = best_position.x
                rect.y = best_position.y
                
                # 記錄已使用的矩形
                used_rect = Rect(rect.x, rect.y, rect.width, rect.height)
                self.used_rects.append(used_rect)
                
                # 分割剩餘空間
                self._split_free_rect(best_position, rect)
                
                # 清理重疊的空閒矩形
                self._cleanup_free_rects()
                
                packed_rects.append(rect)
                logging.debug(f"成功打包: {rect.frame_name} at ({rect.x}, {rect.y})")
            else:
                logging.debug(f"無法打包: {rect.frame_name} ({rect.width}x{rect.height})")
                break  # 無法打包更多矩形
        
        logging.info(f"打包完成: {len(packed_rects)}/{len(rects_to_pack)} 個矩形")
        return packed_rects
    
    def _find_best_position(self, width: int, height: int) -> Optional[Rect]:
        """
        尋找最佳放置位置
        
        Args:
            width: 矩形寬度
            height: 矩形高度
            
        Returns:
            Optional[Rect]: 最佳位置，如果沒有合適位置則返回 None
        """
        best_rect = None
        best_short_side = float('inf')
        best_long_side = float('inf')
        
        for free_rect in self.free_rects:
            # 檢查是否能放入
            if free_rect.width >= width and free_rect.height >= height:
                # 計算剩餘空間
                leftover_horiz = free_rect.width - width
                leftover_vert = free_rect.height - height
                short_side = min(leftover_horiz, leftover_vert)
                long_side = max(leftover_horiz, leftover_vert)
                
                # 選擇最佳位置（剩餘空間最小的）
                if (short_side < best_short_side or 
                    (short_side == best_short_side and long_side < best_long_side)):
                    best_rect = free_rect
                    best_short_side = short_side
                    best_long_side = long_side
        
        return best_rect
    
    def _calculate_score(self, position: Rect, width: int, height: int) -> float:
        """
        計算位置分數（越小越好）
        
        Args:
            position: 候選位置
            width: 矩形寬度
            height: 矩形高度
            
        Returns:
            float: 位置分數
        """
        leftover_horiz = position.width - width
        leftover_vert = position.height - height
        short_side = min(leftover_horiz, leftover_vert)
        long_side = max(leftover_horiz, leftover_vert)
        
        # 使用 Best Short Side Fit 策略
        return short_side + long_side * 0.1
    
    def _split_free_rect(self, free_rect: Rect, used_rect: Rect):
        """
        分割空閒矩形
        
        Args:
            free_rect: 被分割的空閒矩形
            used_rect: 已使用的矩形
        """
        # 移除被使用的空閒矩形
        if free_rect in self.free_rects:
            self.free_rects.remove(free_rect)
        
        # 計算分割後的新矩形
        new_rects = []
        
        # 左側剩餘空間
        if used_rect.x > free_rect.x:
            new_rects.append(Rect(
                free_rect.x, 
                free_rect.y,
                used_rect.x - free_rect.x,
                free_rect.height
            ))
        
        # 右側剩餘空間
        if used_rect.right < free_rect.right:
            new_rects.append(Rect(
                used_rect.right,
                free_rect.y,
                free_rect.right - used_rect.right,
                free_rect.height
            ))
        
        # 上方剩餘空間
        if used_rect.y > free_rect.y:
            new_rects.append(Rect(
                free_rect.x,
                free_rect.y,
                free_rect.width,
                used_rect.y - free_rect.y
            ))
        
        # 下方剩餘空間
        if used_rect.bottom < free_rect.bottom:
            new_rects.append(Rect(
                free_rect.x,
                used_rect.bottom,
                free_rect.width,
                free_rect.bottom - used_rect.bottom
            ))
        
        # 添加新的空閒矩形
        self.free_rects.extend(new_rects)
    
    def _cleanup_free_rects(self):
        """清理重疊和包含的空閒矩形"""
        i = 0
        while i < len(self.free_rects):
            j = i + 1
            while j < len(self.free_rects):
                rect_i = self.free_rects[i]
                rect_j = self.free_rects[j]
                
                # 如果 i 包含 j，移除 j
                if rect_i.contains(rect_j):
                    self.free_rects.pop(j)
                    continue
                
                # 如果 j 包含 i，移除 i
                if rect_j.contains(rect_i):
                    self.free_rects.pop(i)
                    i -= 1  # 重新檢查當前位置
                    break
                
                j += 1
            i += 1
        
        # 移除與已使用矩形相交的空閒矩形
        self.free_rects = [
            free_rect for free_rect in self.free_rects
            if not any(free_rect.intersects(used_rect) for used_rect in self.used_rects)
        ]
    
    def get_efficiency(self) -> float:
        """
        計算空間利用率
        
        Returns:
            float: 利用率百分比 (0-100)
        """
        if not self.used_rects:
            return 0.0
        
        used_area = sum(rect.area for rect in self.used_rects)
        total_area = self.width * self.height
        
        return (used_area / total_area) * 100.0
    
    def get_stats(self) -> dict:
        """
        獲取打包統計資訊
        
        Returns:
            dict: 統計資訊
        """
        return {
            "container_size": (self.width, self.height),
            "used_rects": len(self.used_rects),
            "free_rects": len(self.free_rects),
            "efficiency": self.get_efficiency(),
            "used_area": sum(rect.area for rect in self.used_rects),
            "total_area": self.width * self.height
        }

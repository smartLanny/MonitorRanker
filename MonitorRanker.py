import sys
import re
import copy
import pandas as pd
import math

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QFileDialog, QLabel, QScrollArea, QLineEdit,
    QCheckBox, QSizePolicy, QFrame, QStatusBar, QToolButton, QMenu
)
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QFontMetrics, QPainterPath,
    QBrush, QLinearGradient, QPixmap, QAction, QIcon, QActionGroup
)
from PyQt6.QtCore import Qt, QRectF, QSize, pyqtSignal

# --- 全局配置 (Global Configurations) ---
CHART_CONFIG = { # 各项指标的默认配置 (Default config for each metric)
    "sRGB色准": {
        "csv_column": "sRGB色准", "unit": " ΔE", "lower_is_better": True,
        "bar_color": QColor(255, 100, 100), "base_title": "sRGB 色准"
    },
    "sRGB色域容积": {
        "csv_column": "sRGB色域容积", "unit": "%", "lower_is_better": False,
        "bar_color": QColor(100, 200, 100), "base_title": "sRGB 色域容积"
    },
    "P3色域覆盖率": {
        "csv_column": "P3色域覆盖率",
        "unit": "%",
        "lower_is_better": False,
        "bar_color": QColor(100, 100, 255),
        "base_title": "P3 色域覆盖率"
    },
    "可视角色差": { # 确保您的CSV列名与此处的 "csv_column" 完全一致
        "csv_column": "可视角色差", "unit": " ΔE", "lower_is_better": True,
        "bar_color": QColor(255, 150, 50), "base_title": "可视角 色差" # 标题可以略有不同
    },
    "可视角亮度衰减": { # 确保您的CSV列名与此处的 "csv_column" 完全一致
        "csv_column": "可视角亮度衰减", "unit": "%", "lower_is_better": True,
        "bar_color": QColor(150, 100, 200), "base_title": "可视角 亮度衰减"
    },
    "MPRT运动图像响应时间": { # 确保您的CSV列名与此处的 "csv_column" 完全一致
        "csv_column": "MPRT运动图像响应时间", "unit": "ms", "lower_is_better": True,
        "bar_color": QColor(0, 200, 255), "base_title": "MPRT 响应时间"
    }
}
DEFAULT_NEW_METRIC_COLOR = QColor(160, 160, 170)

RESOLUTION_ALIASES = {
    "3840*2160": "4K", "2560*1440": "2.5K", "1920*1080": "1080p",
    "5120*2880": "5K", "3440*1440": "3.5K UW", "2560*1080": "2.5K UW"
}
RESOLUTION_NUMERIC_MAP = {
    "1080p": 1, "2.5K UW": 2, "2.5K": 3, "3.5K UW": 4, "4K": 5, "5K": 6,
}

DEFAULT_PANEL_COLORS = {
    "FastIPS": QColor("#0F9D58").lighter(135), "HVA": QColor("#DB4437").lighter(110),
    "IPS": QColor("#0F9D58"), "QD-OLED": QColor("#C7B8EA"),
    "TN": QColor("#AB47BC"), "VA": QColor("#00ACC1"), "WOLED": QColor("#FF7043"),
    "未知": QColor("#9E9E9E"), "NanoIPS": QColor("#4285F4").lighter(110),
}
PANEL_COLORS = copy.deepcopy(DEFAULT_PANEL_COLORS)

COLOR_SCHEMES = {
    "默认": {
        "bar_colors": {k: v["bar_color"] for k, v in CHART_CONFIG.items() if "bar_color" in v},
        "panel_colors": copy.deepcopy(DEFAULT_PANEL_COLORS)
    },
    "Material Blue": {
        "bar_colors": { "sRGB色准": QColor("#1976D2"), "sRGB色域容积": QColor("#42A5F5"), "P3色域覆盖率": QColor("#1E88E5"), "可视角色差": QColor("#0D47A1"), "可视角亮度衰减": QColor("#64B5F6"), "MPRT运动图像响应时间": QColor("#2196F3"), },
        "panel_colors": { "FastIPS": QColor("#90CAF9"), "HVA": QColor("#E3F2FD"), "IPS": QColor("#1976D2"), "QD-OLED": QColor("#BBDEFB"), "TN": QColor("#0D47A1"), "VA": QColor("#2196F3"), "WOLED": QColor("#42A5F5"), "未知": QColor("#BDBDBD"), "NanoIPS": QColor("#1E88E5"), }
    },
     "Material Green & Amber": {
        "bar_colors": { "sRGB色准": QColor("#388E3C"), "sRGB色域容积": QColor("#FFC107"), "P3色域覆盖率": QColor("#4CAF50"), "可视角色差": QColor("#1B5E20"), "可视角亮度衰减": QColor("#FFD54F"), "MPRT运动图像响应时间": QColor("#81C784"),},
        "panel_colors": { "FastIPS": QColor("#A5D6A7"), "HVA": QColor("#FFE082"), "IPS": QColor("#388E3C"), "QD-OLED": QColor("#FFD54F"), "TN": QColor("#1B5E20"), "VA": QColor("#4CAF50"), "WOLED": QColor("#FFC107"), "未知": QColor("#BDBDBD"), "NanoIPS": QColor("#66BB6A"),}
    },
    "Material Deep Purple & Teal": {
        "bar_colors": { "sRGB色准": QColor("#512DA8"), "sRGB色域容积": QColor("#009688"), "P3色域覆盖率": QColor("#673AB7"), "可视角色差": QColor("#311B92"), "可视角亮度衰减": QColor("#4DB6AC"), "MPRT运动图像响应时间": QColor("#B39DDB"),},
        "panel_colors": { "FastIPS": QColor("#B39DDB"), "HVA": QColor("#80CBC4"), "IPS": QColor("#512DA8"), "QD-OLED": QColor("#7E57C2"), "TN": QColor("#311B92"), "VA": QColor("#673AB7"), "WOLED": QColor("#009688"), "未知": QColor("#BDBDBD"), "NanoIPS": QColor("#7E57C2"),}
    },
    "Material Pink & Cyan": {
        "bar_colors": { "sRGB色准": QColor("#C2185B"), "sRGB色域容积": QColor("#00BCD4"), "P3色域覆盖率": QColor("#E91E63"), "可视角色差": QColor("#880E4F"), "可视角亮度衰减": QColor("#4DD0E1"), "MPRT运动图像响应时间": QColor("#F48FB1"),},
        "panel_colors": { "FastIPS": QColor("#F48FB1"), "HVA": QColor("#80DEEA"), "IPS": QColor("#C2185B"), "QD-OLED": QColor("#F06292"), "TN": QColor("#880E4F"), "VA": QColor("#E91E63"), "WOLED": QColor("#00BCD4"), "未知": QColor("#BDBDBD"), "NanoIPS": QColor("#F06292"),}
    },
    "Material Orange & Indigo": {
        "bar_colors": { "sRGB色准": QColor("#E64A19"), "sRGB色域容积": QColor("#3F51B5"), "P3色域覆盖率": QColor("#FF5722"), "可视角色差": QColor("#BF360C"), "可视角亮度衰减": QColor("#7986CB"), "MPRT运动图像响应时间": QColor("#FFCCBC"),},
        "panel_colors": { "FastIPS": QColor("#FFAB91"), "HVA": QColor("#9FA8DA"), "IPS": QColor("#E64A19"), "QD-OLED": QColor("#FF8A65"), "TN": QColor("#BF360C"), "VA": QColor("#FF5722"), "WOLED": QColor("#3F51B5"), "未知": QColor("#BDBDBD"), "NanoIPS": QColor("#FF8A65"),}
    },
}

# --- 主题颜色 ---
THEMES = {
    "dark": {
        "background": "#2E3440", 
        "widget_background": "#101217", 
        "text_primary": "#ECEFF4", 
        "text_secondary": "#D8DEE9", 
        "accent": "#88C0D0", 
        "border": "#4C566A", 
        "chart_empty_text": "#E5E9F0",
        "header_background": "#3B4252", 
        "control_panel_background": "#434C5E", 
        "button_text": "#ECEFF4", 
        "disabled_text": "#5E697E",
        "chart_bar_background": "#2A2E37", 
    },
    "light": {
        "background": "#ECEFF4", 
        "widget_background": "#FFFFFF", 
        "text_primary": "#2E3440", 
        "text_secondary": "#4C566A", 
        "accent": "#5E81AC", 
        "border": "#D8DEE9", 
        "chart_empty_text": "#4C566A",
        "header_background": "#E5E9F0", 
        "control_panel_background": "#FFFFFF", 
        "button_text": "#FFFFFF", 
        "disabled_text": "#A0A7B5",
        "chart_bar_background": "#D8DEE9", 
    }
}


class ChartWidget(QWidget):
    EXPORT_TARGET_WIDTH = 1920
    EXPORT_FONT_SCALE_FACTOR = 1.4
    EXPORT_LAYOUT_PARAMS = { 
        "name_text_top_padding_abs": 8, 
        "gap_before_footnote_abs": 2, 
        "gap_after_name_block_abs_compact": 4, 
        "gap_after_name_block_abs_full": 5,    
        "gap_between_sub_label_lines_abs": 2,  
        "row_height_compact": 85, 
        "row_height_full": 115,  
        "base_title_height": 60,
        "show_size_resolution_export": False,
        "sub_label_line_extra_padding": 3, 
    }

    theme_changed = pyqtSignal() 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = []
        self.metric_key = None
        self.config = {}
        self._is_export_mode = False
        self._export_content_width = None
        self.show_size_resolution = False
        self.value_label_inside = False 

        ff = "Source Han Sans CN" 
        self.base_title_font = QFont(ff, int(20 * 1.3), QFont.Weight.ExtraBold)
        self.base_rank_font = QFont(ff, 16, QFont.Weight.Bold)
        self.base_name_font = QFont(ff, 14, QFont.Weight.Medium)
        self.base_sub_label_font = QFont(ff, 11, QFont.Weight.Normal)
        self.base_label_font = QFont(ff, 18, QFont.Weight.Bold)

        self.screen_padding = 20
        self.screen_rank_width = 60
        
        self.current_name_text_top_padding_abs = self.EXPORT_LAYOUT_PARAMS["name_text_top_padding_abs"]
        self.current_gap_before_footnote_abs = self.EXPORT_LAYOUT_PARAMS["gap_before_footnote_abs"]
        self.current_gap_after_name_block_abs_compact = self.EXPORT_LAYOUT_PARAMS["gap_after_name_block_abs_compact"]
        self.current_gap_after_name_block_abs_full = self.EXPORT_LAYOUT_PARAMS["gap_after_name_block_abs_full"]
        self.current_gap_between_sub_label_lines_abs = self.EXPORT_LAYOUT_PARAMS["gap_between_sub_label_lines_abs"]
        self.current_sub_label_line_extra_padding = self.EXPORT_LAYOUT_PARAMS["sub_label_line_extra_padding"]

        self.current_base_row_height_compact = self.EXPORT_LAYOUT_PARAMS["row_height_compact"]
        self.current_base_row_height_full = self.EXPORT_LAYOUT_PARAMS["row_height_full"]
        self.current_base_title_height = self.EXPORT_LAYOUT_PARAMS["base_title_height"]
        self.current_row_height = self.current_base_row_height_compact


        self.min_size, self.max_size = 0,1
        self.min_refresh, self.max_refresh = 0,1
        self.min_resolution_val, self.max_resolution_val = 0,1
        self.label_item_gap = 10

        self.text_primary_color = QColor(THEMES["dark"]["text_primary"])
        self.text_secondary_color = QColor(THEMES["dark"]["text_secondary"])
        self.chart_empty_text_color = QColor(THEMES["dark"]["chart_empty_text"])
        self.bar_background_color = QColor(THEMES["dark"]["chart_bar_background"])

        self.theme_changed.connect(self.update) 

    def set_theme_colors(self, primary_text, secondary_text, empty_text, bar_bg):
        self.text_primary_color = QColor(primary_text)
        self.text_secondary_color = QColor(secondary_text)
        self.chart_empty_text_color = QColor(empty_text)
        self.bar_background_color = QColor(bar_bg)
        self.theme_changed.emit()

    def setValueLabelPosition(self, inside: bool):
        if self.value_label_inside != inside:
            self.value_label_inside = inside
            self.update()

    def setShowSizeResolution(self, show_flag):
        if self.show_size_resolution != show_flag:
            self.show_size_resolution = show_flag
            if self.show_size_resolution:
                self.current_row_height = self.current_base_row_height_full
            else:
                self.current_row_height = self.current_base_row_height_compact
            self.adjustHeight() 
            

    def setData(self, df, metric_key):
        # print(f"ChartWidget.setData called with metric_key: {metric_key}") # DEBUG
        global CHART_CONFIG
        if df is None or df.empty:
            # print("ChartWidget.setData: df is None or empty, clearing data.") # DEBUG
            self.data = []; self.metric_key = None; self.config = {}
        elif metric_key not in CHART_CONFIG:
            # print(f"ChartWidget.setData: metric_key '{metric_key}' not in CHART_CONFIG, clearing data.") # DEBUG
            self.data = []; self.metric_key = None; self.config = {}
        else:
            # print(f"ChartWidget.setData: Processing metric '{metric_key}'") # DEBUG
            self.metric_key = metric_key
            self.config = copy.deepcopy(CHART_CONFIG[metric_key]) # Use deepcopy
            col = self.config["csv_column"]
            # print(f"ChartWidget.setData: Using CSV column '{col}' for metric '{metric_key}'") # DEBUG
            
            items = []
            for idx, r_series in df.iterrows(): 
                v = pd.NA 
                try:
                    val_from_df = r_series.get(col)
                    if pd.isna(val_from_df): continue
                    v = float(val_from_df) 
                    if math.isnan(v): continue
                except Exception as e:
                    # print(f"ChartWidget.setData: Error converting value for col '{col}', row {idx}: {e}") # DEBUG
                    continue
                
                size_n = ref_n = res_val_numeric = None; res_text_display = "N/A"
                try: size_n = float(str(r_series.get("显示器尺寸","")).replace('"',''))
                except: pass
                try: 
                    ref_str_item = str(r_series.get("刷新率",""))
                    ref_n = float(ref_str_item.replace("Hz","").replace("hz",""))
                except: pass
                try:
                    raw_res_str = str(r_series.get("分辨率",""))
                    res_text_display = RESOLUTION_ALIASES.get(raw_res_str, raw_res_str if raw_res_str else "N/A")
                    if res_text_display in RESOLUTION_NUMERIC_MAP: res_val_numeric = RESOLUTION_NUMERIC_MAP[res_text_display]
                    elif res_text_display == "N/A" and raw_res_str: res_text_display = raw_res_str
                except: pass
                items.append({ "name": r_series.get("显示器型号","N/A"), "panel": r_series.get("面板类型","未知"), "value": v, "size_numeric": size_n, "size_text": f"{size_n:.1f}\"" if size_n else "N/A\"", "refresh_numeric": ref_n, "refresh_text": f"{ref_n:.0f}Hz" if ref_n else "N/A Hz", "resolution_text": res_text_display, "resolution_numeric_value": res_val_numeric })
            
            # print(f"ChartWidget.setData: Processed {len(items)} items for metric '{metric_key}'") # DEBUG
            if not items: 
                self.data = []
                # print(f"ChartWidget.setData: No items for metric '{metric_key}', data cleared.") # DEBUG
            else:
                asc = self.config.get("lower_is_better", False) # Ensure default if key missing
                self.data = sorted(items, key=lambda x: x["value"], reverse=not asc)
                vs = [it["value"] for it in self.data]; self.max_value_for_bar = max(vs) if vs else 1
        
        self.adjustHeight() 


    def _sat(self, v, mi, ma, base=0.65, ran=0.35):
        if v is None: return base; 
        if ma == mi: return base + ran/2
        r = (v - mi) / (ma - mi); return base + max(0, min(1, r)) * ran

    def getSizeColor(self, v): sat = self._sat(v, self.min_size, self.max_size); return QColor.fromHslF(0.61, sat, 0.55, 1.0)
    def getRefreshColor(self, v): sat = self._sat(v, self.min_refresh, self.max_refresh, base=0.4, ran=0.2); return QColor.fromHslF(0.0, sat, 0.50, 1.0)
    def getResolutionColor(self, v_numeric): sat = self._sat(v_numeric, self.min_resolution_val, self.max_resolution_val, 0.65, 0.35); return QColor.fromHslF(0.33, sat, 0.55, 1.0) 

    def adjustHeight(self):
        n = len(self.data)
        scaler = self.EXPORT_FONT_SCALE_FACTOR if self._is_export_mode else 1.0
        
        rh = int(self.current_row_height * scaler) 
        th_title = int(self.current_base_title_height * scaler)
        
        pt = pb = int(self.screen_padding * scaler)
        total_h = th_title + n * rh + pt + pb
        if n == 0: total_h += rh 
        self.setMinimumHeight(int(total_h))
        self.update() # Ensure a repaint is triggered after height adjustment

    def paintEvent(self, event):
        # ... (paintEvent remains largely the same as previous version with label position logic)
        # Ensure all font creations and metric calculations use the scaled values based on self._is_export_mode
        super().paintEvent(event)
        p = QPainter(self);
        p.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)

        w = self.width()
        scaler = self.EXPORT_FONT_SCALE_FACTOR if self._is_export_mode else 1.0

        current_rh = int(self.current_row_height * scaler)
        current_title_h = int(self.current_base_title_height * scaler)
        current_pad = int(self.screen_padding * scaler)
        current_rank_w = int(self.screen_rank_width * scaler)

        _title_font = QFont(self.base_title_font.family(), int(self.base_title_font.pointSize() * scaler), self.base_title_font.weight())
        _rank_font = QFont(self.base_rank_font.family(), int(self.base_rank_font.pointSize() * scaler), self.base_rank_font.weight())
        _name_font = QFont(self.base_name_font.family(), int(self.base_name_font.pointSize() * scaler), self.base_name_font.weight())
        _sub_label_font = QFont(self.base_sub_label_font.family(), int(self.base_sub_label_font.pointSize() * scaler), self.base_sub_label_font.weight())
        _label_font = QFont(self.base_label_font.family(), int(self.base_label_font.pointSize() * scaler), self.base_label_font.weight())
        
        foot_font_point_size_float = _name_font.pointSize() * 0.75 
        foot_font_point_size_int = max(1, int(foot_font_point_size_float))
        _foot_font = QFont(_name_font.family(), foot_font_point_size_int, QFont.Weight.Normal)

        _name_text_top_padding = int(self.current_name_text_top_padding_abs * scaler)
        _gap_before_footnote = int(self.current_gap_before_footnote_abs * scaler)
        _gap_after_name_block = int((self.current_gap_after_name_block_abs_full if self.show_size_resolution or (self._is_export_mode and self.EXPORT_LAYOUT_PARAMS["show_size_resolution_export"]) else self.current_gap_after_name_block_abs_compact) * scaler)
        _gap_between_sub_label_lines = int(self.current_gap_between_sub_label_lines_abs * scaler)
        _sub_label_line_extra_padding = int(self.current_sub_label_line_extra_padding * scaler)
        _label_item_gap = int(self.label_item_gap * scaler)

        if not self.data or not self.config: # Check if self.config is also valid
            p.setPen(self.chart_empty_text_color); p.setFont(_title_font)
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "请先加载数据并选择指标.")
            return

        fm_name = QFontMetrics(_name_font)
        fm_sub_label = QFontMetrics(_sub_label_font)
        fm_foot = QFontMetrics(_foot_font) 
        
        max_nw = 0
        if self.data: max_nw = max(fm_name.horizontalAdvance(it["name"].split("（")[0].split("(")[0].strip()) for it in self.data)
        max_label_line1_w = 0; max_label_line2_w = 0
        if self.data:
            max_label_line1_w = max(fm_sub_label.horizontalAdvance(it["panel"]) + _label_item_gap + fm_sub_label.horizontalAdvance(it["refresh_text"]) for it in self.data )
            if self.show_size_resolution or (self._is_export_mode and self.EXPORT_LAYOUT_PARAMS["show_size_resolution_export"]): 
                max_label_line2_w = max(fm_sub_label.horizontalAdvance(it["size_text"]) + _label_item_gap + fm_sub_label.horizontalAdvance(it["resolution_text"]) for it in self.data )
        
        needed_text_w = max(max_nw, max_label_line1_w, max_label_line2_w) + int(20 * scaler) 
        max_info_allowable = int((w - current_pad*2) * 0.40)
        info_w = int(min(needed_text_w, float(max_info_allowable))) 

        bar_gap = int(10 * scaler)
        x_rank = current_pad
        x_info = current_pad + current_rank_w
        x_bar  = x_info + info_w + bar_gap
        
        est_lbl_val = f"{self.max_value_for_bar:.2f}{self.config.get('unit','')}"
        est_lbl = QFontMetrics(_label_font).horizontalAdvance(est_lbl_val) + int(20 * scaler)
        avail_bar_area = w - x_bar - current_pad
        bar_w = max(int(50 * scaler), min(avail_bar_area - est_lbl, (current_rank_w + info_w) * 3, info_w * 4))

        p.setPen(self.text_primary_color); p.setFont(_title_font)
        title_text = self.config.get("base_title", "图表")
        sort_suffix = " (越高越好)" if not self.config.get("lower_is_better", False) else " (越低越好)"
        full_title = title_text + sort_suffix
        p.drawText( QRectF(x_info, current_pad, w - current_pad*2 - x_info + current_pad, current_title_h), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, full_title )
        
        y_row_start = current_pad + current_title_h 

        for i, it in enumerate(self.data):
            y_cursor = y_row_start + _name_text_top_padding 

            p.setFont(_rank_font)
            p.setPen(self.text_primary_color)
            rank_text_height = QFontMetrics(_rank_font).height()
            
            rank_text_rect = QRectF(x_rank, y_cursor, current_rank_w - int(10*scaler), rank_text_height)
            p.drawText(rank_text_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight, str(i + 1))

            name_text_raw = it["name"]; mode_pattern = r'[（\(]([^）\)]+)[）\)]$'
            mode_match = re.search(mode_pattern, name_text_raw)
            main_name = name_text_raw; mode_text_for_footnote = ""
            if mode_match:
                full_parenthesized_mode = mode_match.group(0); mode_content = mode_match.group(1)
                mode_text_for_footnote = mode_content
                main_name = name_text_raw.replace(full_parenthesized_mode, "").strip()

            p.setFont(_name_font)
            p.setPen(self.text_primary_color)
            main_name_rect = QRectF(x_info, y_cursor, info_w - int(10*scaler), fm_name.height())
            p.drawText(main_name_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, main_name)
            y_cursor += fm_name.height() 

            if mode_text_for_footnote:
                y_cursor += _gap_before_footnote
                p.setFont(_foot_font)
                p.setPen(self.text_secondary_color)
                
                available_width_for_footnote = info_w - int(10*scaler) 
                elide_width = max(0, int(available_width_for_footnote))
                elided_mode_text = fm_foot.elidedText(mode_text_for_footnote, Qt.TextElideMode.ElideRight, elide_width)

                actual_elided_footnote_width = fm_foot.horizontalAdvance(elided_mode_text)
                footnote_rect = QRectF(x_info, y_cursor, actual_elided_footnote_width, fm_foot.height())
                p.drawText(footnote_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, elided_mode_text)
                y_cursor += fm_foot.height()

            y_cursor += _gap_after_name_block 

            p.setFont(_sub_label_font) 
            sub_label_line_height = fm_sub_label.height() + _sub_label_line_extra_padding

            panel_text_w = fm_sub_label.horizontalAdvance(it["panel"])
            p.setPen(PANEL_COLORS.get(it["panel"], QColor("grey")))
            label1_rect_panel = QRectF(x_info, y_cursor, panel_text_w, sub_label_line_height)
            p.drawText(label1_rect_panel, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, it["panel"])

            refresh_text_x = x_info + panel_text_w + _label_item_gap
            refresh_text_w = fm_sub_label.horizontalAdvance(it["refresh_text"])
            p.setPen(self.getRefreshColor(it["refresh_numeric"]))
            label1_rect_refresh = QRectF(refresh_text_x, y_cursor, refresh_text_w, sub_label_line_height)
            p.drawText(label1_rect_refresh, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, it["refresh_text"])
            y_cursor += sub_label_line_height

            if self.show_size_resolution or (self._is_export_mode and self.EXPORT_LAYOUT_PARAMS["show_size_resolution_export"]):
                y_cursor += _gap_between_sub_label_lines
                size_text_w = fm_sub_label.horizontalAdvance(it["size_text"])
                p.setPen(self.getSizeColor(it["size_numeric"]))
                label2_rect_size = QRectF(x_info, y_cursor, size_text_w, sub_label_line_height)
                p.drawText(label2_rect_size, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, it["size_text"])

                resolution_text_x = x_info + size_text_w + _label_item_gap
                resolution_text_w = fm_sub_label.horizontalAdvance(it["resolution_text"])
                p.setPen(self.getResolutionColor(it["resolution_numeric_value"]))
                label2_rect_res = QRectF(resolution_text_x, y_cursor, resolution_text_w, sub_label_line_height)
                p.drawText(label2_rect_res, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, it["resolution_text"])
                
            bh = 0.5 * current_rh; bar_y_pos = y_row_start + (current_rh-bh)/2 
            bg_rect = QRectF(x_bar, bar_y_pos, bar_w, bh)
            path_bg = QPainterPath(); path_bg.addRoundedRect(bg_rect, bh*0.1, bh*0.1)
            p.fillPath(path_bg, self.bar_background_color) 

            frac = it["value"]/self.max_value_for_bar if self.max_value_for_bar != 0 else 0; fw = frac * bar_w
            if fw > 0: 
                fr = QRectF(x_bar, bar_y_pos, fw, bh); grad = QLinearGradient(fr.topLeft(), fr.topRight())
                base_c = self.config.get("bar_color", DEFAULT_NEW_METRIC_COLOR) 
                grad.setColorAt(0, base_c.lighter(115)); grad.setColorAt(1, base_c.darker(115))
                path_f = QPainterPath(); path_f.addRoundedRect(fr, bh*0.1, bh*0.1); p.fillPath(path_f, QBrush(grad))
            
            lbl = f"{it['value']:.2f}{self.config.get('unit','')}"
            fm_lbl_val = QFontMetrics(_label_font)
            lbl_width = fm_lbl_val.horizontalAdvance(lbl)
            padding_inside_bar = int(5 * scaler)
            padding_outside_bar = int(8 * scaler)
            lx = 0 

            can_fit_inside = (fw > lbl_width + (2 * padding_inside_bar))

            if self.value_label_inside and can_fit_inside:
                lx = x_bar + fw - lbl_width - padding_inside_bar 
                text_color_for_inside_label = Qt.GlobalColor.white 
                bar_end_color = self.config.get("bar_color", DEFAULT_NEW_METRIC_COLOR).darker(115)
                luminance = 0.299 * bar_end_color.redF() + 0.587 * bar_end_color.greenF() + 0.114 * bar_end_color.blueF()
                if luminance > 0.5: 
                    text_color_for_inside_label = Qt.GlobalColor.black
                p.setPen(text_color_for_inside_label)
            else: 
                lx = x_bar + fw + padding_outside_bar
                p.setPen(self.text_primary_color)
            
            ly_val = bar_y_pos + (bh - fm_lbl_val.height()) / 2 + fm_lbl_val.ascent()
            p.setFont(_label_font) 
            p.drawText(int(lx), int(ly_val), lbl)
            
            y_row_start += current_rh 

        if self._is_export_mode: 
            fm_value_label = QFontMetrics(_label_font)
            max_value_label_w = 0
            last_item_fw = 0
            last_item_lbl_width = 0
            if self.data:
                last_item_val = self.data[-1]["value"]
                last_item_fw = (last_item_val / self.max_value_for_bar if self.max_value_for_bar !=0 else 0) * bar_w
                last_item_lbl_text = f"{last_item_val:.2f}{self.config.get('unit','')}"
                last_item_lbl_width = fm_value_label.horizontalAdvance(last_item_lbl_text)
            
            last_label_was_inside_and_fit = self.value_label_inside and (last_item_fw > last_item_lbl_width + (2 * padding_inside_bar))

            if last_label_was_inside_and_fit : 
                 _content_w = x_bar + bar_w + current_pad 
            else: 
                 max_value_label_w = fm_value_label.horizontalAdvance(f"{self.max_value_for_bar:.2f}{self.config.get('unit','')}") 
                 _content_w = x_bar + bar_w + padding_outside_bar + max_value_label_w + current_pad

            self._export_content_width = min(math.ceil(_content_w), w) 
        p.end()

    def getChartPixmap(self, target_width=None):
        # ... (getChartPixmap remains the same)
        original_show_size_res = self.show_size_resolution
        original_label_pos = self.value_label_inside 
        original_style_sheet = self.styleSheet()
        original_auto_fill = self.autoFillBackground()
        
        self._is_export_mode = True 
        self.setAutoFillBackground(False) 
        self.setStyleSheet("background:transparent;") 

        self.show_size_resolution = self.EXPORT_LAYOUT_PARAMS["show_size_resolution_export"]
        
        if self.EXPORT_LAYOUT_PARAMS["show_size_resolution_export"]:
            self.current_row_height = self.EXPORT_LAYOUT_PARAMS["row_height_full"]
        else:
            self.current_row_height = self.EXPORT_LAYOUT_PARAMS["row_height_compact"]
        self.current_base_title_height = self.EXPORT_LAYOUT_PARAMS["base_title_height"]

        self.adjustHeight() 
        
        render_export_height_scaled = self.minimumHeight() 
        render_export_width_unscaled = self.EXPORT_TARGET_WIDTH 
        
        dpr_export = 1.8 

        pixmap_width_device_pixels = int(render_export_width_unscaled * dpr_export)
        pixmap_height_device_pixels = int(render_export_height_scaled * dpr_export)

        if pixmap_width_device_pixels <= 0 or pixmap_height_device_pixels <= 0:
            pixmap_width_device_pixels = max(pixmap_width_device_pixels, int(1920 * dpr_export))
            pixmap_height_device_pixels = max(pixmap_height_device_pixels, int(1080 * dpr_export))

        pix = QPixmap(QSize(pixmap_width_device_pixels, pixmap_height_device_pixels))
        pix.setDevicePixelRatio(dpr_export)
        pix.fill(Qt.GlobalColor.transparent) 
        
        original_widget_size = self.size()
        self.resize(render_export_width_unscaled, render_export_height_scaled)

        painter = QPainter(pix); self.render(painter); painter.end()
        
        content_width_scaled = getattr(self, '_export_content_width', render_export_width_unscaled * self.EXPORT_FONT_SCALE_FACTOR) 
        crop_width_device_pixels = int(content_width_scaled * dpr_export) 
        crop_width_device_pixels = min(crop_width_device_pixels, pixmap_width_device_pixels)
        
        final_pixmap = pix.copy(0, 0, crop_width_device_pixels, pixmap_height_device_pixels)
        final_pixmap.setDevicePixelRatio(dpr_export)
        
        self.show_size_resolution = original_show_size_res
        self.value_label_inside = original_label_pos 
        self.setStyleSheet(original_style_sheet)
        self.setAutoFillBackground(original_auto_fill)

        if self.show_size_resolution:
            self.current_row_height = self.EXPORT_LAYOUT_PARAMS["row_height_full"] 
        else:
            self.current_row_height = self.EXPORT_LAYOUT_PARAMS["row_height_compact"]
        self.current_base_title_height = self.EXPORT_LAYOUT_PARAMS["base_title_height"]


        self._is_export_mode = False 
        self.resize(original_widget_size) 
        self.adjustHeight() 
        return final_pixmap


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_theme_name = "dark" 
        self.data_frame = None
        self.known_columns = ["显示器型号", "面板类型", "显示器尺寸", "刷新率", "分辨率"] 

        self.setWindowTitle("显示器天梯图生成器")
        self.setGeometry(100, 100, 1400, 900) 

        self.init_ui() 
        self.apply_stylesheet(self.current_theme_name) 
        
        theme_colors = THEMES[self.current_theme_name]
        self.chart_widget.set_theme_colors( 
            theme_colors["text_primary"],
            theme_colors["text_secondary"],
            theme_colors["chart_empty_text"],
            theme_colors["chart_bar_background"]
        )
        self.statusBar().showMessage("请加载 CSV 文件。")
        self.populate_metric_combo()
        self.on_scheme_change(self.scheme_combo.currentText()) 
        self.chart_widget.setShowSizeResolution(self.show_details_checkbox.isChecked())
        self.chart_widget.setValueLabelPosition(self.label_pos_checkbox.isChecked())


    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        window_layout = QVBoxLayout(main_widget)
        window_layout.setContentsMargins(0,0,0,0) 
        window_layout.setSpacing(0) 

        app_bar_widget = self.create_app_bar()
        window_layout.addWidget(app_bar_widget)

        control_panel_widget = self.create_control_panel()
        window_layout.addWidget(control_panel_widget)
        
        self.chart_widget = ChartWidget(self) 
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.chart_widget)
        self.scroll_area.setObjectName("ChartScrollArea") 
        window_layout.addWidget(self.scroll_area, 1) 

        self.setStatusBar(QStatusBar())
        self.statusBar().setObjectName("AppStatusBar")


    def create_app_bar(self):
        app_bar = QWidget()
        app_bar.setObjectName("AppBar")
        app_bar_layout = QHBoxLayout(app_bar)
        app_bar_layout.setContentsMargins(15, 5, 15, 5) 
        app_bar_layout.setSpacing(10)

        title_label = QLabel("显示器天梯图生成器")
        title_label.setObjectName("AppBarTitle")
        app_bar_layout.addWidget(title_label)

        app_bar_layout.addStretch(1)

        self.btn_load_csv = QPushButton("加载 CSV") 
        self.btn_load_csv.clicked.connect(self.load_csv)
        self.btn_load_csv.setObjectName("AppBarButton")
        app_bar_layout.addWidget(self.btn_load_csv)

        self.btn_save_current_png = QPushButton("导出当前") 
        self.btn_save_current_png.clicked.connect(self.save_png)
        self.btn_save_current_png.setEnabled(False)
        self.btn_save_current_png.setObjectName("AppBarButton")
        app_bar_layout.addWidget(self.btn_save_current_png)
        
        self.btn_save_all_png = QPushButton("导出全部") 
        self.btn_save_all_png.clicked.connect(self.save_all_png)
        self.btn_save_all_png.setEnabled(False)
        self.btn_save_all_png.setObjectName("AppBarButton")
        app_bar_layout.addWidget(self.btn_save_all_png)

        self.theme_toggle_button = QToolButton()
        self.theme_toggle_button.setObjectName("ThemeToggleButton") 
        self.update_theme_toggle_button_icon() 
        self.theme_toggle_button.clicked.connect(self.toggle_theme_and_button)
        app_bar_layout.addWidget(self.theme_toggle_button)

        return app_bar

    def update_theme_toggle_button_icon(self):
        if not hasattr(self, 'theme_toggle_button'): return
        if self.current_theme_name == "dark":
            self.theme_toggle_button.setText("☀️") 
        else:
            self.theme_toggle_button.setText("🌙") 
        font = self.theme_toggle_button.font()
        font.setPointSize(14) 
        self.theme_toggle_button.setFont(font)


    def toggle_theme_and_button(self):
        if self.current_theme_name == "dark":
            self.switch_theme("light")
        else:
            self.switch_theme("dark")
        

    def create_control_panel(self):
        control_panel = QWidget()
        control_panel.setObjectName("ControlPanel")
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(15, 10, 15, 10) 
        control_layout.setSpacing(10) 

        control_layout.addWidget(QLabel("指标:"))
        self.metric_combo = QComboBox()
        self.metric_combo.currentTextChanged.connect(self.on_metric_selected)
        self.metric_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        control_layout.addWidget(self.metric_combo, 2) 

        control_layout.addWidget(QLabel("排序:"))
        self.sort_order_combo = QComboBox()
        self.sort_order_combo.addItems(["越高越好", "越低越好"])
        self.sort_order_combo.setEnabled(False)
        self.sort_order_combo.currentIndexChanged.connect(self.on_sort_order_changed)
        control_layout.addWidget(self.sort_order_combo, 1)

        control_layout.addWidget(QLabel("单位:"))
        self.unit_input = QLineEdit()
        self.unit_input.setPlaceholderText("例如: %, ms, ΔE")
        self.unit_input.setEnabled(False)
        self.unit_input.editingFinished.connect(self.on_unit_changed)
        control_layout.addWidget(self.unit_input, 1)
        
        control_layout.addWidget(QLabel("配色:"))
        self.scheme_combo = QComboBox()
        self.scheme_combo.addItems(COLOR_SCHEMES.keys())
        self.scheme_combo.currentTextChanged.connect(self.on_scheme_change)
        control_layout.addWidget(self.scheme_combo, 1)

        self.show_details_checkbox = QCheckBox("显示尺寸和分辨率")
        self.show_details_checkbox.setChecked(False)
        self.show_details_checkbox.setEnabled(False)
        self.show_details_checkbox.stateChanged.connect(self.on_show_details_changed)
        control_layout.addWidget(self.show_details_checkbox)

        self.label_pos_checkbox = QCheckBox("数值标签内显")
        self.label_pos_checkbox.setChecked(False) 
        self.label_pos_checkbox.setEnabled(False)
        self.label_pos_checkbox.stateChanged.connect(self.on_label_pos_changed)
        control_layout.addWidget(self.label_pos_checkbox)
        
        control_layout.addStretch(1) 

        return control_panel

    def on_label_pos_changed(self, state):
        if self.chart_widget:
            self.chart_widget.setValueLabelPosition(state == Qt.CheckState.Checked.value)


    def switch_theme(self, theme_name):
        if theme_name != self.current_theme_name:
            self.current_theme_name = theme_name
            self.apply_stylesheet(theme_name) 
            
            theme_colors = THEMES[self.current_theme_name]
            if hasattr(self, 'chart_widget') and self.chart_widget:
                self.chart_widget.set_theme_colors(
                    theme_colors["text_primary"],
                    theme_colors["text_secondary"],
                    theme_colors["chart_empty_text"],
                    theme_colors["chart_bar_background"] 
                )
            
            if hasattr(self, 'theme_toggle_button') and self.theme_toggle_button:
                self.update_theme_toggle_button_icon()

            if hasattr(self, 'statusBar') and self.statusBar():
                self.statusBar().setStyleSheet(f"""
                    QStatusBar {{
                        background-color: {theme_colors["widget_background"]};
                        color: {theme_colors["text_secondary"]};
                    }}
                    QStatusBar::item {{
                        border: none; 
                    }}
                """)


    def apply_stylesheet(self, theme_name):
        theme = THEMES[theme_name]
        common_stylesheet = f"""
            QMainWindow {{
                background-color: {theme["background"]};
            }}
            QWidget {{
                color: {theme["text_primary"]};
                font-family: "Source Han Sans CN", "Microsoft YaHei", sans-serif; 
                font-size: 13px;
            }}
            QLabel {{
                background-color: transparent; 
            }}
            QPushButton, QToolButton {{ 
                background-color: {theme["accent"]};
                color: {theme["button_text"]};
                border: 1px solid {theme["accent"]};
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover, QToolButton:hover {{
                background-color: {QColor(theme["accent"]).lighter(115).name()};
            }}
            QPushButton:pressed, QToolButton:pressed {{
                background-color: {QColor(theme["accent"]).darker(115).name()};
            }}
            QPushButton:disabled {{
                background-color: {theme["widget_background"]};
                color: {theme["disabled_text"]};
                border-color: {theme["border"]};
            }}
            QComboBox {{
                background-color: {theme["widget_background"]};
                border: 1px solid {theme["border"]};
                padding: 5px;
                border-radius: 4px;
                min-height: 20px; 
            }}
            QComboBox:disabled {{
                background-color: {QColor(theme["widget_background"]).darker(105).name()};
                color: {theme["disabled_text"]};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                 image: url(none); 
            }}
            QComboBox QAbstractItemView {{ 
                background-color: {theme["widget_background"]};
                border: 1px solid {theme["border"]};
                selection-background-color: {theme["accent"]};
                selection-color: {theme["button_text"]};
                color: {theme["text_primary"]}; 
                outline: none; 
            }}

            QLineEdit {{
                background-color: {theme["widget_background"]};
                border: 1px solid {theme["border"]};
                padding: 6px;
                border-radius: 4px;
            }}
            QLineEdit:disabled {{
                background-color: {QColor(theme["widget_background"]).darker(105).name()};
                color: {theme["disabled_text"]};
            }}
            QCheckBox {{
                spacing: 5px; 
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {theme["border"]};
                border-radius: 3px;
                background-color: {theme["widget_background"]};
            }}
            QCheckBox::indicator:checked {{
                background-color: {theme["accent"]};
                border-color: {theme["accent"]};
            }}
             QCheckBox::indicator:disabled {{
                background-color: {QColor(theme["widget_background"]).darker(105).name()};
                border-color: {QColor(theme["border"]).darker(105).name()};
            }}
            QScrollArea {{
                border: none; 
                 background-color: {theme["widget_background"]}; 
            }}
            #ChartScrollArea > QWidget {{ 
                 background-color: {theme["widget_background"]};
            }}
             #ChartScrollArea > QWidget > QWidget {{ 
                 background-color: {theme["widget_background"]};
            }}
            QScrollBar:vertical {{
                border: none;
                background: {theme["widget_background"]};
                width: 10px;
                margin: 0px 0px 0px 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {QColor(theme["border"]).lighter(120).name()};
                min-height: 20px;
                border-radius: 5px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0px;
                width: 0px;
            }}
             QScrollBar:horizontal {{
                border: none;
                background: {theme["widget_background"]};
                height: 10px;
                margin: 0px 0px 0px 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: {QColor(theme["border"]).lighter(120).name()};
                min-width: 20px;
                border-radius: 5px;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                border: none;
                background: none;
                height: 0px;
                width: 0px;
            }}
        """
        
        specific_stylesheet = f"""
            #AppBar {{
                background-color: {theme["header_background"]};
            }}
            #AppBarTitle {{
                font-size: 18px;
                font-weight: bold;
                color: {theme["text_primary"]};
            }}
            #AppBarButton {{ 
                padding: 6px 10px; 
                font-size: 13px;
            }}
            #ThemeToggleButton {{ 
                padding: 6px 8px; 
                font-size: 14px; 
            }}
            #ControlPanel {{
                background-color: {theme["control_panel_background"]};
                border-bottom: 1px solid {theme["border"]}; 
            }}
            #AppStatusBar {{
                background-color: {theme["widget_background"]};
                color: {theme["text_secondary"]};
            }}
            #AppStatusBar::item {{
                border: none; 
            }}
        """
        self.setStyleSheet(common_stylesheet + specific_stylesheet)
        if hasattr(self, 'chart_widget') and self.chart_widget: 
             self.chart_widget.update()


    def on_show_details_changed(self, state):
        if self.chart_widget:
            self.chart_widget.setShowSizeResolution(state == Qt.CheckState.Checked.value)

    def populate_metric_combo(self):
        current_metric = self.metric_combo.currentText()
        self.metric_combo.blockSignals(True); self.metric_combo.clear()
        self.metric_combo.addItems(CHART_CONFIG.keys())
        if current_metric in CHART_CONFIG.keys(): self.metric_combo.setCurrentText(current_metric)
        elif self.metric_combo.count() > 0: self.metric_combo.setCurrentIndex(0) 
        self.metric_combo.blockSignals(False)
        self.on_metric_selected(self.metric_combo.currentText()) # Trigger update for initial item

    def load_csv(self):
        global CHART_CONFIG
        fn, _ = QFileDialog.getOpenFileName(self, "打开 CSV", "", "CSV Files (*.csv)")
        if not fn: return
        
        original_chart_config_keys = set(CHART_CONFIG.keys()); success = False
        loaded_df = None 

        for enc in ('utf-8', 'gbk', 'gb2312', 'utf-8-sig'):
            try:
                df_attempt = pd.read_csv(fn, encoding=enc, on_bad_lines='skip', dtype=str)
                df_processed = df_attempt.rename(columns=lambda x: x.strip())
                if '显示器型号' not in df_processed.columns:
                    continue

                current_chart_config_keys = set(CHART_CONFIG.keys()) 
                for col_name in df_processed.columns:
                    if col_name not in self.known_columns and col_name not in current_chart_config_keys:
                        CHART_CONFIG[col_name] = {"csv_column": col_name, "unit": "", "lower_is_better": False,
                                                  "bar_color": DEFAULT_NEW_METRIC_COLOR, "base_title": col_name}
                
                cols_to_clean = [cfg["csv_column"] for cfg in CHART_CONFIG.values()] + ["显示器尺寸", "刷新率"]
                for col_name_to_clean in list(set(cols_to_clean)):
                    if col_name_to_clean in df_processed.columns:
                        df_processed[col_name_to_clean] = df_processed[col_name_to_clean].astype(str).str.replace(r'[^\d\.\-]', '', regex=True)
                        df_processed[col_name_to_clean] = pd.to_numeric(df_processed[col_name_to_clean].replace('', pd.NA), errors='coerce')
                
                loaded_df = df_processed.copy() 
                success = True; break 
            except Exception as e: 
                print(f"Error loading CSV with encoding {enc}: {e}")
        
        if success and loaded_df is not None:
            self.data_frame = loaded_df.dropna(subset=['显示器型号'])
            self.data_frame = self.data_frame[self.data_frame['显示器型号'].astype(str).str.strip() != '']
            
            if self.data_frame.empty: 
                self.statusBar().showMessage(f"加载成功，但清理后数据为空或'显示器型号'无效。")
                self.enable_controls(False)
                self.chart_widget.setData(None, None)
                CHART_CONFIG = {k:v for k,v in CHART_CONFIG.items() if k in original_chart_config_keys} 
                self.populate_metric_combo() 
            else: 
                self.statusBar().showMessage(f"加载 {len(self.data_frame)} 条有效记录 (使用编码 {enc if success else '未知'})")
                self.enable_controls(True)
                self.populate_metric_combo() 
                self.on_scheme_change(self.scheme_combo.currentText(), force_update_new_metrics=True)
                # self.chart_widget.setShowSizeResolution(self.show_details_checkbox.isChecked()) # Done in on_metric_selected via update_chart
                # self.update_chart() # Done by populate_metric_combo -> on_metric_selected
        else: 
            if not success: self.statusBar().showMessage("加载失败，请检查文件编码或 CSV 格式。")
            else: self.statusBar().showMessage("加载成功但未能正确处理数据。")
            self.data_frame = None
            self.enable_controls(False)
            self.chart_widget.setData(None, None)
            CHART_CONFIG = {k:v for k,v in CHART_CONFIG.items() if k in original_chart_config_keys}
            self.populate_metric_combo()
        
        # Ensure these are set based on current state after loading or failing
        self.chart_widget.setShowSizeResolution(self.show_details_checkbox.isChecked())
        self.chart_widget.setValueLabelPosition(self.label_pos_checkbox.isChecked())


    def enable_controls(self, enabled):
        self.sort_order_combo.setEnabled(enabled)
        self.unit_input.setEnabled(enabled)
        self.show_details_checkbox.setEnabled(enabled)
        self.label_pos_checkbox.setEnabled(enabled) 
        self.btn_save_current_png.setEnabled(enabled)
        self.btn_save_all_png.setEnabled(enabled)
        if not enabled:
            self.show_details_checkbox.setChecked(False)
            self.label_pos_checkbox.setChecked(False)


    def on_metric_selected(self, metric_key):
        # print(f"MainWindow.on_metric_selected: '{metric_key}'") # DEBUG
        is_metric_valid = bool(metric_key and metric_key in CHART_CONFIG)
        self.sort_order_combo.setEnabled(is_metric_valid and self.data_frame is not None)
        self.unit_input.setEnabled(is_metric_valid and self.data_frame is not None)

        if not metric_key:
            self.unit_input.setText("")
            self.update_chart(None) # Clear chart if metric becomes empty
            return

        if not is_metric_valid:
            self.update_chart(metric_key) # Attempt to update, will likely clear chart
            return

        config = CHART_CONFIG[metric_key]
        self.sort_order_combo.blockSignals(True)
        self.sort_order_combo.setCurrentIndex(1 if config.get("lower_is_better", False) else 0)
        self.sort_order_combo.blockSignals(False)

        self.unit_input.blockSignals(True)
        self.unit_input.setText(config.get("unit", ""))
        self.unit_input.blockSignals(False)

        self.update_chart(metric_key) 

    def on_sort_order_changed(self, index):
        metric_key_from_combo = self.metric_combo.currentText()
        # print(f"MainWindow.on_sort_order_changed for: '{metric_key_from_combo}'") # DEBUG
        if metric_key_from_combo and metric_key_from_combo in CHART_CONFIG:
            new_lower_is_better = (index == 1)
            if CHART_CONFIG[metric_key_from_combo].get("lower_is_better") != new_lower_is_better:
                CHART_CONFIG[metric_key_from_combo]["lower_is_better"] = new_lower_is_better
                self.update_chart(metric_key_from_combo)


    def on_unit_changed(self):
        metric_key = self.metric_combo.currentText()
        if metric_key and metric_key in CHART_CONFIG:
            CHART_CONFIG[metric_key]["unit"] = self.unit_input.text()
            self.update_chart(metric_key) 

    def update_chart(self, metric_to_display=None): 
        # print(f"MainWindow.update_chart called for: {metric_to_display}") # DEBUG
        if self.data_frame is not None and not self.data_frame.empty:
            current_metric = metric_to_display if metric_to_display is not None else self.metric_combo.currentText()
            if current_metric in CHART_CONFIG:
                self.chart_widget.setData(self.data_frame, current_metric)
                self.chart_widget.setValueLabelPosition(self.label_pos_checkbox.isChecked())
                self.chart_widget.setShowSizeResolution(self.show_details_checkbox.isChecked()) # Ensure this is also updated
            else:
                self.chart_widget.setData(None, None)
        else:
            self.chart_widget.setData(None, None) 

    def save_png(self):
        if not self.chart_widget.metric_key or self.chart_widget.data is None or not self.chart_widget.data:
            self.statusBar().showMessage("请先选择指标并加载有效数据。"); return
        safe_metric_key = re.sub(r'[^\w\s-]', '', self.chart_widget.metric_key).strip().replace(' ', '_')
        default_filename = f"{safe_metric_key or 'chart'}.png"
        fn, _ = QFileDialog.getSaveFileName(self, "保存 PNG", default_filename, "PNG Files (*.png)")
        if fn:
            pix = self.chart_widget.getChartPixmap()
            if pix.save(fn, "PNG"):
                self.statusBar().showMessage(f"已保存 {fn}")
            else: self.statusBar().showMessage("保存失败。")

    def save_all_png(self):
        if self.data_frame is None or self.data_frame.empty:
            self.statusBar().showMessage("请先加载数据。"); return

        folder = QFileDialog.getExistingDirectory(self, "选择保存文件夹")
        if not folder:
            return

        original_metric = self.metric_combo.currentText()
        num_exported = 0
        for metric_key_to_export in CHART_CONFIG.keys(): # Iterate over all known config keys
            # Ensure this metric is valid and has data processable from the current dataframe
            if metric_key_to_export not in CHART_CONFIG or CHART_CONFIG[metric_key_to_export].get("csv_column", "") not in self.data_frame.columns:
                print(f"Skipping export for '{metric_key_to_export}': column not in DataFrame or config missing.")
                continue

            # Temporarily set the application to this metric for rendering
            self.metric_combo.blockSignals(True)
            self.metric_combo.setCurrentText(metric_key_to_export)
            # Manually update config for sort order and unit based on this metric for the chart_widget
            config = CHART_CONFIG[metric_key_to_export]
            self.sort_order_combo.setCurrentIndex(1 if config.get("lower_is_better", False) else 0)
            self.unit_input.setText(config.get("unit", ""))
            self.metric_combo.blockSignals(False)

            self.chart_widget.setData(self.data_frame, metric_key_to_export) 
            QApplication.processEvents() # Allow UI to update if needed for setData

            if self.chart_widget.data and self.chart_widget.config: # Check if chart widget has data for this metric
                safe_metric_key_filename = re.sub(r'[^\w\s-]', '', metric_key_to_export).strip().replace(' ', '_')
                filename = f"{folder}/{safe_metric_key_filename or 'chart'}.png" # Removed num_exported from filename for clarity
                pix = self.chart_widget.getChartPixmap()
                if pix.save(filename, "PNG"):
                    num_exported += 1
                    self.statusBar().showMessage(f"正在导出: {metric_key_to_export} ({num_exported}/{len(CHART_CONFIG)})")
                    QApplication.processEvents() 
                else:
                    print(f"Failed to save {filename}")
            else:
                print(f"Skipping PNG export for {metric_key_to_export} due to no displayable data in chart widget.")
        
        # Restore original metric in UI
        self.metric_combo.blockSignals(True)
        self.metric_combo.setCurrentText(original_metric)
        if original_metric in CHART_CONFIG: # Restore sort and unit for the original metric
            config = CHART_CONFIG[original_metric]
            self.sort_order_combo.setCurrentIndex(1 if config.get("lower_is_better", False) else 0)
            self.unit_input.setText(config.get("unit", ""))
        self.metric_combo.blockSignals(False)
        self.update_chart(original_metric) # Refresh chart to original state

        self.statusBar().showMessage(f"已成功导出 {num_exported} 个图表到 {folder}")


    def on_scheme_change(self, name, force_update_new_metrics=False):
        global PANEL_COLORS, CHART_CONFIG
        scheme = COLOR_SCHEMES.get(name, COLOR_SCHEMES["默认"])
        
        for k_metric, config_metric in CHART_CONFIG.items():
            if "bar_colors" in scheme and k_metric in scheme["bar_colors"]:
                config_metric["bar_color"] = scheme["bar_colors"][k_metric]
            elif k_metric not in COLOR_SCHEMES["默认"]["bar_colors"]: 
                if "bar_color" not in config_metric or force_update_new_metrics: 
                     config_metric["bar_color"] = DEFAULT_NEW_METRIC_COLOR
        
        if "panel_colors" in scheme:
            current_scheme_panel_colors = scheme["panel_colors"]
            updated_panel_colors = copy.deepcopy(DEFAULT_PANEL_COLORS)
            updated_panel_colors.update(current_scheme_panel_colors)
            PANEL_COLORS = updated_panel_colors
        else: 
            PANEL_COLORS = copy.deepcopy(DEFAULT_PANEL_COLORS)

        if self.chart_widget:
            current_chart_metric = self.chart_widget.metric_key # Use chart's current metric
            if current_chart_metric and current_chart_metric in CHART_CONFIG:
                 self.chart_widget.config = copy.deepcopy(CHART_CONFIG[current_chart_metric]) # Update with deepcopy
            self.chart_widget.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("MonitorRankingApp")
    app.setOrganizationName("MyCompany") 
    
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

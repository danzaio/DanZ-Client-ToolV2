"""
DanZ Client Tool - Modern Dark Theme Styles
"""

# Color Palette (Zinc/Cyan Scheme)
COLORS = {
    "background": "#09090b",    # Zinc 950
    "surface": "#18181b",       # Zinc 900
    "surface_hover": "#27272a", # Zinc 800
    "border": "#27272a",        # Zinc 800
    "text": "#f4f4f5",          # Zinc 100
    "text_dim": "#a1a1aa",      # Zinc 400
    "primary": "#06b6d4",       # Cyan 500
    "primary_hover": "#0891b2", # Cyan 600
    "danger": "#ef4444",        # Red 500
    "danger_hover": "#dc2626",  # Red 600
    "success": "#22c55e",       # Green 500
    "overlay": "rgba(9, 9, 11, 0.8)",
}

# Main Application Stylesheet
STYLESHEET = f"""
    /* Global Reset */
    * {{
        font-family: 'Segoe UI', sans-serif;
        font-size: 13px;
        color: {COLORS['text']};
        outline: none;
    }}

    QMainWindow, QDialog {{
        background-color: {COLORS['background']};
        border: 1px solid {COLORS['border']};
    }}
    
    QWidget {{
        background-color: transparent;
    }}

    /* GroupBox (Card) */
    QGroupBox {{
        background-color: {COLORS['surface']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        margin-top: 24px;
        font-weight: bold;
        font-size: 14px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 4px 0px;
        color: {COLORS['text']};
        background-color: transparent;
    }}

    /* Buttons */
    QPushButton {{
        background-color: {COLORS['surface']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 8px 16px;
        color: {COLORS['text']};
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {COLORS['surface_hover']};
        border-color: {COLORS['text_dim']};
    }}
    QPushButton:pressed {{
        background-color: {COLORS['border']};
    }}
    
    QPushButton[primary="true"] {{
        background-color: {COLORS['primary']};
        border: 1px solid {COLORS['primary']};
        color: #fff;
    }}
    QPushButton[primary="true"]:hover {{
        background-color: {COLORS['primary_hover']};
        border-color: {COLORS['primary_hover']};
    }}
    
    QPushButton[danger="true"] {{
        background-color: transparent;
        border: 1px solid {COLORS['danger']};
        color: {COLORS['danger']};
    }}
    QPushButton[danger="true"]:hover {{
        background-color: {COLORS['danger']};
        color: #fff;
    }}

    /* Inputs */
    QLineEdit, QSpinBox, QComboBox {{
        background-color: {COLORS['background']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 6px 10px;
        color: {COLORS['text']};
        selection-background-color: {COLORS['primary']};
    }}
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
        border: 1px solid {COLORS['primary']};
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    QComboBox::down-arrow {{
        image: none; /* Can replace with icon */
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid {COLORS['text_dim']};
        margin-right: 8px;
    }}

    /* ScrollBar */
    QScrollBar:vertical {{
        border: none;
        background: {COLORS['background']};
        width: 8px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS['border']};
        min-height: 20px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {COLORS['text_dim']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    /* CheckBox */
    QCheckBox {{
        spacing: 8px;
        color: {COLORS['text_dim']};
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 1px solid {COLORS['border']};
        border-radius: 4px;
        background: {COLORS['background']};
    }}
    QCheckBox::indicator:checked {{
        background-color: {COLORS['primary']};
        border-color: {COLORS['primary']};
        image: url("resources/check.png"); /* Optional if we had icons */
    }}
    QCheckBox:checked {{
        color: {COLORS['text']};
    }}

    /* Sliders */
    QSlider::groove:horizontal {{
        border: 1px solid {COLORS['border']};
        height: 4px;
        background: {COLORS['surface']};
        margin: 2px 0;
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: {COLORS['primary']};
        border: 1px solid {COLORS['primary']};
        width: 14px;
        height: 14px;
        margin: -6px 0;
        border-radius: 7px;
    }}
    
    /* Table/Tree */
    QTreeWidget, QListWidget {{
        background-color: {COLORS['surface']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
    }}
    QHeaderView::section {{
        background-color: {COLORS['background']};
        color: {COLORS['text_dim']};
        padding: 8px;
        border: none;
        border-bottom: 1px solid {COLORS['border']};
        font-weight: 600;
    }}
"""

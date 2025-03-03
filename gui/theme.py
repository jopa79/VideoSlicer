"""Theme management for the VideoSlicer application."""
import tkinter as tk
from tkinter import ttk

# Define color scheme for custom elements
COLORS = {
    'primary': '#0078d7',       # Blue
    'primary_light': '#429ce3',
    'primary_dark': '#005a9e',
    'secondary': '#6c757d',     # Gray
    'success': '#28a745',       # Green
    'warning': '#ffc107',       # Yellow
    'error': '#dc3545',         # Red
    'background': '#f8f9fa',    # Light gray
    'card': '#ffffff',          # White
    'text': '#212529',          # Dark gray
    'text_secondary': '#6c757d'  # Medium gray
}

def apply_custom_styles():
    """Apply custom styles beyond what the theme provides."""
    style = ttk.Style()
    
    # Card style for frames that should look like cards
    style.configure('Card.TFrame', relief='flat')
    
    # Header styles
    style.configure('Header.TLabel', font=('', 16, 'bold'))
    style.configure('Subheader.TLabel', font=('', 12))
    
    # Card title
    style.configure('CardTitle.TLabel', font=('', 12, 'bold'))
    
    # Primary button with slightly larger text and padding
    style.configure('Primary.TButton', font=('', 10))
    
    # Success button
    style.configure('Success.TButton', font=('', 10))
    
    # Info text
    style.configure('Info.TLabel', foreground=COLORS['text_secondary'])
    
    return style

def get_theme_mode():
    """Get the current theme mode (light or dark)."""
    try:
        import sv_ttk
        return sv_ttk.get_theme()
    except ImportError:
        return "dark"  # Default to dark theme

def toggle_theme_mode(root):
    """Toggle between light and dark theme."""
    try:
        import sv_ttk
        current_theme = sv_ttk.get_theme()
        new_theme = "dark" if current_theme == "light" else "light"
        sv_ttk.set_theme(new_theme)
        return new_theme
    except ImportError:
        return "dark"  # Default to dark theme if sv_ttk is not available
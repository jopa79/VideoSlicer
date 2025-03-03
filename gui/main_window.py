"""GUI for the video slicer with a modern design using Sun Valley theme."""
import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading
from PIL import Image, ImageTk
import webbrowser
import platform
import subprocess

from core.video_processor import VideoProcessor
from utils import check_ffmpeg_installed, get_free_disk_space, format_file_size, get_videos_folder, create_thumbnail, format_time
from config import (
    DEFAULT_SEQUENCE_LENGTH, 
    DEFAULT_SCENE_THRESHOLD,
    DEFAULT_NUM_SEQUENCES,
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_QUALITY,
    OUTPUT_FORMATS,
    QUALITY_SETTINGS
)
from constants import (
    VIDEO_EXTENSIONS, 
    WINDOW_WIDTH, 
    WINDOW_HEIGHT,
    APP_NAME,
    APP_VERSION,
    MAX_ANALYSIS_DURATION
)
from gui.theme import COLORS, apply_custom_styles, get_theme_mode, toggle_theme_mode

class VideoSlicerGUI:
    """Modern GUI for the VideoSlicer application."""
    
    def __init__(self, root, config_manager=None, i18n=None):
        """Initialize the GUI.
        
        Args:
            root: The tkinter root window.
            config_manager: Configuration manager instance.
            i18n: Internationalization instance.
        """
        self.root = root
        self.config_manager = config_manager
        
        # Set window properties
        self.root.title(APP_NAME)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(800, 600)
        
        # Apply custom styles
        self.style = apply_custom_styles()
        
        # Set default folders
        self.default_input_folder = get_videos_folder()
        self.default_output_folder = ""
        
        # Create the video processor
        self.processor = VideoProcessor()
        
        # Create variables
        self.input_path_var = tk.StringVar()
        self.output_path_var = tk.StringVar()
        self.sequence_length_var = tk.IntVar(value=DEFAULT_SEQUENCE_LENGTH)
        self.num_sequences_var = tk.IntVar(value=DEFAULT_NUM_SEQUENCES)
        self.threshold_var = tk.DoubleVar(value=DEFAULT_SCENE_THRESHOLD)
        self.output_format_var = tk.StringVar(value=DEFAULT_OUTPUT_FORMAT)
        self.quality_var = tk.StringVar(value=DEFAULT_QUALITY)
        self.progress_var = tk.DoubleVar(value=0)
        self.status_var = tk.StringVar(value="Ready to process videos")
        self.description_var = tk.StringVar()
        
        # Thumbnail image
        self.thumbnail_image = None
        
        # Create the GUI
        self.create_widgets()
        
        # Check FFmpeg on startup
        self.check_ffmpeg()
        
    def check_ffmpeg(self):
        """Check if FFmpeg is installed and show a message if not."""
        if not check_ffmpeg_installed():
            messagebox.showerror(
                "FFmpeg Not Found", 
                "FFmpeg is required but not found on your system. Please install FFmpeg to use this application."
            )
            # Add a download link
            result = messagebox.askyesno(
                "Download FFmpeg",
                "Would you like to visit the FFmpeg download page?"
            )
            if result:
                webbrowser.open("https://ffmpeg.org/download.html")
        
    def create_widgets(self):
        """Create the GUI widgets with a modern design."""
        # Main container with padding
        self.main_container = ttk.Frame(self.root, padding=20)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header with app title and theme toggle
        header_frame = ttk.Frame(self.main_container)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # App title
        ttk.Label(
            header_frame, 
            text=APP_NAME, 
            style="Header.TLabel"
        ).pack(side=tk.LEFT)
        
        # Version
        ttk.Label(
            header_frame, 
            text=f"v{APP_VERSION}", 
            style="Subheader.TLabel"
        ).pack(side=tk.LEFT, padx=(10, 0), pady=(8, 0))
        
        # Theme toggle button
        self.theme_button = ttk.Button(
            header_frame,
            text="☀️" if get_theme_mode() == "dark" else "🌙",
            command=self.toggle_theme,
            width=3
        )
        self.theme_button.pack(side=tk.RIGHT)
        
        # Create a two-column layout
        content_frame = ttk.Frame(self.main_container)
        content_frame.pack(fill=tk.BOTH, expand=True)
        content_frame.columnconfigure(0, weight=3)
        content_frame.columnconfigure(1, weight=2)
        
        # Left column - Input/Output and Parameters
        left_column = ttk.Frame(content_frame)
        left_column.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Right column - Preview and Progress
        right_column = ttk.Frame(content_frame)
        right_column.grid(row=0, column=1, sticky="nsew")
        
        # ===== LEFT COLUMN =====
        
        # Input/Output Card
        io_card = ttk.LabelFrame(left_column, text="Input & Output", padding=15)
        io_card.pack(fill=tk.X, pady=(0, 15))
        
        # Input video
        input_frame = ttk.Frame(io_card)
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="Input Video:").pack(anchor="w")
        
        input_browse_frame = ttk.Frame(input_frame)
        input_browse_frame.pack(fill=tk.X, pady=5)
        
        ttk.Entry(
            input_browse_frame, 
            textvariable=self.input_path_var
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(
            input_browse_frame, 
            text="Browse", 
            command=self.browse_input
        ).pack(side=tk.RIGHT)
        
        # Output folder
        output_frame = ttk.Frame(io_card)
        output_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(output_frame, text="Output Folder:").pack(anchor="w")
        
        output_browse_frame = ttk.Frame(output_frame)
        output_browse_frame.pack(fill=tk.X, pady=5)
        
        ttk.Entry(
            output_browse_frame, 
            textvariable=self.output_path_var
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(
            output_browse_frame, 
            text="Browse", 
            command=self.browse_output
        ).pack(side=tk.RIGHT)
        
        # Parameters Card
        params_card = ttk.LabelFrame(left_column, text="Parameters", padding=15)
        params_card.pack(fill=tk.X, pady=(0, 15))
        
        # Parameters grid
        params_grid = ttk.Frame(params_card)
        params_grid.pack(fill=tk.X)
        
        # After the parameters grid
        # Add a note about the 40-second limit
        ttk.Label(
            params_card,
            text=f"Note: Scene detection analyzes only the first {MAX_ANALYSIS_DURATION} seconds of the video for speed.",
            style="Info.TLabel",
            wraplength=400
        ).pack(pady=(10, 0))

        # Sequence length
        ttk.Label(
            params_grid, 
            text="Sequence Length (seconds):"
        ).grid(row=0, column=0, sticky="w", pady=5)
        
        ttk.Spinbox(
            params_grid, 
            from_=1, 
            to=60, 
            textvariable=self.sequence_length_var, 
            width=5
        ).grid(row=0, column=1, sticky="w", pady=5, padx=5)
        
        # Number of sequences
        ttk.Label(
            params_grid, 
            text="Number of Sequences:"
        ).grid(row=1, column=0, sticky="w", pady=5)
        
        ttk.Spinbox(
            params_grid, 
            from_=1, 
            to=10, 
            textvariable=self.num_sequences_var, 
            width=5
        ).grid(row=1, column=1, sticky="w", pady=5, padx=5)
        
        # Scene detection threshold
        ttk.Label(
            params_grid, 
            text="Scene Detection Threshold:"
        ).grid(row=2, column=0, sticky="w", pady=5)
        
        ttk.Spinbox(
            params_grid, 
            from_=5.0, 
            to=100.0, 
            increment=5.0, 
            textvariable=self.threshold_var, 
            width=5
        ).grid(row=2, column=1, sticky="w", pady=5, padx=5)
        
        # Output format
        ttk.Label(
            params_grid, 
            text="Output Format:"
        ).grid(row=0, column=2, sticky="w", pady=5, padx=(20, 5))
        
        format_values = list(OUTPUT_FORMATS.keys())
        format_combobox = ttk.Combobox(
            params_grid, 
            textvariable=self.output_format_var, 
            values=format_values, 
            width=15,
            state="readonly"
        )
        format_combobox.grid(row=0, column=3, sticky="w", pady=5)
        format_combobox.bind("<<ComboboxSelected>>", self.update_format_description)
        
        # Quality
        ttk.Label(
            params_grid, 
            text="Quality:"
        ).grid(row=1, column=2, sticky="w", pady=5, padx=(20, 5))
        
        quality_values = list(QUALITY_SETTINGS.keys())
        quality_combobox = ttk.Combobox(
            params_grid, 
            textvariable=self.quality_var, 
            values=quality_values, 
            width=15,
            state="readonly"
        )
        quality_combobox.grid(row=1, column=3, sticky="w", pady=5)
        quality_combobox.bind("<<ComboboxSelected>>", self.update_quality_description)
        
        # Description
        description_frame = ttk.Frame(params_card)
        description_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(
            description_frame, 
            textvariable=self.description_var, 
            wraplength=350,
            style="Info.TLabel"
        ).pack(fill=tk.X)
        
        # Initialize descriptions
        self.update_format_description(None)
        self.update_quality_description(None)
        
        # ===== RIGHT COLUMN =====
        
        # Preview Card
        preview_card = ttk.LabelFrame(right_column, text="Preview", padding=15)
        preview_card.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Thumbnail frame
        self.thumbnail_frame = ttk.Frame(preview_card)
        self.thumbnail_frame.pack(fill=tk.BOTH, expand=True)
        
        # Default thumbnail label
        self.thumbnail_label = ttk.Label(
            self.thumbnail_frame, 
            text="No video selected"
        )
        self.thumbnail_label.pack(fill=tk.BOTH, expand=True, pady=50)
        
        # Progress Card
        progress_card = ttk.LabelFrame(right_column, text="Progress", padding=15)
        progress_card.pack(fill=tk.X, pady=(0, 15))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            progress_card, 
            variable=self.progress_var, 
            mode="determinate"
        )
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Status label
        ttk.Label(
            progress_card, 
            textvariable=self.status_var
        ).pack(fill=tk.X, pady=5)
        
        # Action buttons
        button_frame = ttk.Frame(self.main_container)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Process button
        self.process_button = ttk.Button(
            button_frame, 
            text="Process Video", 
            command=self.process_video,
            style="Accent.TButton" if hasattr(self.style, 'configure') and 'Accent.TButton' in self.style.theme_names() else ""
        )
        self.process_button.pack(side=tk.RIGHT, padx=5)
        
        # Exit button
        ttk.Button(
            button_frame, 
            text="Exit", 
            command=self.root.destroy
        ).pack(side=tk.RIGHT, padx=5)
    
    def toggle_theme(self):
        """Toggle between light and dark theme."""
        new_theme = toggle_theme_mode(self.root)
        self.theme_button.config(text="☀️" if new_theme == "dark" else "🌙")
        
        # Save theme preference if config manager is available
        if self.config_manager:
            self.config_manager.set('theme', new_theme)
            self.config_manager.save_config()
            
    def browse_input(self):
        """Open a file dialog to select the input video."""
        filetypes = [("Video files", " ".join(f"*{ext}" for ext in VIDEO_EXTENSIONS))]
        filetypes.append(("All files", "*.*"))
        
        file_path = filedialog.askopenfilename(
            title="Select Input Video",
            filetypes=filetypes,
            initialdir=self.default_input_folder
        )
        if file_path:
            self.input_path_var.set(file_path)
            
            # Remember this directory for next time
            self.default_input_folder = os.path.dirname(file_path)
            
            # Auto-set the output folder to a subfolder in the same directory
            input_dir = os.path.dirname(file_path)
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_dir = os.path.join(input_dir, f"{base_name}_sequences")
            self.output_path_var.set(output_dir)
            self.default_output_folder = input_dir
            
            # Update the thumbnail
            self.update_thumbnail(file_path)
            
    def update_thumbnail(self, video_path):
        """Update the thumbnail preview with a frame from the video."""
        # Clear existing thumbnail
        for widget in self.thumbnail_frame.winfo_children():
            widget.destroy()
            
        # Create a new thumbnail
        thumbnail = create_thumbnail(video_path)
        
        if thumbnail:
            # Convert PIL image to Tkinter PhotoImage
            self.thumbnail_image = ImageTk.PhotoImage(thumbnail)
            
            # Display the thumbnail
            thumbnail_label = ttk.Label(
                self.thumbnail_frame, 
                image=self.thumbnail_image
            )
            thumbnail_label.pack(pady=10)
            
            # Add video name
            ttk.Label(
                self.thumbnail_frame, 
                text=os.path.basename(video_path)
            ).pack()
        else:
            # Display error message if thumbnail creation failed
            ttk.Label(
                self.thumbnail_frame, 
                text="Could not create thumbnail"
            ).pack(fill=tk.BOTH, expand=True, pady=50)
            
    def browse_output(self):
        """Open a folder dialog to select the output directory."""
        folder_path = filedialog.askdirectory(
            title="Select Output Folder",
            initialdir=self.default_output_folder or self.default_input_folder
        )
        if folder_path:
            self.output_path_var.set(folder_path)
            self.default_output_folder = folder_path
            
    def update_progress(self, value):
        """Update the progress bar."""
        self.progress_var.set(value)
        
    def update_status(self, message):
        """Update the status message."""
        self.status_var.set(message)
        
    def update_format_description(self, event):
        """Update the description when format is changed."""
        selected_format = self.output_format_var.get()
        if selected_format in OUTPUT_FORMATS:
            desc = OUTPUT_FORMATS[selected_format]['description']
            self.description_var.set(f"Format: {desc}")
            self.update_quality_description(None)
        
    def update_quality_description(self, event):
        """Update the description when quality is changed."""
        selected_quality = self.quality_var.get()
        selected_format = self.output_format_var.get()
        
        if selected_format in OUTPUT_FORMATS and selected_quality in QUALITY_SETTINGS:
            format_desc = OUTPUT_FORMATS[selected_format]['description']
            
            if 'profiles' in OUTPUT_FORMATS[selected_format] and selected_quality in OUTPUT_FORMATS[selected_format]['profiles']:
                profile_desc = OUTPUT_FORMATS[selected_format]['profiles'][selected_quality]
                self.description_var.set(f"{format_desc} - {profile_desc}")
            else:
                quality_desc = QUALITY_SETTINGS[selected_quality]
                self.description_var.set(f"{format_desc} - {quality_desc}")
    
    def process_video(self):
        """Process the selected video."""
        input_path = self.input_path_var.get()
        output_folder = self.output_path_var.get()
        
        if not input_path or not output_folder:
            messagebox.showerror("Error", "Please select both input video and output folder")
            return
            
        if not os.path.exists(input_path):
            messagebox.showerror("Error", "Input video file does not exist")
            return
            
        # Get parameters
        sequence_length = self.sequence_length_var.get()
        threshold = self.threshold_var.get()
        num_sequences = self.num_sequences_var.get()
        output_format = self.output_format_var.get()
        quality = self.quality_var.get()
        
        # Check disk space
        try:
            input_size = os.path.getsize(input_path)
            estimated_output_size = input_size * num_sequences * 1.5  # Conservative estimate
            free_space = get_free_disk_space(os.path.dirname(output_folder))
            
            if free_space < estimated_output_size:
                messagebox.showerror(
                    "Insufficient Disk Space",
                    f"Not enough disk space. Need approximately {format_file_size(estimated_output_size)} "
                    f"but only {format_file_size(free_space)} available."
                )
                return
        except Exception as e:
            messagebox.showerror("Error", f"Error checking disk space: {str(e)}")
            return
            
        # Disable the button during processing
        self.process_button.config(state="disabled")
        
        # Reset progress
        self.progress_var.set(0)
        
        # Run processing in a separate thread to keep UI responsive
        def run_processing():
            try:
                # Create output folder if it doesn't exist
                os.makedirs(output_folder, exist_ok=True)
                
                # Detect scene changes in the first 40 seconds only
                self.update_status("Detecting scene changes in first 40 seconds...")
                scene_changes = self.processor.detect_scene_changes(
                    input_path,
                    threshold,
                    max_duration=40.0,  # Analyze only first 40 seconds
                    progress_callback=lambda p: self.root.after(0, lambda: self.update_progress(p * 0.5))
                )
                
                self.root.after(0, lambda: self.update_status("Extracting sequences..."))
                
                # Extract sequences
                output_paths = self.processor.extract_sequences(
                    input_path,
                    output_folder,
                    scene_changes,
                    sequence_length,
                    num_sequences,
                    output_format,
                    quality,
                    progress_callback=lambda p: self.root.after(0, lambda: self.update_progress(50 + p * 0.5))
                )
                
                # Update UI from the main thread
                self.root.after(0, lambda: self.processing_complete(True, output_paths))
                
            except Exception as e:
                self.root.after(0, lambda: self.processing_complete(False, str(e)))
                
        # Start processing thread
        threading.Thread(target=run_processing, daemon=True).start()
        
    def processing_complete(self, success, result):
        """Handle the completion of video processing."""
        # Re-enable buttons
        self.process_button.config(state="normal")
        
        # Update progress and status
        self.progress_var.set(100)
        
        if success:
            self.update_status("Processing completed successfully")
            self.show_processing_results(result)
        else:
            self.update_status(f"Error: {result}")
            messagebox.showerror("Error", str(result))
            
    def show_processing_results(self, output_paths):
        """Show detailed processing results.
        
        Args:
            output_paths: List of paths to the extracted sequences
        """
        # Create a new window
        results_window = tk.Toplevel(self.root)
        results_window.title("Processing Results")
        results_window.geometry("600x400")
        results_window.transient(self.root)
        
        # Create a frame for the results
        main_frame = ttk.Frame(results_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add a header
        ttk.Label(
            main_frame, 
            text="Processing Completed Successfully", 
            style="Header.TLabel"
        ).pack(pady=(0, 10))
        
        # Add summary
        ttk.Label(
            main_frame, 
            text=f"Extracted {len(output_paths)} sequences"
        ).pack(pady=(0, 10))
        
        # Create a frame for the file list
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create a listbox with scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=listbox.yview)
        
        # Add files to the listbox
        for path in output_paths:
            listbox.insert(tk.END, os.path.basename(path))
        
        # Add buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Open output folder button
        def open_output_folder():
            if output_paths:
                folder = os.path.dirname(output_paths[0])
                if platform.system() == "Windows":
                    os.startfile(folder)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", folder])
                else:  # Linux
                    subprocess.run(["xdg-open", folder])
        
        ttk.Button(
            button_frame,
            text="Open Output Folder",
            command=open_output_folder
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Close",
            command=results_window.destroy
        ).pack(side=tk.RIGHT, padx=5)

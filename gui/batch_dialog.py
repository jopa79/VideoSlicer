# gui/batch_dialog.py
"""Batch processing dialog for processing multiple videos."""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

class BatchDialog:
    """Dialog for batch processing of videos."""
    
    def __init__(self, parent, batch_processor, config_manager, i18n):
        """Initialize the batch processing dialog.
        
        Args:
            parent: Parent window.
            batch_processor: Batch processor instance.
            config_manager: Configuration manager instance.
            i18n: Internationalization instance.
        """
        self.parent = parent
        self.batch_processor = batch_processor
        self.config_manager = config_manager
        self.i18n = i18n
        
        # Create the dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(i18n.get('batch_title'))
        self.dialog.geometry("800x600")
        self.dialog.minsize(600, 400)
        self.dialog.grab_set()
        
        # Video files list
        self.video_files = []
        
        # Processing parameters
        self.sequence_length = config_manager.get('sequence_length', 10)
        self.num_sequences = config_manager.get('num_sequences', 3)
        self.threshold = config_manager.get('scene_threshold', 30.0)
        self.output_format = config_manager.get('output_format', 'prores')
        self.quality = config_manager.get('quality', 'medium')
        
        # Status tracking
        self.status_map = {}  # Maps file path to status
        self.output_map = {}  # Maps file path to output paths
        
        # Processing thread
        self.processing_thread = None
        self.stop_processing = False
        
        self.create_widgets()
        
    def create_widgets(self):
        """Create the dialog widgets."""
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # File list frame
        file_frame = ttk.LabelFrame(main_frame, text=self.i18n.get('file'), padding=10)
        file_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Button toolbar
        toolbar = ttk.Frame(file_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text=self.i18n.get('add_files'), 
                  command=self.add_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text=self.i18n.get('add_folder'), 
                  command=self.add_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text=self.i18n.get('remove'), 
                  command=self.remove_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text=self.i18n.get('clear'), 
                  command=self.clear_files).pack(side=tk.LEFT, padx=2)
        
        # File list with scrollbar
        list_frame = ttk.Frame(file_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview for files
        columns = ('file', 'status', 'output')
        self.file_tree = ttk.Treeview(list_frame, columns=columns, show='headings', selectmode='extended')
        self.file_tree.heading('file', text=self.i18n.get('file'))
        self.file_tree.heading('status', text=self.i18n.get('status'))
        self.file_tree.heading('output', text=self.i18n.get('output'))
        
        # Set column widths
        self.file_tree.column('file', width=400)
        self.file_tree.column('status', width=100)
        self.file_tree.column('output', width=200)
        
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrollbar
        scrollbar.config(command=self.file_tree.yview)
        self.file_tree.config(yscrollcommand=scrollbar.set)
        
        # Parameters frame
        params_frame = ttk.LabelFrame(main_frame, text=self.i18n.get('parameters'), padding=10)
        params_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create a grid for parameters
        param_grid = ttk.Frame(params_frame)
        param_grid.pack(fill=tk.X, expand=True)
        
        # Sequence length
        ttk.Label(param_grid, text=self.i18n.get('sequence_length')).grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.sequence_length_var = tk.IntVar(value=self.sequence_length)
        ttk.Spinbox(param_grid, from_=1, to=60, textvariable=self.sequence_length_var, width=5).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Number of sequences
        ttk.Label(param_grid, text=self.i18n.get('num_sequences')).grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        self.num_sequences_var = tk.IntVar(value=self.num_sequences)
        ttk.Spinbox(param_grid, from_=1, to=10, textvariable=self.num_sequences_var, width=5).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Scene detection threshold
        ttk.Label(param_grid, text=self.i18n.get('scene_threshold')).grid(row=2, column=0, sticky=tk.W, pady=5, padx=5)
        self.threshold_var = tk.DoubleVar(value=self.threshold)
        ttk.Spinbox(param_grid, from_=5.0, to=100.0, increment=5.0, textvariable=self.threshold_var, width=5).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Output format
        ttk.Label(param_grid, text=self.i18n.get('output_format')).grid(row=0, column=2, sticky=tk.W, pady=5, padx=(20, 5))
        self.output_format_var = tk.StringVar(value=self.output_format)
        ttk.Combobox(param_grid, textvariable=self.output_format_var, values=["prores", "h264", "h265"], width=10).grid(row=0, column=3, sticky=tk.W, pady=5)
        
        # Quality
        ttk.Label(param_grid, text=self.i18n.get('quality')).grid(row=1, column=2, sticky=tk.W, pady=5, padx=(20, 5))
        self.quality_var = tk.StringVar(value=self.quality)
        ttk.Combobox(param_grid, textvariable=self.quality_var, values=["low", "medium", "high"], width=10).grid(row=1, column=3, sticky=tk.W, pady=5)
        
        # Output folder
        ttk.Label(param_grid, text=self.i18n.get('output_folder')).grid(row=3, column=0, sticky=tk.W, pady=5, padx=5)
        output_frame = ttk.Frame(param_grid)
        output_frame.grid(row=3, column=1, columnspan=3, sticky=tk.EW, pady=5)
        
        self.output_folder_var = tk.StringVar(value=self.config_manager.get('output_folder', ''))
        ttk.Entry(output_frame, textvariable=self.output_folder_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_frame, text=self.i18n.get('browse'), 
                  command=self.browse_output_folder).pack(side=tk.RIGHT, padx=5)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text=self.i18n.get('progress'), padding=10)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, length=100, mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Status label
        self.status_var = tk.StringVar(value=self.i18n.get('ready'))
        status_label = ttk.Label(progress_frame, textvariable=self.status_var, anchor=tk.W)
        status_label.pack(fill=tk.X, pady=5)
        
        # Button frame
        button_frame = ttk.Frame(self.dialog, padding=10)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Start button
        self.start_button = ttk.Button(button_frame, text=self.i18n.get('start_batch'), 
                                      command=self.start_batch)
        self.start_button.pack(side=tk.RIGHT, padx=5)
        
        # Cancel button
        self.cancel_button = ttk.Button(button_frame, text=self.i18n.get('cancel'), 
                                      command=self.cancel_batch)
        self.cancel_button.pack(side=tk.RIGHT, padx=5)
        
        # Handle dialog close
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def add_files(self):
        """Add video files to the batch."""
        files = filedialog.askopenfilenames(
            title=self.i18n.get('add_files'),
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv"), ("All files", "*.*")],
            initialdir=self.config_manager.get('input_folder', os.path.expanduser("~"))
        )
        
        if not files:
            return
            
        # Remember this directory
        if files:
            self.config_manager.set('input_folder', os.path.dirname(files[0]))
            
        # Add files to the list
        for file in files:
            if file not in self.video_files:
                self.video_files.append(file)
                self.status_map[file] = self.i18n.get('pending')
                self.file_tree.insert('', 'end', values=(os.path.basename(file), self.i18n.get('pending'), ''))
                
    def add_folder(self):
        """Add all video files from a folder."""
        folder = filedialog.askdirectory(
            title=self.i18n.get('add_folder'),
            initialdir=self.config_manager.get('input_folder', os.path.expanduser("~"))
        )
        
        if not folder:
            return
            
        # Remember this directory
        self.config_manager.set('input_folder', folder)
        
        # Find all video files in the folder
        video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv')
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.lower().endswith(video_extensions):
                    file_path = os.path.join(root, file)
                    if file_path not in self.video_files:
                        self.video_files.append(file_path)
                        self.status_map[file_path] = self.i18n.get('pending')
                        self.file_tree.insert('', 'end', values=(os.path.basename(file_path), self.i18n.get('pending'), ''))
                        
    def remove_files(self):
        """Remove selected files from the batch."""
        selected = self.file_tree.selection()
        if not selected:
            return
            
        # Get the file paths for the selected items
        selected_files = []
        for item_id in selected:
            item = self.file_tree.item(item_id)
            filename = item['values'][0]
            
            # Find the full path
            for file_path in self.video_files:
                if os.path.basename(file_path) == filename:
                    selected_files.append(file_path)
                    break
                    
        # Remove from the list and tree
        for file_path in selected_files:
            self.video_files.remove(file_path)
            del self.status_map[file_path]
            if file_path in self.output_map:
                del self.output_map[file_path]
                
        for item_id in selected:
            self.file_tree.delete(item_id)
            
    def clear_files(self):
        """Clear all files from the batch."""
        self.video_files = []
        self.status_map = {}
        self.output_map = {}
        
        # Clear the tree
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
            
    def browse_output_folder(self):
        """Browse for output folder."""
        folder = filedialog.askdirectory(
            title=self.i18n.get('output_folder'),
            initialdir=self.output_folder_var.get() or self.config_manager.get('output_folder', os.path.expanduser("~"))
        )
        if folder:
            self.output_folder_var.set(folder)
            self.config_manager.set('output_folder', folder)
            
    def update_file_status(self, file_path, status, output=''):
        """Update the status of a file in the tree.
        
        Args:
            file_path: Path to the file.
            status: New status string.
            output: Output information.
        """
        self.status_map[file_path] = status
        
        # Find the item in the tree
        for item_id in self.file_tree.get_children():
            item = self.file_tree.item(item_id)
            if item['values'][0] == os.path.basename(file_path):
                self.file_tree.item(item_id, values=(os.path.basename(file_path), status, output))
                break
                
    def start_batch(self):
        """Start batch processing."""
        if not self.video_files:
            messagebox.showwarning(self.i18n.get('warning'), "No files to process")
            return
            
        output_folder = self.output_folder_var.get()
        if not output_folder:
            messagebox.showerror(self.i18n.get('error'), "Please select an output folder")
            return
            
        # Disable UI during processing
        self.start_button.config(state='disabled')
        self.progress_var.set(0)
        self.status_var.set(self.i18n.get('processing'))
        
        # Get parameters
        sequence_length = self.sequence_length_var.get()
        threshold = self.threshold_var.get()
        num_sequences = self.num_sequences_var.get()
        output_format = self.output_format_var.get()
        quality = self.quality_var.get()
        
        # Get batch settings
        batch_settings = self.config_manager.get('batch_settings', {})
        parallel = batch_settings.get('parallel_processing', True)
        max_workers = batch_settings.get('max_workers', 2)
        
        # Reset stop flag
        self.stop_processing = False
        
        # Start processing thread
        self.processing_thread = threading.Thread(
            target=self._process_batch,
            args=(output_folder, sequence_length, threshold, num_sequences, 
                 output_format, quality, parallel, max_workers),
            daemon=True
        )
        self.processing_thread.start()
        
    def _process_batch(self, output_folder, sequence_length, threshold, 
                      num_sequences, output_format, quality, parallel, max_workers):
        """Process the batch of videos.
        
        Args:
            output_folder: Base output folder.
            sequence_length: Length of each sequence in seconds.
            threshold: Threshold for scene change detection.
            num_sequences: Number of consecutive sequences to extract.
            output_format: Output format (prores, h264, h265).
            quality: Quality setting (low, medium, high).
            parallel: Whether to process videos in parallel.
            max_workers: Maximum number of parallel workers.
        """
        try:
            # Update all files to 'pending'
            for file_path in self.video_files:
                self.update_file_status(file_path, self.i18n.get('pending'))
                
            # Process videos
            for i, file_path in enumerate(self.video_files):
                if self.stop_processing:
                    break
                    
                # Update status
                self.update_file_status(file_path, self.i18n.get('processing'))
                self.dialog.after(0, lambda: self.status_var.set(
                    f"{self.i18n.get('processing')} {i+1}/{len(self.video_files)}: {os.path.basename(file_path)}"
                ))
                
                try:
                    # Create output directory for this file
                    base_name = os.path.splitext(os.path.basename(file_path))[0]
                    file_output_dir = os.path.join(output_folder, f"{base_name}_sequences")
                    os.makedirs(file_output_dir, exist_ok=True)
                    
                    # Process the file
                    success, output_paths = self.batch_processor._process_single_video(
                        file_path,
                        output_folder,
                        sequence_length,
                        threshold,
                        num_sequences,
                        output_format,
                        quality,
                        lambda p: self.dialog.after(0, lambda: self.progress_var.set(p))
                    )
                    
                    # Update status
                    if success:
                        status = self.i18n.get('completed')
                        output_info = f"{len(output_paths)} {self.i18n.get('sequences')}"
                        self.output_map[file_path] = output_paths
                    else:
                        status = self.i18n.get('failed')
                        output_info = ""
                        
                    self.update_file_status(file_path, status, output_info)
                    
                except Exception as e:
                    self.update_file_status(file_path, self.i18n.get('failed'), str(e))
                    
                # Update progress
                overall_progress = ((i + 1) / len(self.video_files)) * 100
                self.dialog.after(0, lambda p=overall_progress: self.progress_var.set(p))
                
            # Processing complete
            self.dialog.after(0, lambda: self.status_var.set(
                f"{self.i18n.get('processing_complete')} ({len(self.output_map)}/{len(self.video_files)})"
            ))
            
        except Exception as e:
            self.dialog.after(0, lambda: self.status_var.set(f"{self.i18n.get('error')}: {str(e)}"))
            
        finally:
            # Re-enable UI
            self.dialog.after(0, lambda: self.start_button.config(state='normal'))
            
    def cancel_batch(self):
        """Cancel batch processing and close the dialog."""
        if self.processing_thread and self.processing_thread.is_alive():
            self.stop_processing = True
            self.status_var.set(self.i18n.get('canceling'))
            # Wait for thread to finish
            self.processing_thread.join(0.1)
            
        self.dialog.destroy()
        
    def on_close(self):
        """Handle dialog close."""
        self.cancel_batch()
"""Core video processing functionality using OpenCV and FFmpeg."""
import os
import cv2
import numpy as np
import logging
import subprocess
import tempfile
import time
from datetime import datetime
from utils import setup_logger, format_time

class VideoProcessor:
    """Class for processing videos, detecting scenes, and extracting sequences."""
    
    def __init__(self, logger=None):
        """Initialize the VideoProcessor.
        
        Args:
            logger: Optional logger instance. If None, a new one will be created.
        """
        self.logger = logger or setup_logger("video_processor")
    
    def check_ffmpeg_available(self):
        """Check if FFmpeg is available and has the required codecs.
        
        Returns:
            tuple: (bool, str, dict) - (is_available, error_message, codec_support)
        """
        codec_support = {
            'prores': False,
            'h264': False,
            'h265': False,
        }
        
        try:
            # Check if FFmpeg is installed
            process = subprocess.run(
                ["ffmpeg", "-version"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            if process.returncode != 0:
                return False, "FFmpeg is not installed or not in PATH", codec_support
                
            # Check for codec support
            encoders_process = subprocess.run(
                ["ffmpeg", "-encoders"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            if encoders_process.returncode != 0:
                return False, "Error checking FFmpeg encoders", codec_support
            
            # Check for ProRes support (could be prores or prores_ks depending on ffmpeg version)
            if "prores" in encoders_process.stdout or "prores_ks" in encoders_process.stdout:
                codec_support['prores'] = True
                
            # Check for H.264 support
            if "libx264" in encoders_process.stdout:
                codec_support['h264'] = True
                
            # Check for H.265 support
            if "libx265" in encoders_process.stdout:
                codec_support['h265'] = True
                
            # Base ffmpeg availability on whether at least one codec is supported
            is_available = any(codec_support.values())
            
            if not is_available:
                return False, "FFmpeg is installed but no supported video codecs found", codec_support
            
            # If ProRes is specifically requested but not available, give a more detailed message
            if not codec_support['prores']:
                self.logger.warning("FFmpeg is installed but doesn't support ProRes encoding")
                
            return True, "", codec_support
        except Exception as e:
            return False, f"Error checking FFmpeg: {str(e)}", codec_support
        
    def detect_scene_changes(self, video_path, threshold=30.0, max_duration=40.0, progress_callback=None):
        """Detect scene changes in the video.
        
        Args:
            video_path: Path to the input video
            threshold: Threshold for scene change detection (higher = less sensitive)
            max_duration: Maximum duration in seconds to analyze (default: 40 seconds)
            progress_callback: Optional callback function for progress updates
            
        Returns:
            List of timestamps (in seconds) where scene changes occur
        """
        self.logger.info(f"Detecting scene changes with threshold {threshold} in first {max_duration} seconds...")
        
        # Open the video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            self.logger.error(f"Could not open video file: {video_path}")
            raise ValueError(f"Could not open video file: {video_path}")
            
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Calculate max frames to process based on max_duration
        max_frames = int(max_duration * fps)
        frames_to_process = min(max_frames, total_frames)
        
        self.logger.info(f"Will process {frames_to_process} frames (max {max_duration} seconds at {fps} fps)")
        
        # Initialize variables
        prev_frame = None
        scene_changes = []
        frame_count = 0
        
        # Process each frame up to the maximum
        while frame_count < frames_to_process:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Convert frame to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Skip the first frame
            if prev_frame is None:
                prev_frame = gray
                frame_count += 1
                continue
                
            # Calculate absolute difference between current and previous frame
            frame_diff = cv2.absdiff(gray, prev_frame)
            
            # Calculate the mean difference
            mean_diff = np.mean(frame_diff)
            
            # If the difference is above the threshold, consider it a scene change
            if mean_diff > threshold:
                timestamp = frame_count / fps
                scene_changes.append(timestamp)
                self.logger.info(f"Scene change detected at {timestamp:.2f} seconds (diff: {mean_diff:.2f})")
                
            # Update variables for next iteration
            prev_frame = gray
            frame_count += 1
            
            # Update progress if callback provided
            if progress_callback and frames_to_process > 0:
                progress = (frame_count / frames_to_process) * 100
                progress_callback(progress)
            
            # Log progress every 100 frames
            if frame_count % 100 == 0:
                self.logger.info(f"Processed {frame_count}/{frames_to_process} frames ({frame_count/frames_to_process*100:.2f}%)")
                
        # Release the video capture
        cap.release()
        
        self.logger.info(f"Scene detection complete. Found {len(scene_changes)} scene changes in first {max_duration} seconds.")
        return scene_changes
        
    def extract_sequences(self, video_path, output_folder, scene_changes, 
                         sequence_length=10, 
                         num_sequences=3,
                         output_format="prores",
                         quality="medium",
                         progress_callback=None):
        """Extract sequences from the video starting at scene changes.
        
        Args:
            video_path: Path to the input video
            output_folder: Folder to save the extracted sequences
            scene_changes: List of timestamps where scene changes occur
            sequence_length: Length of each sequence in seconds
            num_sequences: Number of consecutive sequences to extract
            output_format: Output format ('prores' for ProRes 422, 'h264' for MP4)
            quality: Quality setting ('low', 'medium', 'high')
            progress_callback: Optional callback function for progress updates
            
        Returns:
            List of paths to the extracted sequences
        """
        # Check if FFmpeg is available with required codecs
        ffmpeg_available, error_message, codec_support = self.check_ffmpeg_available()
        if not ffmpeg_available:
            self.logger.error(f"FFmpeg error: {error_message}")
            raise RuntimeError(f"FFmpeg error: {error_message}")
        
        # If the requested format isn't supported, fall back to an alternative
        if output_format not in codec_support or not codec_support[output_format]:
            original_format = output_format
            # Try to find a supported format to fall back to
            for format_name, is_supported in codec_support.items():
                if is_supported:
                    output_format = format_name
                    self.logger.warning(f"Requested format '{original_format}' not supported. "
                                      f"Falling back to '{output_format}'")
                    break
            else:
                raise RuntimeError(f"No supported video codecs available in FFmpeg")
        
        self.logger.info(f"Extracting {num_sequences} sequences of {sequence_length} seconds each...")
        
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Open the video to get properties
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            self.logger.error(f"Could not open video file: {video_path}")
            raise ValueError(f"Could not open video file: {video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_duration = total_frames / fps
        cap.release()  # Release the capture as we'll use FFmpeg for extraction
        
        # Filter scene changes
        valid_scene_changes = [sc for sc in scene_changes 
                              if sc + (sequence_length * num_sequences) <= video_duration]
        
        if not valid_scene_changes:
            self.logger.warning("No valid scene changes found for sequence extraction")
            if scene_changes:
                self.logger.info("Using the first scene change and adjusting sequence length")
                first_change = scene_changes[0]
                max_sequences = int((video_duration - first_change) / sequence_length)
                if max_sequences > 0:
                    valid_scene_changes = [first_change]
                    num_sequences = min(num_sequences, max_sequences)
                else:
                    self.logger.warning("Not enough video duration after first scene change")
                    valid_scene_changes = [0.0]  # Start from beginning
            else:
                self.logger.warning("No scene changes detected. Using the beginning of the video.")
                valid_scene_changes = [0.0]  # Start from the beginning if no scene changes detected
        
        # Select the first scene change
        start_time = valid_scene_changes[0]
        
        # Set up output parameters based on format
        if output_format == 'prores':
            extension = '.mov'
            # Quality settings for ProRes 422
            profiles = {
                "low": "0",      # ProRes 422 Proxy
                "medium": "2",   # ProRes 422 LT
                "high": "3"      # ProRes 422 HQ
            }
            profile = profiles.get(quality.lower(), "2")  # Default to ProRes 422 LT
        elif output_format in ('h264', 'mp4'):
            extension = '.mp4'
            # CRF values for H.264 (lower = higher quality)
            profiles = {
                "low": "28",     # Lower quality
                "medium": "23",  # Medium quality
                "high": "18"     # High quality
            }
            profile = profiles.get(quality.lower(), "23")  # Default to medium
        elif output_format == 'h265':
            extension = '.mp4'
            # CRF values for H.265 (lower = higher quality)
            profiles = {
                "low": "28",     # Lower quality
                "medium": "23",  # Medium quality
                "high": "18"     # High quality
            }
            profile = profiles.get(quality.lower(), "23")  # Default to medium
        else:
            # Fallback to H.264
            self.logger.warning(f"Unknown format '{output_format}'. Falling back to H.264")
            output_format = 'h264'
            extension = '.mp4'
            profile = "23"  # Medium quality
        
        # Get base filename without extension
        base_filename = os.path.splitext(os.path.basename(video_path))[0]
        
        output_paths = []
        
        for i in range(num_sequences):
            sequence_start = start_time + (i * sequence_length)
            sequence_end = sequence_start + sequence_length
            
            if sequence_end > video_duration:
                self.logger.warning(f"Sequence {i+1} would exceed video duration. Skipping.")
                continue
            
            # Define output path with input filename as base
            output_filename = f"{base_filename}_seq_{i+1}{extension}"
            output_path = os.path.join(output_folder, output_filename)
            
            # Extract the sequence using FFmpeg with appropriate codec
            if output_format == 'prores':
                success = self._extract_prores_sequence(
                    video_path, 
                    output_path, 
                    sequence_start, 
                    sequence_length, 
                    profile,
                    progress_callback
                )
            else:  # h264 or h265
                success = self._extract_h26x_sequence(
                    video_path, 
                    output_path, 
                    sequence_start, 
                    sequence_length,
                    output_format,  # 'h264' or 'h265'
                    profile,
                    progress_callback
                )
            
            if success:
                output_paths.append(output_path)
                self.logger.info(f"Saved sequence {i+1} ({sequence_start:.2f}s - {sequence_end:.2f}s) to {output_path}")
            else:
                self.logger.error(f"Failed to save sequence {i+1}")
            
            # Update progress
            if progress_callback:
                progress = ((i + 1) / num_sequences) * 100
                progress_callback(progress)
        
        self.logger.info(f"Successfully extracted {len(output_paths)} sequences")
        return output_paths
    
    def _extract_prores_sequence(self, input_path, output_path, start_time, duration, profile="2", progress_callback=None):
        """Extract a sequence using FFmpeg with ProRes 422 codec and copy audio.
        
        Args:
            input_path: Path to the input video
            output_path: Path to save the output video
            start_time: Start time in seconds
            duration: Duration in seconds
            profile: ProRes profile (0=Proxy, 1=LT, 2=Standard, 3=HQ)
            progress_callback: Optional callback function for progress updates
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Format start time for FFmpeg
            start_time_str = format_time(start_time)
            
            # Create a temporary file for FFmpeg output
            progress_file = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
            progress_file.close()
            progress_file_path = progress_file.name
            
            # Get video dimensions
            cap = cv2.VideoCapture(input_path)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            
            # Check if we need to scale down to HD (1920x1080)
            scale_filter = ""
            if width > 1920 or height > 1080:
                self.logger.info(f"Scaling down from {width}x{height} to HD (1920x1080)")
                scale_filter = "-vf scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"
                
            # Construct FFmpeg command for ProRes 422 with audio copy
            cmd = [
                "ffmpeg",
                "-y",
                "-i", input_path,
                "-ss", str(start_time),
                "-t", str(duration),
            ]
            
            # Add scale filter if needed
            if scale_filter:
                cmd.extend(scale_filter.split())
                
            # Add codec options
            cmd.extend([
                "-c:v", "prores_ks",
                "-profile:v", profile,
                "-vendor", "ap10",
                "-pix_fmt", "yuv422p10le",
                "-c:a", "copy",  # Copy audio stream
                "-progress", progress_file_path,  # Write progress to file
                output_path
            ])
            
            # Run FFmpeg
            self.logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Monitor progress with improved method
            success = self._monitor_ffmpeg_progress(
                process, 
                progress_file_path, 
                progress_callback
            )
            
            return success
        except Exception as e:
            self.logger.error(f"Error extracting sequence: {str(e)}")
            return False
            
    def _extract_h26x_sequence(self, input_path, output_path, start_time, duration, 
                             codec='h264', quality="23", progress_callback=None):
        """Extract a sequence using FFmpeg with H.264/H.265 codec.
        
        Args:
            input_path: Path to the input video
            output_path: Path to save the output video
            start_time: Start time in seconds
            duration: Duration in seconds
            codec: Video codec ('h264' or 'h265')
            quality: CRF value (lower = higher quality)
            progress_callback: Optional callback function for progress updates
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create a temporary file for FFmpeg output
            progress_file = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
            progress_file.close()
            progress_file_path = progress_file.name
            
            # Get video dimensions
            cap = cv2.VideoCapture(input_path)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            
            # Check if we need to scale down to HD (1920x1080)
            scale_filter = ""
            if width > 1920 or height > 1080:
                self.logger.info(f"Scaling down from {width}x{height} to HD (1920x1080)")
                scale_filter = "-vf scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"
                
            # Construct FFmpeg command
            cmd = [
                "ffmpeg", "-y",
                "-i", input_path,
                "-ss", str(start_time),
                "-t", str(duration),
            ]
            
            # Add scale filter if needed
            if scale_filter:
                cmd.extend(scale_filter.split())
                
            # Select the right codec
            if codec == 'h265':
                codec_params = [
                    "-c:v", "libx265",
                    "-crf", quality,
                    "-preset", "medium",
                ]
            else:  # Default to h264
                codec_params = [
                    "-c:v", "libx264",
                    "-crf", quality,
                    "-preset", "medium",
                    "-pix_fmt", "yuv420p",
                ]
                
            cmd.extend(codec_params)
            
            # Add audio and progress tracking
            cmd.extend([
                "-c:a", "aac",      # Use AAC audio codec
                "-b:a", "128k",     # Audio bitrate
                "-progress", progress_file_path,  # Write progress to file
                output_path
            ])
            
            # Run FFmpeg
            self.logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Monitor progress with improved method
            success = self._monitor_ffmpeg_progress(
                process, 
                progress_file_path, 
                progress_callback
            )
            
            return success
        except Exception as e:
            self.logger.error(f"Error extracting sequence: {str(e)}")
            return False
            
    def _monitor_ffmpeg_progress(self, process, progress_file, progress_callback):
        """Monitor FFmpeg progress from a progress file.
        
        Args:
            process: Subprocess running FFmpeg
            progress_file: Path to the progress file
            progress_callback: Callback function for progress updates
        
        Returns:
            bool: True if successful, False otherwise
        """
        import time
        import os

        try:
            # Wait for progress file to be created
            while not os.path.exists(progress_file) or os.path.getsize(progress_file) == 0:
                time.sleep(0.1)
                # Check if process is still running
                if process.poll() is not None:
                    break
            
            # Reset tracking variables
            duration = None
            last_position = 0
            start_time = time.time()
            timeout = 30  # 30 seconds timeout for processing
            
            try:
                while process.poll() is None:
                    # Check for timeout
                    if time.time() - start_time > timeout:
                        self.logger.warning("FFmpeg process timed out")
                        process.terminate()
                        break
                    
                    if os.path.exists(progress_file):
                        with open(progress_file, 'r') as f:
                            content = f.read()
                        
                        # Parse progress information
                        for line in content.splitlines():
                            if line.startswith('out_time_ms='):
                                try:
                                    time_ms = int(line.split('=')[1])
                                    position = time_ms / 1000000  # Convert to seconds
                                    last_position = position
                                except (ValueError, IndexError):
                                    pass
                            elif line.startswith('duration='):
                                try:
                                    duration = float(line.split('=')[1])
                                except (ValueError, IndexError):
                                    pass
                        
                        # Calculate and report progress
                        if duration and duration > 0:
                            percent = min(100, (last_position / duration) * 100)
                            if progress_callback:
                                progress_callback(percent)
                    
                    time.sleep(0.5)
                
                # Ensure process is terminated
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.logger.warning("Force killing FFmpeg process")
                        process.kill()
                
                # Final progress update
                if progress_callback:
                    progress_callback(100)
                
                # Check process result
                if process.returncode and process.returncode != 0:
                    # Capture and log error output
                    stdout, stderr = process.communicate()
                    self.logger.error(f"FFmpeg process failed with return code {process.returncode}")
                    self.logger.error(f"Stderr: {stderr}")
                    return False
                
                return True
            
            finally:
                # Cleanup: remove progress file
                if os.path.exists(progress_file):
                    try:
                        os.unlink(progress_file)
                    except Exception as e:
                        self.logger.warning(f"Could not remove progress file: {e}")
        
        except Exception as e:
            self.logger.error(f"Error monitoring FFmpeg progress: {str(e)}")
            return False
    
    def get_scene_thumbnails(self, video_path, scene_changes, size=(320, 180)):
        """Get thumbnails for each scene change.
        
        Args:
            video_path: Path to the video file
            scene_changes: List of scene change timestamps
            size: Thumbnail size as (width, height)
            
        Returns:
            list: List of (timestamp, thumbnail) tuples
        """
        from utils import create_thumbnail
        
        thumbnails = []
        for timestamp in scene_changes:
            thumbnail = create_thumbnail(video_path, timestamp, size)
            if thumbnail:
                thumbnails.append((timestamp, thumbnail))
                
        return thumbnails
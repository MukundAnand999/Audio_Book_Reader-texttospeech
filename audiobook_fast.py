import os
import re
import threading
import time
import pyttsx3
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QFileDialog, QProgressBar, QTextEdit, QMessageBox

class AudioBookConverter(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.engine = None
        self.is_playing = False
        self.is_converting = False
        self.stop_requested = False
        self.init_engine()
        self.initUI()
        self.setup_connections()
        
    def init_engine(self):
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)
            self.engine.setProperty('volume', 0.9)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not initialize TTS engine: {str(e)}")
    
    def initUI(self):
        self.setWindowTitle("⚡ Turbo Audiobook Converter")
        self.setGeometry(100, 100, 900, 700)
        
        # Main layout
        main_layout = QtWidgets.QVBoxLayout()
        
        # Text input group
        self.setup_text_group()
        main_layout.addWidget(self.text_group)
        
        # Settings groups
        settings_layout = QtWidgets.QHBoxLayout()
        
        left_column = QtWidgets.QVBoxLayout()
        self.setup_voice_group()
        self.setup_pacing_group()
        left_column.addWidget(self.voice_group)
        left_column.addWidget(self.pacing_group)
        
        right_column = QtWidgets.QVBoxLayout()
        self.setup_output_group()
        right_column.addWidget(self.output_group)
        
        settings_layout.addLayout(left_column)
        settings_layout.addLayout(right_column)
        main_layout.addLayout(settings_layout)
        
        # Control buttons
        self.setup_control_buttons()
        main_layout.addLayout(self.control_buttons)
        
        # Progress and status
        self.setup_progress_status()
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.status_label)
        
        self.setLayout(main_layout)
        self.apply_styles()
    
    def setup_text_group(self):
        self.text_group = QtWidgets.QGroupBox("Text Input")
        layout = QtWidgets.QVBoxLayout()
        
        # Play controls
        controls = QtWidgets.QHBoxLayout()
        self.play_button = QtWidgets.QPushButton("▶ Play Text")
        self.stop_play_button = QtWidgets.QPushButton("■ Stop Playing")
        self.clear_button = QtWidgets.QPushButton("Clear Text")
        controls.addWidget(self.play_button)
        controls.addWidget(self.stop_play_button)
        controls.addWidget(self.clear_button)
        
        # Text area
        self.text_area = QTextEdit()
        self.text_area.setPlaceholderText("Enter or paste your text here...")
        
        layout.addLayout(controls)
        layout.addWidget(self.text_area)
        self.text_group.setLayout(layout)
    
    def setup_voice_group(self):
        self.voice_group = QtWidgets.QGroupBox("Voice Settings")
        layout = QtWidgets.QGridLayout()
        
        # Voice selection
        layout.addWidget(QtWidgets.QLabel("Voice:"), 0, 0)
        self.voice_combo = QtWidgets.QComboBox()
        self.populate_voices()
        layout.addWidget(self.voice_combo, 0, 1, 1, 2)
        
        # Rate control
        layout.addWidget(QtWidgets.QLabel("Speech Rate:"), 1, 0)
        self.rate_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.rate_slider.setRange(50, 300)
        self.rate_slider.setValue(150)
        self.rate_label = QtWidgets.QLabel("150 words/min")
        layout.addWidget(self.rate_slider, 1, 1)
        layout.addWidget(self.rate_label, 1, 2)
        
        # Volume control
        layout.addWidget(QtWidgets.QLabel("Volume:"), 2, 0)
        self.volume_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(90)
        self.volume_label = QtWidgets.QLabel("90%")
        layout.addWidget(self.volume_slider, 2, 1)
        layout.addWidget(self.volume_label, 2, 2)
        
        # Pitch control
        layout.addWidget(QtWidgets.QLabel("Pitch:"), 3, 0)
        self.pitch_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.pitch_slider.setRange(50, 150)
        self.pitch_slider.setValue(100)
        self.pitch_label = QtWidgets.QLabel("Normal")
        layout.addWidget(self.pitch_slider, 3, 1)
        layout.addWidget(self.pitch_label, 3, 2)
        
        self.voice_group.setLayout(layout)
    
    def setup_pacing_group(self):
        self.pacing_group = QtWidgets.QGroupBox("Pacing Settings")
        layout = QtWidgets.QGridLayout()
        
        layout.addWidget(QtWidgets.QLabel("Pause (s):"), 0, 0)
        self.pause_duration = QtWidgets.QDoubleSpinBox()
        self.pause_duration.setRange(0.1, 5.0)
        self.pause_duration.setValue(0.5)
        self.pause_duration.setSingleStep(0.1)
        layout.addWidget(self.pause_duration, 0, 1)
        
        layout.addWidget(QtWidgets.QLabel("Words/min:"), 1, 0)
        self.words_per_minute = QtWidgets.QSpinBox()
        self.words_per_minute.setRange(80, 300)
        self.words_per_minute.setValue(180)
        layout.addWidget(self.words_per_minute, 1, 1)
        
        self.pacing_group.setLayout(layout)
    
    def setup_output_group(self):
        self.output_group = QtWidgets.QGroupBox("Output Settings")
        layout = QtWidgets.QGridLayout()
        
        # Output directory
        layout.addWidget(QtWidgets.QLabel("Directory:"), 0, 0)
        self.output_dir = QtWidgets.QLineEdit(os.path.expanduser("~/Audiobooks"))
        self.browse_button = QtWidgets.QPushButton("...")
        self.browse_button.setFixedWidth(30)
        dir_layout = QtWidgets.QHBoxLayout()
        dir_layout.addWidget(self.output_dir)
        dir_layout.addWidget(self.browse_button)
        layout.addLayout(dir_layout, 0, 1)
        
        # Output format
        layout.addWidget(QtWidgets.QLabel("Format:"), 1, 0)
        self.format_combo = QtWidgets.QComboBox()
        self.format_combo.addItems(["Play Only", "Save as MP3", "Both"])
        layout.addWidget(self.format_combo, 1, 1)
        
        # Filename
        layout.addWidget(QtWidgets.QLabel("Filename:"), 2, 0)
        self.filename = QtWidgets.QLineEdit("audiobook")
        layout.addWidget(self.filename, 2, 1)
        
        self.output_group.setLayout(layout)
    
    def setup_control_buttons(self):
        self.control_buttons = QtWidgets.QHBoxLayout()
        
        self.convert_button = QtWidgets.QPushButton("🔊 Convert")
        self.stop_button = QtWidgets.QPushButton("🛑 Stop")
        self.preview_button = QtWidgets.QPushButton("🎧 Preview")
        
        self.control_buttons.addWidget(self.convert_button)
        self.control_buttons.addWidget(self.stop_button)
        self.control_buttons.addWidget(self.preview_button)
    
    def setup_progress_status(self):
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        
        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
    
    def setup_connections(self):
        # Slider connections
        self.rate_slider.valueChanged.connect(self.update_rate_label)
        self.volume_slider.valueChanged.connect(self.update_volume_label)
        self.pitch_slider.valueChanged.connect(self.update_pitch_label)
        
        # Button connections
        self.play_button.clicked.connect(self.play_text)
        self.stop_play_button.clicked.connect(self.stop_playing)
        self.clear_button.clicked.connect(self.clear_text)
        self.browse_button.clicked.connect(self.browse_directory)
        self.convert_button.clicked.connect(self.start_conversion)
        self.stop_button.clicked.connect(self.stop_conversion)
        self.preview_button.clicked.connect(self.preview_voice)
    
    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #000000;
                color: #FFFF00;
                font-family: Arial;
            }
            QGroupBox {
                border: 1px solid #555500;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QTextEdit, QLineEdit, QComboBox {
                background-color: #111111;
                color: #FFFF00;
                border: 1px solid #333300;
                padding: 5px;
            }
            QPushButton {
                background-color: #222200;
                color: #FFFF00;
                border: 1px solid #444400;
                padding: 5px 10px;
                min-width: 80px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #333300;
            }
            QPushButton:pressed {
                background-color: #111100;
            }
            QPushButton:disabled {
                background-color: #0A0A00;
                color: #888800;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #222200;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #FFFF00;
                border: 1px solid #444400;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QProgressBar {
                border: 1px solid #333300;
                border-radius: 3px;
                text-align: center;
                color: #FFFF00;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #FFCC00;
                border-radius: 2px;
            }
        """)
        
        # Additional styling
        self.text_area.setStyleSheet("font-size: 14px;")
        self.status_label.setStyleSheet("font-size: 12px; color: #FFCC00;")
        
        # Set initial button states
        self.stop_play_button.setEnabled(False)
        self.stop_button.setEnabled(False)
    
    def populate_voices(self):
        if not self.engine:
            return
            
        self.voice_combo.clear()
        voices = self.engine.getProperty('voices')
        for i, voice in enumerate(voices):
            self.voice_combo.addItem(f"{voice.name} ({voice.gender})", i)
    
    def update_rate_label(self, value):
        self.rate_label.setText(f"{value} wpm")
        if self.engine:
            self.engine.setProperty('rate', value)
    
    def update_volume_label(self, value):
        self.volume_label.setText(f"{value}%")
        if self.engine:
            self.engine.setProperty('volume', value/100)
    
    def update_pitch_label(self, value):
        if value < 90:
            self.pitch_label.setText("Low")
        elif value > 110:
            self.pitch_label.setText("High")
        else:
            self.pitch_label.setText("Normal")
    
    def clear_text(self):
        self.text_area.clear()
    
    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir.setText(directory)
    
    def preview_voice(self):
        if not self.engine:
            return
            
        # Save current settings
        old_voice = self.engine.getProperty('voice')
        old_rate = self.engine.getProperty('rate')
        old_volume = self.engine.getProperty('volume')
        old_pitch = self.engine.getProperty('pitch') if hasattr(self.engine, 'getProperty') else None
        
        # Apply selected settings
        voice_idx = self.voice_combo.currentData()
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[voice_idx].id)
        self.engine.setProperty('rate', self.rate_slider.value())
        self.engine.setProperty('volume', self.volume_slider.value()/100)
        
        # Apply pitch if available
        if old_pitch is not None:
            self.engine.setProperty('pitch', self.pitch_slider.value()/100)
        
        # Speak preview
        self.engine.say("This is a preview of the current voice settings.")
        self.engine.runAndWait()
        
        # Restore original settings
        self.engine.setProperty('voice', old_voice)
        self.engine.setProperty('rate', old_rate)
        self.engine.setProperty('volume', old_volume)
        if old_pitch is not None:
            self.engine.setProperty('pitch', old_pitch)
    
    def play_text(self):
        if self.is_playing or not self.engine:
            return
            
        text = self.text_area.toPlainText().strip()
        if not text:
            self.show_message("Please enter some text to play.", "warning")
            return
            
        self.is_playing = True
        self.stop_requested = False
        self.toggle_play_controls(True)
        self.status_label.setText("Playing...")
        
        # Start playback in thread
        threading.Thread(
            target=self._play_text_thread,
            args=(text,),
            daemon=True
        ).start()
    
    def _play_text_thread(self, text):
        try:
            # Configure voice
            voice_idx = self.voice_combo.currentData()
            voices = self.engine.getProperty('voices')
            self.engine.setProperty('voice', voices[voice_idx].id)
            self.engine.setProperty('rate', self.rate_slider.value())
            self.engine.setProperty('volume', self.volume_slider.value()/100)
            
            # Split into chunks for progress tracking
            chunks = self._split_text(text)
            total_chunks = len(chunks)
            
            for i, chunk in enumerate(chunks):
                if self.stop_requested:
                    break
                    
                # Update progress
                progress = int((i + 1) / total_chunks * 100)
                self.update_progress(progress, f"Playing chunk {i+1}/{total_chunks}")
                
                # Speak the chunk
                self.engine.say(chunk)
                self.engine.runAndWait()
                
                # Short pause between chunks
                if i < total_chunks - 1 and not self.stop_requested:
                    time.sleep(0.2)
            
            if not self.stop_requested:
                self.update_status("Playback complete")
        
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
        
        finally:
            self.is_playing = False
            self.toggle_play_controls(False)
    
    def stop_playing(self):
        self.stop_requested = True
        if self.engine:
            self.engine.stop()
        self.update_status("Playback stopped")
    
    def start_conversion(self):
        if self.is_converting or not self.engine:
            return
            
        text = self.text_area.toPlainText().strip()
        if not text:
            self.show_message("Please enter some text to convert.", "warning")
            return
            
        output_dir = self.output_dir.text()
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                self.show_message(f"Cannot create directory: {str(e)}", "error")
                return
        
        self.is_converting = True
        self.stop_requested = False
        self.toggle_convert_controls(True)
        self.status_label.setText("Converting...")
        
        # Start conversion in thread
        threading.Thread(
            target=self._convert_text_thread,
            args=(text, output_dir),
            daemon=True
        ).start()
    
    def _convert_text_thread(self, text, output_dir):
        try:
            # Configure voice
            voice_idx = self.voice_combo.currentData()
            voices = self.engine.getProperty('voices')
            self.engine.setProperty('voice', voices[voice_idx].id)
            self.engine.setProperty('rate', self.rate_slider.value())
            self.engine.setProperty('volume', self.volume_slider.value()/100)
            
            # Get output settings
            output_format = self.format_combo.currentText()
            filename = self.filename.text().strip() or "audiobook"
            output_file = os.path.join(output_dir, f"{filename}.mp3")
            
            # Split text for processing
            chunks = self._split_text(text)
            total_chunks = len(chunks)
            
            # Temporary storage for MP3 chunks
            temp_files = []
            temp_dir = os.path.join(output_dir, "temp_audio")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Create a single output file writer
            if output_format in ["Save as MP3", "Both"]:
                try:
                    from pydub import AudioSegment
                    combined = AudioSegment.empty()
                    save_to_file = True
                except ImportError:
                    self.update_status("pydub not available - cannot save MP3")
                    save_to_file = False
            else:
                save_to_file = False
            
            for i, chunk in enumerate(chunks):
                if self.stop_requested:
                    break
                    
                # Update progress
                progress = int((i + 1) / total_chunks * 100)
                self.update_progress(progress, f"Processing chunk {i+1}/{total_chunks}")
                
                # Play chunk if requested
                if output_format in ["Play Only", "Both"]:
                    self.engine.say(chunk)
                    self.engine.runAndWait()
                    
                    # Pause between chunks
                    if i < total_chunks - 1 and not self.stop_requested:
                        time.sleep(self.pause_duration.value())
                
                # Save to file if requested
                if save_to_file:
                    temp_file = os.path.join(temp_dir, f"chunk_{i}.wav")  # Save as WAV first
                    self.engine.save_to_file(chunk, temp_file)
                    self.engine.runAndWait()
                    
                    # Convert to AudioSegment and add to combined
                    sound = AudioSegment.from_wav(temp_file)
                    combined += sound
                    
                    # Add pause between chunks except the last one
                    if i < total_chunks - 1:
                        combined += AudioSegment.silent(
                            duration=int(self.pause_duration.value() * 1000)
                        )
                    
                    temp_files.append(temp_file)
            
            # Save final MP3 file
            if not self.stop_requested and save_to_file and len(combined) > 0:
                try:
                    combined.export(output_file, format="mp3", bitrate="64k")
                    self.update_status(f"Successfully saved to {output_file}")
                except Exception as e:
                    self.update_status(f"Error saving MP3: {str(e)}")
            
            if not self.stop_requested:
                self.update_status("Conversion complete!")
        
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
        
        finally:
            # Cleanup temporary files
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                for file in temp_files:
                    if os.path.exists(file):
                        os.remove(file)
                os.rmdir(temp_dir)
            
            self.is_converting = False
            self.toggle_convert_controls(False)
    
    def stop_conversion(self):
        self.stop_requested = True
        if self.engine:
            self.engine.stop()
        self.update_status("Conversion stopped")
    
    def _split_text(self, text):
        """Optimized text splitting with paragraph awareness"""
        # Split by paragraphs first
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Further split long paragraphs into sentences
        chunks = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            if len(para) > 500:  # Split long paragraphs
                sentences = re.split(r'(?<=[.!?])\s+', para)
                current_chunk = []
                current_length = 0
                
                for sentence in sentences:
                    if current_length + len(sentence) > 500 and current_chunk:
                        chunks.append(' '.join(current_chunk))
                        current_chunk = []
                        current_length = 0
                    
                    current_chunk.append(sentence)
                    current_length += len(sentence)
                
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
            else:
                chunks.append(para)
        
        return chunks
    
    def toggle_play_controls(self, playing):
        self.play_button.setEnabled(not playing)
        self.stop_play_button.setEnabled(playing)
        self.convert_button.setEnabled(not playing)
    
    def toggle_convert_controls(self, converting):
        self.convert_button.setEnabled(not converting)
        self.stop_button.setEnabled(converting)
        self.play_button.setEnabled(not converting)
    
    def update_progress(self, value, message=""):
        QtCore.QMetaObject.invokeMethod(
            self.progress_bar, "setValue",
            QtCore.Qt.QueuedConnection,
            QtCore.Q_ARG(int, value)
        )
        if message:
            self.update_status(message)
    
    def update_status(self, message):
        QtCore.QMetaObject.invokeMethod(
            self.status_label, "setText",
            QtCore.Qt.QueuedConnection,
            QtCore.Q_ARG(str, message)
        )
    
    def show_message(self, message, msg_type="info"):
        if msg_type == "info":
            QMessageBox.information(self, "Information", message)
        elif msg_type == "warning":
            QMessageBox.warning(self, "Warning", message)
        else:
            QMessageBox.critical(self, "Error", message)

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    converter = AudioBookConverter()
    converter.show()
    sys.exit(app.exec_())
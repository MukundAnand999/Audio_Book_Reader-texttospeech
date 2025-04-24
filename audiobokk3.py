import os
import time
import re
import threading
import pyttsx3
from pydub import AudioSegment
from pydub.playback import play
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QFileDialog, QProgressBar, QTextEdit, QMessageBox

class AudioBookConverter(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.engine = None
        self.is_playing = False
        self.init_engine()
        self.initUI()
        
    def init_engine(self):
        try:
            self.engine = pyttsx3.init()
            # Set default properties
            self.engine.setProperty('rate', 150)
            self.engine.setProperty('volume', 0.9)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not initialize TTS engine: {str(e)}")
    
    def initUI(self):
        # Set black and yellow color scheme
        self.setStyleSheet("""
            QWidget {
                background-color: #000000;
                color: #FFFF00;
            }
            QTextEdit, QLineEdit, QComboBox {
                background-color: #222222;
                color: #FFFF00;
                border: 1px solid #444444;
            }
            QPushButton {
                background-color: #333300;
                color: #FFFF00;
                border: 1px solid #555500;
                padding: 5px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #444400;
            }
            QPushButton:pressed {
                background-color: #222200;
            }
            QPushButton:disabled {
                background-color: #111100;
                color: #888800;
            }
            QGroupBox {
                border: 2px solid #555500;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: #333300;
                margin: 2px 0;
            }
            QSlider::handle:horizontal {
                background: #FFFF00;
                border: 1px solid #444400;
                width: 18px;
                margin: -5px 0;
                border-radius: 3px;
            }
            QProgressBar {
                border: 1px solid #444400;
                text-align: center;
                color: #FFFF00;
            }
            QProgressBar::chunk {
                background-color: #555500;
                width: 1px;
            }
        """)

        self.setWindowTitle("Advanced Text-to-Speech Audiobook")
        self.setGeometry(100, 100, 900, 700)
        layout = QtWidgets.QVBoxLayout()

        # Text input area with play controls
        text_group = QtWidgets.QGroupBox("Text Input")
        text_layout = QtWidgets.QVBoxLayout()
        
        # Text edit with play controls
        control_layout = QtWidgets.QHBoxLayout()
        self.play_button = QtWidgets.QPushButton("▶ Play Text")
        self.play_button.clicked.connect(self.play_text)
        control_layout.addWidget(self.play_button)
        
        self.stop_play_button = QtWidgets.QPushButton("■ Stop Playing")
        self.stop_play_button.clicked.connect(self.stop_playing)
        self.stop_play_button.setEnabled(False)
        control_layout.addWidget(self.stop_play_button)
        
        self.clear_button = QtWidgets.QPushButton("Clear Text")
        self.clear_button.clicked.connect(self.clear_text)
        control_layout.addWidget(self.clear_button)
        
        text_layout.addLayout(control_layout)
        
        self.text_area = QTextEdit()
        self.text_area.setPlaceholderText("Enter or paste your text here...")
        self.text_area.setStyleSheet("font-size: 14px;")
        text_layout.addWidget(self.text_area)
        
        text_group.setLayout(text_layout)
        layout.addWidget(text_group)

        # Output directory selection
        output_layout = QtWidgets.QHBoxLayout()
        output_label = QtWidgets.QLabel("Output Directory:")
        output_layout.addWidget(output_label)
        
        self.output_dir_entry = QtWidgets.QLineEdit(os.path.expanduser("~/Audiobooks"))
        output_layout.addWidget(self.output_dir_entry)

        browse_button = QtWidgets.QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(browse_button)

        layout.addLayout(output_layout)

        # Voice settings
        voice_group = QtWidgets.QGroupBox("Voice Settings")
        voice_layout = QtWidgets.QGridLayout()
        
        # Voice selection
        voice_layout.addWidget(QtWidgets.QLabel("Voice:"), 0, 0)
        self.voice_combo = QtWidgets.QComboBox()
        self.populate_voices()
        voice_layout.addWidget(self.voice_combo, 0, 1, 1, 2)
        
        # Rate control
        voice_layout.addWidget(QtWidgets.QLabel("Speech Rate:"), 1, 0)
        self.rate_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.rate_slider.setRange(50, 300)
        self.rate_slider.setValue(150)
        self.rate_slider.valueChanged.connect(self.update_rate_label)
        voice_layout.addWidget(self.rate_slider, 1, 1)
        self.rate_label = QtWidgets.QLabel("150 words/min")
        voice_layout.addWidget(self.rate_label, 1, 2)
        
        # Volume control
        voice_layout.addWidget(QtWidgets.QLabel("Volume:"), 2, 0)
        self.volume_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(90)
        self.volume_slider.valueChanged.connect(self.update_volume_label)
        voice_layout.addWidget(self.volume_slider, 2, 1)
        self.volume_label = QtWidgets.QLabel("90%")
        voice_layout.addWidget(self.volume_label, 2, 2)
        
        # Pitch control
        voice_layout.addWidget(QtWidgets.QLabel("Pitch:"), 3, 0)
        self.pitch_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.pitch_slider.setRange(0, 200)
        self.pitch_slider.setValue(100)
        self.pitch_slider.valueChanged.connect(self.update_pitch_label)
        voice_layout.addWidget(self.pitch_slider, 3, 1)
        self.pitch_label = QtWidgets.QLabel("Normal")
        voice_layout.addWidget(self.pitch_label, 3, 2)
        
        # Voice effects
        voice_layout.addWidget(QtWidgets.QLabel("Effect:"), 4, 0)
        self.effect_combo = QtWidgets.QComboBox()
        self.effect_combo.addItems(["None", "Echo", "Whisper", "Robot", "Slow Motion"])
        voice_layout.addWidget(self.effect_combo, 4, 1, 1, 2)
        
        voice_group.setLayout(voice_layout)
        layout.addWidget(voice_group)

        # Pacing settings
        pacing_group = QtWidgets.QGroupBox("Pacing Settings")
        pacing_layout = QtWidgets.QGridLayout()
        
        pause_label = QtWidgets.QLabel("Pause between paragraphs (s):")
        pacing_layout.addWidget(pause_label, 0, 0)
        self.pause_duration_entry = QtWidgets.QDoubleSpinBox()
        self.pause_duration_entry.setRange(0.1, 10.0)
        self.pause_duration_entry.setValue(1.0)
        self.pause_duration_entry.setSingleStep(0.1)
        pacing_layout.addWidget(self.pause_duration_entry, 0, 1)
        
        words_label = QtWidgets.QLabel("Words per minute:")
        pacing_layout.addWidget(words_label, 1, 0)
        self.words_per_minute = QtWidgets.QSpinBox()
        self.words_per_minute.setRange(50, 300)
        self.words_per_minute.setValue(180)
        pacing_layout.addWidget(self.words_per_minute, 1, 1)
        
        pacing_group.setLayout(pacing_layout)
        layout.addWidget(pacing_group)

        # Output format
        format_group = QtWidgets.QGroupBox("Output Settings")
        format_layout = QtWidgets.QGridLayout()
        
        format_layout.addWidget(QtWidgets.QLabel("Output Format:"), 0, 0)
        self.format_combo = QtWidgets.QComboBox()
        self.format_combo.addItems(["Play Only", "Save as MP3", "Both"])
        format_layout.addWidget(self.format_combo, 0, 1)
        
        format_layout.addWidget(QtWidgets.QLabel("File Name:"), 1, 0)
        self.filename_entry = QtWidgets.QLineEdit("audiobook")
        format_layout.addWidget(self.filename_entry, 1, 1)
        
        format_layout.addWidget(QtWidgets.QLabel("Save Location:"), 2, 0)
        self.save_location_combo = QtWidgets.QComboBox()
        self.save_location_combo.addItems(["Same as Output Directory", "Choose Different Location"])
        format_layout.addWidget(self.save_location_combo, 2, 1)
        
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        # Control buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        self.convert_button = QtWidgets.QPushButton("🔊 Convert to Audiobook")
        self.convert_button.clicked.connect(self.convert_to_audio)
        button_layout.addWidget(self.convert_button)
        
        self.stop_button = QtWidgets.QPushButton("🛑 Stop Conversion")
        self.stop_button.clicked.connect(self.stop_conversion)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        self.preview_button = QtWidgets.QPushButton("🎧 Preview Voice")
        self.preview_button.clicked.connect(self.preview_voice)
        button_layout.addWidget(self.preview_button)
        
        layout.addLayout(button_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                height: 20px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #FFCC00;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setStyleSheet("font-size: 12px; color: #FFCC00;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        
        # Conversion control flag
        self.is_converting = False

    def populate_voices(self):
        if not self.engine:
            return
            
        voices = self.engine.getProperty('voices')
        self.voice_combo.clear()
        for i, voice in enumerate(voices):
            self.voice_combo.addItem(f"{voice.name} ({voice.id})", i)

    def update_rate_label(self, value):
        self.rate_label.setText(f"{value} words/min")
        if self.engine:
            self.engine.setProperty('rate', value)

    def update_volume_label(self, value):
        self.volume_label.setText(f"{value}%")
        if self.engine:
            self.engine.setProperty('volume', value/100)

    def update_pitch_label(self, value):
        if value < 90:
            pitch_text = "Low"
        elif value > 110:
            pitch_text = "High"
        else:
            pitch_text = "Normal"
        self.pitch_label.setText(pitch_text)

    def browse_output_dir(self):
        dir_name = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if dir_name:
            self.output_dir_entry.setText(dir_name)

    def clear_text(self):
        self.text_area.clear()

    def preview_voice(self):
        if not self.engine:
            return
            
        # Save current properties
        old_voice = self.engine.getProperty('voice')
        old_rate = self.engine.getProperty('rate')
        old_volume = self.engine.getProperty('volume')
        
        # Set preview properties
        voice_index = self.voice_combo.currentData()
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[voice_index].id)
        self.engine.setProperty('rate', self.rate_slider.value())
        self.engine.setProperty('volume', self.volume_slider.value()/100)
        
        # Apply pitch effect
        pitch = self.pitch_slider.value()
        if pitch != 100:
            self.engine.setProperty('pitch', pitch/100)
        
        # Speak preview with selected effect
        effect = self.effect_combo.currentText()
        preview_text = {
            "None": "This is a preview of the current voice settings.",
            "Echo": "Echo... echo... echo effect...",
            "Whisper": "This is a whisper effect preview...",
            "Robot": "I. AM. A. ROBOT. VOICE. EFFECT.",
            "Slow Motion": "This... is... a... slow... motion... preview..."
        }.get(effect, "Preview")
        
        self.engine.say(preview_text)
        self.engine.runAndWait()
        
        # Restore original properties
        self.engine.setProperty('voice', old_voice)
        self.engine.setProperty('rate', old_rate)
        self.engine.setProperty('volume', old_volume)
        if pitch != 100:
            self.engine.setProperty('pitch', 1.0)

    def play_text(self):
        if not self.engine or self.is_playing:
            return
            
        text = self.text_area.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Warning", "Please enter some text to play.")
            return
            
        self.is_playing = True
        self.play_button.setEnabled(False)
        self.stop_play_button.setEnabled(True)
        self.status_label.setText("Playing text...")
        
        # Start playing in a separate thread
        threading.Thread(
            target=self._play_text_thread,
            args=(text,),
            daemon=True
        ).start()

    def _play_text_thread(self, text):
        try:
            # Set voice properties
            voice_index = self.voice_combo.currentData()
            voices = self.engine.getProperty('voices')
            self.engine.setProperty('voice', voices[voice_index].id)
            self.engine.setProperty('rate', self.rate_slider.value())
            self.engine.setProperty('volume', self.volume_slider.value()/100)
            
            # Apply pitch effect
            pitch = self.pitch_slider.value()
            if pitch != 100:
                self.engine.setProperty('pitch', pitch/100)
            
            # Split text into paragraphs
            paragraphs = re.split(r'\n\s*\n', text)
            
            for paragraph in paragraphs:
                if not self.is_playing:
                    break
                    
                paragraph = paragraph.strip()
                if not paragraph:
                    continue
                
                # Apply voice effect if selected
                effect = self.effect_combo.currentText()
                if effect != "None":
                    paragraph = self.apply_voice_effect(paragraph, effect)
                
                # Speak the paragraph
                self.engine.say(paragraph)
                self.engine.runAndWait()
                
        except Exception as e:
            QtCore.QMetaObject.invokeMethod(
                self.status_label,
                "setText",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, f"Error: {str(e)}")
            )
        
        finally:
            self.is_playing = False
            QtCore.QMetaObject.invokeMethod(
                self.play_button,
                "setEnabled",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(bool, True)
            )
            QtCore.QMetaObject.invokeMethod(
                self.stop_play_button,
                "setEnabled",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(bool, False)
            )
            if self.is_playing:
                QtCore.QMetaObject.invokeMethod(
                    self.status_label,
                    "setText",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(str, "Playback complete")
                )

    def apply_voice_effect(self, text, effect):
        """Modify text to simulate different voice effects"""
        if effect == "Echo":
            words = text.split()
            return " ... ".join([f"{word} {word}" for word in words])
        elif effect == "Whisper":
            return f"(whispering) {text.lower()}"
        elif effect == "Robot":
            return " ".join([word.upper() for word in text.split()])
        elif effect == "Slow Motion":
            return " ... ".join(text.split())
        return text

    def stop_playing(self):
        self.is_playing = False
        if self.engine:
            self.engine.stop()
        self.status_label.setText("Playback stopped")

    def convert_to_audio(self):
        if self.is_converting:
            return
            
        text = self.text_area.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Warning", "Please enter some text to convert.")
            return
            
        if not self.engine:
            QMessageBox.critical(self, "Error", "Text-to-speech engine not initialized.")
            return
            
        output_dir = self.output_dir_entry.text()
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not create output directory: {str(e)}")
                return

        # Get voice settings
        voice_index = self.voice_combo.currentData()
        voices = self.engine.getProperty('voices')
        voice_config = {
            'voice': voices[voice_index].id,
            'rate': self.rate_slider.value(),
            'volume': self.volume_slider.value()/100,
            'pitch': self.pitch_slider.value()/100,
            'effect': self.effect_combo.currentText()
        }

        # Get pacing settings
        pause_duration = self.pause_duration_entry.value()
        words_per_minute = self.words_per_minute.value()
        
        # Get output format
        output_format = self.format_combo.currentText()
        filename = self.filename_entry.text().strip() or "audiobook"
        
        # Determine save location
        if self.save_location_combo.currentIndex() == 1:  # Choose Different Location
            save_dir = QFileDialog.getExistingDirectory(self, "Select Save Location")
            if not save_dir:
                return
        else:
            save_dir = output_dir
        
        # Disable controls during conversion
        self.is_converting = True
        self.convert_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("Converting...")
        
        # Start conversion in a separate thread
        threading.Thread(
            target=self.advanced_text_to_audio_book,
            args=(text, save_dir, voice_config, pause_duration, words_per_minute, output_format, filename),
            daemon=True
        ).start()

    def stop_conversion(self):
        self.is_converting = False
        if self.engine:
            self.engine.stop()
        self.status_label.setText("Conversion stopped")

    def advanced_text_to_audio_book(self, text, output_dir, voice_config, pause_duration, words_per_minute, output_format, filename):
        try:
            # Set voice properties
            self.engine.setProperty('voice', voice_config['voice'])
            self.engine.setProperty('rate', voice_config['rate'])
            self.engine.setProperty('volume', voice_config['volume'])
            if voice_config['pitch'] != 1.0:
                self.engine.setProperty('pitch', voice_config['pitch'])
            
            # Split text into paragraphs
            paragraphs = re.split(r'\n\s*\n', text)
            total_paragraphs = len(paragraphs)
            
            # Prepare for saving to file if needed
            if output_format in ["Save as MP3", "Both"]:
                output_file = os.path.join(output_dir, f"{filename}.mp3")
                # Create a temporary directory for individual MP3 files
                temp_dir = os.path.join(output_dir, "temp")
                os.makedirs(temp_dir, exist_ok=True)
                temp_files = []
            
            for i, paragraph in enumerate(paragraphs):
                if not self.is_converting:
                    break
                    
                paragraph = paragraph.strip()
                if not paragraph:
                    continue
                
                # Apply voice effect if selected
                if voice_config['effect'] != "None":
                    paragraph = self.apply_voice_effect(paragraph, voice_config['effect'])
                
                # Update progress
                progress = int((i + 1) / total_paragraphs * 100)
                QtCore.QMetaObject.invokeMethod(
                    self.progress_bar, 
                    "setValue", 
                    QtCore.Qt.QueuedConnection, 
                    QtCore.Q_ARG(int, progress)
                )
                QtCore.QMetaObject.invokeMethod(
                    self.status_label,
                    "setText",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(str, f"Processing paragraph {i+1} of {total_paragraphs}")
                )
                
                if output_format in ["Play Only", "Both"]:
                    # Speak the paragraph
                    self.engine.say(paragraph)
                    self.engine.runAndWait()
                    
                    # Add pause between paragraphs
                    if i < total_paragraphs - 1:
                        time.sleep(pause_duration)
                
                if output_format in ["Save as MP3", "Both"]:
                    # Save paragraph to temporary file
                    temp_file = os.path.join(temp_dir, f"para_{i}.mp3")
                    self.engine.save_to_file(paragraph, temp_file)
                    self.engine.runAndWait()
                    temp_files.append(temp_file)
            
            if output_format in ["Save as MP3", "Both"] and self.is_converting and temp_files:
                # Combine all temporary files into one MP3
                self.status_label.setText("Combining audio files...")
                combined = AudioSegment.empty()
                for temp_file in temp_files:
                    sound = AudioSegment.from_mp3(temp_file)
                    combined += sound
                    # Add pause between paragraphs in the output file
                    combined += AudioSegment.silent(duration=pause_duration*1000)  # pydub uses milliseconds
                    os.remove(temp_file)
                
                # Export the combined audio
                combined.export(output_file, format="mp3")
                os.rmdir(temp_dir)
                
                QtCore.QMetaObject.invokeMethod(
                    self.status_label,
                    "setText",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(str, f"Saved to {output_file}")
                )
            
            if self.is_converting:
                QtCore.QMetaObject.invokeMethod(
                    self.status_label,
                    "setText",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(str, "Conversion complete!")
                )
        
        except Exception as e:
            QtCore.QMetaObject.invokeMethod(
                self.status_label,
                "setText",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, f"Error: {str(e)}")
            )
        
        finally:
            # Re-enable controls
            QtCore.QMetaObject.invokeMethod(
                self.convert_button,
                "setEnabled",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(bool, True)
            )
            QtCore.QMetaObject.invokeMethod(
                self.stop_button,
                "setEnabled",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(bool, False)
            )
            self.is_converting = False

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = AudioBookConverter()
    window.show()
    sys.exit(app.exec_())
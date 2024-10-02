# -*- coding: utf-8 -*-
"""
Created on Fri Dec 15 17:56:34 2023

@author: Polar
"""
import sys
import os
import json
import sounddevice as sd
from PyQt6.QtWidgets import QApplication, QWidget, QTabWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QDoubleSpinBox, QSpinBox, QComboBox, QCheckBox, QPlainTextEdit,QFileDialog


class Configurator(QWidget):
    def __init__(self):
        super().__init__()
        devices = sd.query_devices()
        input_devices = [str(device['index'])+" "+device['name'] for device in devices if device.get('max_input_channels') > 0 and device.get('max_output_channels') == 0]
        output_devices = [str(device['index'])+" "+device['name'] for device in devices if device.get('max_output_channels') > 0 and device.get('max_input_channels') == 0]
        
        # Initialize parameters with default values, limits, and increments
        self.parameters = {
            "Prompt Settings": {
                "add_prompt_threshold": {"default": -0.5, "min": -2.0, "max": 0.0, "increment": 0.1},
                "prompt_reset_on_temperature": {"default": True},
                "special_words": {"default": ""},
            },
            "Audio Settings": {
                "sample_rate": {"default": 16000, "min": 1000, "max": 100000, "increment": 100},
                "sample_duration": {"default": 5, "min": 3, "max": 10, "increment": 1},
                "device_input": {"default": "CABLE Output (VB-Audio Virtual , MME","options":input_devices},
                "device_output": {"default": "CABLE Input (VB-Audio Virtual , MME","options":output_devices},
                "model": {"default": "large-v3", "options": ["medium", "large-v1", "large-v2", "large-v3"]},
                "circular_audio": {"default": True},
                "audio_overlap": {"default": 2, "min": 1, "max": 5, "increment": 1},
            },
            "Model Settings": {
                "model": {"default": "large-v3", "options": ["medium", "large-v1", "large-v2", "large-v3"]},
                "task": {"default": "translate", "options": ["translate", "transcribe"]},
                "beam_size": {"default": 5, "min": 1, "max": 10, "increment": 1},
                "best_of": {"default": 3, "min": 1, "max": 5, "increment": 1},
                "patience": {"default": 1.5, "min": 1, "max": 10, "increment": 0.1},
                "repetition_penalty": {"default": 1.05, "min": 1.00, "max": 5.00, "increment": 0.05},
                "log_prob_threshold": {"default": -0.99, "min": -2.0, "max": 0.0, "increment": 0.01},
                "no_speech_threshold": {"default": 0.8, "min": 0.0, "max": 1.0, "increment": 0.1},
                "condition_on_previous_text": {"default": True},
                "word_timestamps": {"default": True},
                "vad_filter": {"default": True},
                "vad_threshold": {"default": 0.6, "min": 0.0, "max": 1.0, "increment": 0.1},
                "min_silence_duration_ms": {"default": 500, "min": 100, "max": 2000, "increment": 100},
            },
            "Other Settings": {
                "debug_mode": {"default": False},
            },
        }

        self.fixed_parameters = {
            "block_size": None,  # calculated in post_calculation
            "file_only_mode": False,
            "audio_file":"",
            "starting_words": "vtuber,hololive,japanese and english,",
        }

        self.init_ui()
        self.resize(500, 600)
        
    def init_ui(self):
        tabs = QTabWidget()

        for tab_name, params in self.parameters.items():
            tab = self.create_tab(tab_name, params)
            tabs.addTab(tab, tab_name)

        layout = QVBoxLayout()
        layout.addWidget(tabs)

        save_button = QPushButton("Replace and Save Configuration")
        save_button.clicked.connect(self.save_configuration)
        layout.addWidget(save_button)
        
        proceed_button = QPushButton("Proceed with pre-saved configuration")
        proceed_button.clicked.connect(self.proceed_configuration)
        layout.addWidget(proceed_button)
        
        self.setLayout(layout)
        self.setWindowTitle("Program Configuration")

    def create_tab(self, tab_name, params):
        tab = QWidget()
        layout = QVBoxLayout()
        combo_box_param = ["model","task","device_input","device_output"]
        for param, info in params.items():
            label = QLabel(f"{param.capitalize()}:")
            layout.addWidget(label)

            # if param == "model" or param == "task":
            if param in combo_box_param:
                combo_box = QComboBox()
                combo_box.addItems(info["options"])
                combo_box.setCurrentText(info["default"])
                combo_box.currentTextChanged.connect(lambda text, param=param: self.update_parameter(tab_name,param, text))
                layout.addWidget(combo_box)
            elif param == "special_words":  # Modified code for 'special_words'
                text_edit = QPlainTextEdit()
                text_edit.setPlainText(info["default"])
                text_edit.textChanged.connect(lambda param=param: self.update_parameter(tab_name, param, text_edit.toPlainText()))
                layout.addWidget(text_edit)
            elif isinstance(info["default"], bool):
                checkbox = QCheckBox()
                checkbox.setChecked(info["default"])
                checkbox.setStyleSheet("QCheckBox::indicator { width: 40px; height: 20px; }")
                checkbox.stateChanged.connect(lambda state, param=param: self.update_parameter(tab_name,param, state == 2))
                layout.addWidget(checkbox)
            elif isinstance(info["default"], int):
                spinbox = QSpinBox()
                spinbox.setRange(info["min"], info["max"])
                spinbox.setValue(info["default"])
                spinbox.setSingleStep(info.get("increment", 1))
                spinbox.valueChanged.connect(lambda value, param=param: self.update_parameter(tab_name,param, value))
                layout.addWidget(spinbox)
            elif isinstance(info["default"], float):
                spinbox = QDoubleSpinBox()
                spinbox.setRange(info["min"], info["max"])
                spinbox.setValue(info["default"])
                spinbox.setSingleStep(info.get("increment", 1))
                spinbox.valueChanged.connect(lambda value, param=param: self.update_parameter(tab_name,param, value))
                layout.addWidget(spinbox)
            else:
                input_field = QLineEdit(str(info["default"]))
                input_field.textChanged.connect(lambda text, param=param: self.update_parameter(tab_name,param, text))
                layout.addWidget(input_field)

        tab.setLayout(layout)
        if tab_name == "Other Settings":
            File_Only_button = QPushButton('File Only Mode')
            File_Only_button.clicked.connect(self.showFileDialog)
            layout.addWidget(File_Only_button)
            
        return tab

    def update_parameter(self, tab_name,param, value):
        self.parameters[tab_name][param]["default"] = value
        
        if param == "device_input" or param == "device_output":
            #print(self.parameters[tab_name][param]["default"])
            self.parameters[tab_name][param]["default"] = int(self.parameters[tab_name][param]["default"][:2])
            #print(self.parameters[tab_name][param]["default"])
            
            

    def post_calculation(self):
        #DEAL WITH USER MISUSE
        sample_rate = self.parameters["Audio Settings"]["sample_rate"]["default"]
        sample_duration = self.parameters["Audio Settings"]["sample_duration"]["default"]
        audio_overlap = self.parameters["Audio Settings"]["audio_overlap"]["default"]
        
        self.fixed_parameters["block_size"] = int(sample_rate * sample_duration)
        
        if audio_overlap > sample_duration:
            print("USER MISUSE, setting audio_overlap to max of sample_duration")
            self.parameters["Audio Settings"]["audio_overlap"]["default"] = sample_duration
    
    def showFileDialog(self):
        file_name = QFileDialog.getOpenFileName(parent = self, 
                                               caption = "QFileDialog.getOpenFileName()",
                                               directory= os.getcwd(),
                                               filter= "All Files (*);;Audio Files (*.mp3)",
                                               initialFilter="Audio Files (*.mp3)")
        if file_name:
            print("Selected file:", file_name)
            self.fixed_parameters["file_only_mode"] = True
            self.fixed_parameters["audio_file"] = file_name[0]
    
    def save_configuration(self):
        self.post_calculation()
        # Save both regular and fixed parameters to a file
        configuration = {param: info["default"] for _, params in self.parameters.items() for param, info in params.items()}
        configuration.update(self.fixed_parameters)

        with open("config_live_transcript.json", "w") as config_file:
            json.dump(configuration, config_file, indent=4)

        print("Configuration saved to 'config_live_transcript.json'.")
        QApplication.quit()

    def proceed_configuration(self):
        print("Pre-saved Configuration being used")
        QApplication.quit()

def main():
    app = QApplication(sys.argv)
    configurator = Configurator()
    configurator.show()
    app.exec()


if __name__ == '__main__':
    main()

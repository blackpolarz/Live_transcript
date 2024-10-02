# -*- coding: utf-8 -*-
"""
Created on Fri Dec 15 17:56:34 2023

@author: BlackPolar
"""

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
    QGridLayout, QLabel, QMainWindow, QPlainTextEdit,
    QPushButton, QSizePolicy, QSpacerItem, QSpinBox,
    QStackedWidget, QStatusBar, QVBoxLayout, QWidget,QFileDialog)
import sys
import sounddevice as sd
import json
import os

def create_icon_button(parent, icon_path, object_name,icon_text,exclusive):
    button = QPushButton(parent)
    button.setObjectName(object_name)
    icon = QIcon()
    icon.addFile(icon_path, QSize(), QIcon.Mode.Normal, QIcon.State.Off)
    button.setIcon(icon)
    button.setCheckable(True)
    button.setAutoExclusive(exclusive)
    button.setText(icon_text)
    return button

def create_label(parent,object_name,text):
    label = QLabel(parent)
    label.setObjectName(object_name)
    label.setAlignment(Qt.AlignCenter)
    label.setWordWrap(True)
    label.setText(text)
    return label

def create_widget(widget_type,page,widget_name,layout,row,col,row_span,col_span,**kwargs):
    match widget_type:
        case "QSpinBox":
            widget = QSpinBox(page)
            widget.setObjectName(widget_name)
            widget.setEnabled(kwargs.get("enabled",True))
            widget.setWrapping(kwargs.get("wrapping",True))
            widget.setAlignment(Qt.AlignCenter)
            widget.setMinimum(kwargs.get("minimum"))
            widget.setMaximum(kwargs.get("maximum"))
            widget.setSingleStep(kwargs.get("single_step",1))
            widget.setValue(kwargs.get("value"))
            layout.addWidget(widget,row,col,row_span,col_span)
        
        case "QDoubleSpinBox":
            widget = QDoubleSpinBox(page)
            widget.setObjectName(widget_name)
            widget.setAlignment(Qt.AlignCenter)
            widget.setMinimum(kwargs.get("minimum"))
            widget.setMaximum(kwargs.get("maximum"))
            widget.setSingleStep(kwargs.get("single_step"))
            widget.setValue(kwargs.get("value"))
            layout.addWidget(widget,row,col,row_span,col_span)
        
        case "QComboBox":
            widget = QComboBox(page)
            widget.setObjectName(widget_name)
            widget.setEditable(kwargs.get("editable"))
            widget.addItems(kwargs.get("items"))
            widget.setCurrentIndex(kwargs.get("current_index",0))
            layout.addWidget(widget,row,col,row_span,col_span)
            
        case "QCheckBox":
            widget = QCheckBox(page)
            widget.setObjectName(widget_name)
            widget.setEnabled(kwargs.get("enabled",True))
            widget.setLayoutDirection(Qt.RightToLeft)
            widget.setAutoExclusive(kwargs.get("exclusive"))
            widget.setText(kwargs.get("text"))
            widget.setChecked(kwargs.get("checked",True))
            
            #Special case to handle alignment problem in checkboxes.
            if 'alignment' in kwargs:
                layout.addWidget(widget,row,col,row_span,col_span)
            else:
                layout.addWidget(widget,row,col,row_span,col_span,Qt.AlignCenter)
                
    return widget


class Ui_MainWindow(object):
    
    
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1000, 700)
        devices = sd.query_devices()
        input_devices = [None]+[str(device['index'])+" "+device['name'] for device in devices if device.get('max_input_channels') > 0 and device.get('max_output_channels') == 0]
        output_devices = [None]+[str(device['index'])+" "+device['name'] for device in devices if device.get('max_output_channels') > 0 and device.get('max_input_channels') == 0]
        model_options = ["medium", "large-v1", "large-v2", "large-v3"]
        task_options = ["translate", "transcribe"]
        

        #Central Widget
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        
        #Collapsed Widget
        self.Iconwid = QWidget(self.centralwidget)
        self.Iconwid.setObjectName(u"Iconwid")
        self.Iconwid.setStyleSheet(u"QWidget{\n"
                                   "	background-color: rgb(58, 58, 58);\n"
                                   "}\n"
                                   "\n"
                                   "QPushButton{\n"
                                   "	color:white;\n"
                                   "	height:30;\n"
                                   "	border:none;\n"
                                   "}\n"
                                   "")
        
        self.verticalLayout_3 = QVBoxLayout(self.Iconwid)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(10, 10, 10, 10)
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setSpacing(20)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 20)
        
        button_configurations_1 = [
            { "name": "menuButton_1", "text":"","path": "./icons/menu-icon.png", "exclusive":True,"layout_pos":"verticalLayout_2"},
            { "name": "audioButton_1", "text":"","path": "./icons/audio-icon.png","exclusive":True,"layout_pos":"verticalLayout_2"},
            { "name": "promptButton_1", "text":"","path": "./icons/prompt-icon.png","exclusive":True,"layout_pos":"verticalLayout_2"},
            { "name": "modelButton_1", "text":"","path": "./icons/closed-book-icon.png","exclusive":True,"layout_pos":"verticalLayout_2"},
            { "name": "settingButton_1", "text":"","path": "./icons/setting-icon.png","exclusive":True,"layout_pos":"verticalLayout_2"},
            ]
        button_configurations_2 = [
            { "name": "menuButton_2", "text":"Menu","path": "./icons/menu-icon.png", "exclusive":False,"layout_pos":"verticalLayout"},
            { "name": "audioButton_2", "text":"Audio","path": "./icons/audio-icon.png","exclusive":True,"layout_pos":"verticalLayout"},
            { "name": "promptButton_2", "text":"Prompt","path": "./icons/prompt-icon.png","exclusive":True,"layout_pos":"verticalLayout"},
            { "name": "modelButton_2", "text":"Model","path": "./icons/book-icon.png","exclusive":True,"layout_pos":"verticalLayout"},
            { "name": "settingButton_2", "text":"Others","path": "./icons/setting-icon.png","exclusive":True,"layout_pos":"verticalLayout"},
            ]
        
        self.buttons = {}
        for button_config in button_configurations_1:    
            icon_path = button_config['path']
            object_name = button_config['name']
            icon_text = button_config['text']
            exclusive = button_config['exclusive']
            button = create_icon_button(self.Iconwid,icon_path, object_name,icon_text,exclusive)
            self.buttons[object_name]= button
            self.verticalLayout_2.addWidget(button)
       
        
        #Spacer
        self.verticalLayout_3.addLayout(self.verticalLayout_2)
        self.verticalSpacer_3 = QSpacerItem(20, 347, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.verticalLayout_3.addItem(self.verticalSpacer_3)
        
        #File Only Mode Button
        self.fileButton_1 = create_icon_button(self.Iconwid,icon_path="./icons/file-icon.png", object_name=u"fileButton_1",icon_text = "",exclusive=False)
        self.verticalLayout_3.addWidget(self.fileButton_1)
        
        self.gridLayout.addWidget(self.Iconwid, 0, 0, 1, 1)
        
        self.Iconwid2 = QWidget(self.centralwidget)
        self.Iconwid2.setObjectName(u"Iconwid2")
        self.Iconwid2.setStyleSheet(u"QWidget{\n"
                                    "	background-color: rgb(58, 58, 58);\n"
                                    "}\n"
                                    "\n"
                                    "QPushButton{\n"
                                    "	color:white;\n"
                                    "	text-align:left;\n"
                                    "	height:30;\n"
                                    "	border:none;\n"
                                    "	padding-left:10;\n"
                                    "}")
        self.Iconwid2.setHidden(True)
        self.verticalLayout_4 = QVBoxLayout(self.Iconwid2)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(10, 10, 10, 10)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(20)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(-1, -1, 10, 20)
        
        
        
        for button_config in button_configurations_2:    
            icon_path = button_config['path']
            object_name = button_config['name']
            exclusive = button_config['exclusive']
            icon_text = button_config['text']
            button = create_icon_button(self.Iconwid2,icon_path, object_name,icon_text,exclusive)
            self.buttons[object_name]= button
            self.verticalLayout.addWidget(button)


        self.verticalLayout_4.addLayout(self.verticalLayout)
        self.verticalSpacer_2 = QSpacerItem(20, 347, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.verticalLayout_4.addItem(self.verticalSpacer_2)
        
        self.fileButton_2 = create_icon_button(self.Iconwid2,icon_path="./icons/file-icon.png", object_name=u"fileButton_2",icon_text = "File Mode",exclusive=False)
        self.verticalLayout_4.addWidget(self.fileButton_2)


        self.gridLayout.addWidget(self.Iconwid2, 0, 1, 1, 1)
        
        
        
        
        #Open Widget
        self.MainWindow_2 = QWidget(self.centralwidget)
        self.MainWindow_2.setObjectName(u"MainWindow_2")
        self.MainWindow_2.setStyleSheet(u"QWidget{\n"
                                        "	background-color:rgb(169, 186, 157);\n"
                                        "}\n"
                                        "QPushButton{\n"
                                        "	background-color: rgb(58, 58, 58);\n"
                                        "	color:white;\n"
                                        "	height:30;\n"
                                        "	padding-left:10;\n"
                                        "}\n"
                                        "")
        self.gridLayout_6 = QGridLayout(self.MainWindow_2)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.stackedWidget = QStackedWidget(self.MainWindow_2)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.stackedWidget.setStyleSheet(u"QWidget{\n"
                                         "	background-color:rgb(169, 186, 157);\n"
                                         "}\n"
                                         "QSpinBox{\n"
                                         "	background-color: white;\n"
                                         "  font:bold 15px ""Times New Roman"";\n"
                                         "	height:25;\n"
                                         "}\n"
                                         "QDoubleSpinBox{\n"
                                         "	background-color: white;\n"
                                         "  font:bold 15px ""Times New Roman"";\n"
                                         "	height:25;\n"
                                         "}\n"
                                         "QComboBox{\n"
                                         "	background-color: white;\n"
                                         "  font:bold 15px ""Times New Roman"";\n"
                                         "	height:25;\n"
                                         "}\n"
                                         "QLabel{\n"
                                         "  font:bold 15px ""Times New Roman"";\n"
                                         "	height:25;\n"
                                         "}\n"
                                         "QCheckBox{\n"
                                         "  font:bold 15px ""Times New Roman"";\n"
                                         "	height:25;\n"
                                         "}\n"
                                         
                                         "QSpinBox::disabled{\n"
                                         "	background-color: silver;\n"
                                         "}\n"
                                         "QDoubleSpinBox::disabled{\n"
                                         "	background-color: silver;\n"
                                         "}\n"
                                         "")
        
        
        #Audio Setting Page
        self.AudioSettingPage = QWidget()
        self.AudioSettingPage.setObjectName(u"AudioSettingPage")
        self.AudioSettingPage.setEnabled(True)
        self.gridLayout_2 = QGridLayout(self.AudioSettingPage)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setVerticalSpacing(0)
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        
        self.audio_overlap = create_widget("QSpinBox",
                                           self.AudioSettingPage,
                                           "audio_overlap",
                                           self.gridLayout_2,
                                           3,3,1,1,
                                           enabled = True,
                                           wrapping = True,
                                           minimum = 1,
                                           maximum = 5,
                                           single_step = 1,
                                           value = 3)
                                           

        self.sample_rate = create_widget("QSpinBox",
                                        self.AudioSettingPage,
                                        "sample_rate",
                                        self.gridLayout_2,
                                        0, 1, 1, 1,
                                        wrapping=True,
                                        minimum=1000,
                                        maximum=100000,
                                        single_step=1000,
                                        value=16000)


        self.device_input = create_widget("QComboBox",
                                          self.AudioSettingPage,
                                          "device_input",
                                          self.gridLayout_2,
                                          1, 1, 1, 1,
                                          editable=False,
                                          items=input_devices)


        self.sample_duration = create_widget("QSpinBox",
                                             self.AudioSettingPage,
                                             "sample_duration",
                                             self.gridLayout_2,
                                             0, 3, 1, 1,
                                             wrapping=True,
                                             minimum=3,
                                             maximum=10,
                                             single_step=1,
                                             value=5)
        

        self.device_output = create_widget("QComboBox",
                                           self.AudioSettingPage,
                                           "device_output",
                                           self.gridLayout_2,
                                           1, 3, 1, 1,
                                           editable=False,
                                           items=output_devices)


        self.circular_audio = create_widget("QCheckBox",
                                            self.AudioSettingPage,
                                            "circular_audio",
                                            self.gridLayout_2,
                                            3, 1, 1, 1,
                                            enabled=True,
                                            exclusive=False,
                                            text="Circular Audio")

        
        
        
        
        self.gridLayout_2.addWidget(self.circular_audio, 3, 1, 1, 1, Qt.AlignCenter)

        self.stackedWidget.addWidget(self.AudioSettingPage)
        self.PromptSettingPage = QWidget()
        self.PromptSettingPage.setObjectName(u"PromptSettingPage")
        self.gridLayout_3 = QGridLayout(self.PromptSettingPage)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setHorizontalSpacing(10)
        self.gridLayout_3.setVerticalSpacing(50)
        self.gridLayout_3.setContentsMargins(20, 0, 0, 0)
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_3.addItem(self.horizontalSpacer_3, 1, 5, 1, 1)

        

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_3.addItem(self.horizontalSpacer_4, 0, 7, 1, 1)
        
        
        self.add_prompt_threshold = create_widget("QDoubleSpinBox",
                                                  self.PromptSettingPage,
                                                  "add_prompt_threshold",
                                                  self.gridLayout_3,
                                                  1, 3, 1, 2,
                                                  minimum=-2.000,
                                                  maximum=0.000,
                                                  single_step=0.100,
                                                  value=-0.500)

        self.prompt_reset_on_temperature = create_widget("QCheckBox",
                                                         self.PromptSettingPage,
                                                         "prompt_reset_on_temperature",
                                                         self.gridLayout_3,
                                                         1, 6, 1, 1,
                                                         enabled=True,
                                                         exclusive=False,
                                                         text="Prompt Reset on Temperature")


        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_3.addItem(self.horizontalSpacer_5, 0, 4, 1, 1)

        self.special_words = QPlainTextEdit(self.PromptSettingPage)
        self.special_words.setObjectName(u"special_words")
        self.special_words.setPlaceholderText("Please type here if there are any specific prompts or special words you would like to add to vocabulary of the program.")
        
        self.gridLayout_3.addWidget(self.special_words, 2, 4, 1, 4)
        
        self.filtered_words = QPlainTextEdit(self.PromptSettingPage)
        self.filtered_words.setObjectName(u"filtered_words")
        self.filtered_words.setPlaceholderText("Please type here for any filtered words. Each filtered word is split by comma.")
        
        self.gridLayout_3.addWidget(self.filtered_words, 3, 4, 1, 4)        

        self.stackedWidget.addWidget(self.PromptSettingPage)
        self.ModelSettingPage = QWidget()
        self.ModelSettingPage.setObjectName(u"ModelSettingPage")
        self.gridLayout_4 = QGridLayout(self.ModelSettingPage)
        self.gridLayout_4.setSpacing(0)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setContentsMargins(0, 0, 0, 0)
        
        self.task = create_widget("QComboBox",
                                  self.ModelSettingPage,
                                  "task",
                                  self.gridLayout_4,
                                  0, 4, 1, 2,
                                  editable=False,
                                  items=task_options)

        self.word_timestamps = create_widget("QCheckBox",
                                             self.ModelSettingPage,
                                             "word_timestamps",
                                             self.gridLayout_4,
                                             4, 0, 1, 1,
                                             enabled=True,
                                             exclusive=False,
                                             text="Word Timestamps")
        

        self.vad_threshold = create_widget("QDoubleSpinBox",
                                            self.ModelSettingPage,
                                            "vad_threshold",
                                            self.gridLayout_4,
                                            5, 1, 1, 1,
                                            minimum=0.000,
                                            maximum=1.000,
                                            single_step=0.100,
                                            value=0.600)

        self.log_prob_threshold = create_widget("QDoubleSpinBox",
                                                self.ModelSettingPage,
                                                "log_prob_threshold",
                                                self.gridLayout_4,
                                                3, 1, 1, 1,
                                                minimum=-2.000,
                                                maximum=0.000,
                                                single_step=0.010,
                                                value=-0.990)

        self.model = create_widget("QComboBox",
                                    self.ModelSettingPage,
                                    "model",
                                    self.gridLayout_4,
                                    0, 1, 1, 1,
                                    editable=False,
                                    items=model_options,
                                    current_index = 2)


        self.repetition_penalty = create_widget("QDoubleSpinBox",
                                                self.ModelSettingPage,
                                                "repetition_penalty",
                                                self.gridLayout_4,
                                                2, 4, 1, 2,
                                                minimum=1.000,
                                                maximum=5.000,
                                                single_step=0.050,
                                                value=1.050)

        self.no_speech_threshold = create_widget("QDoubleSpinBox",
                                                  self.ModelSettingPage,
                                                  "no_speech_threshold",
                                                  self.gridLayout_4,
                                                  3, 4, 1, 2,
                                                  minimum=-2.000,
                                                  maximum=0.000,
                                                  single_step=0.100,
                                                  value=-0.500)

        self.condition_on_previous_text = create_widget("QCheckBox",
                                                        self.ModelSettingPage,
                                                        "condition_on_previous_text",
                                                        self.gridLayout_4,
                                                        4, 3, 1, 1,
                                                        enabled=True,
                                                        exclusive=False,
                                                        text="Condition on Previous Text",
                                                        alignment = None)

        self.best_of = create_widget("QSpinBox",
                                     self.ModelSettingPage,
                                     "best_of",
                                     self.gridLayout_4,
                                     1, 4, 1, 2,
                                     wrapping=True,
                                     minimum=1,
                                     maximum=5,
                                     value=3)

        self.patience = create_widget("QDoubleSpinBox",
                                      self.ModelSettingPage,
                                      "patience",
                                      self.gridLayout_4,
                                      2, 1, 1, 1,
                                      alignment=Qt.AlignCenter,
                                      minimum=1.000,
                                      maximum=10.000,
                                      single_step=0.100,
                                      value=1.500)

        self.beam_size = create_widget("QSpinBox",
                                        self.ModelSettingPage,
                                        "beam_size",
                                        self.gridLayout_4,
                                        1, 1, 1, 1,
                                        wrapping=True,
                                        alignment=Qt.AlignCenter,
                                        minimum=1,
                                        maximum=10,
                                        value=5)

        self.min_silence_duration_ms = create_widget("QSpinBox",
                                                     self.ModelSettingPage,
                                                     "min_silence_duration_ms",
                                                     self.gridLayout_4,
                                                     5, 4, 1, 2,
                                                     enabled=True,
                                                     wrapping=True,
                                                     minimum=100,
                                                     maximum=2000,
                                                     single_step=100,
                                                     value=500)

        self.vad_filter = create_widget("QCheckBox",
                                        self.ModelSettingPage,
                                        "vad_filter",
                                        self.gridLayout_4,
                                        4, 4, 1, 2,
                                        enabled=True,
                                        exclusive=True,
                                        text="VAD Filter")



        self.stackedWidget.addWidget(self.ModelSettingPage)
        self.OtherSettingPage = QWidget()
        self.OtherSettingPage.setObjectName(u"OtherSettingPage")
        self.gridLayout_7 = QGridLayout(self.OtherSettingPage)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.gridLayout_7.setHorizontalSpacing(0)
        self.gridLayout_7.setVerticalSpacing(20)
        self.gridLayout_7.setContentsMargins(0, 0, 0, 0)


        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_7.addItem(self.verticalSpacer_4, 5, 0, 1, 1)

        self.debug_mode = create_widget("QCheckBox",
                                        self.OtherSettingPage,
                                        "debug_mode",
                                        self.gridLayout_7,
                                        2, 0, 1, 1,
                                        checked = False,
                                        exclusive = False,
                                        text = "Debug Mode:")
                                           



        self.gridLayout_7.addWidget(self.debug_mode, 2, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_7.addItem(self.verticalSpacer, 0, 0, 1, 1)

        self.horizontalSpacer = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_7.addItem(self.horizontalSpacer, 6, 1, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_7.addItem(self.horizontalSpacer_2, 4, 0, 1, 1)

        self.stackedWidget.addWidget(self.OtherSettingPage)

        self.gridLayout_6.addWidget(self.stackedWidget, 0, 0, 1, 1)

        self.proceed_button = QPushButton(self.MainWindow_2)
        self.proceed_button.setObjectName(u"proceed_button")
        self.proceed_button.setText("Proceed with last saved Configurations")

        self.gridLayout_6.addWidget(self.proceed_button, 3, 0, 1, 1)

        self.save_button = QPushButton(self.MainWindow_2)
        self.save_button.setObjectName(u"save_button")
        self.save_button.setText("Replace and Save Configurations")


        self.gridLayout_6.addWidget(self.save_button, 2, 0, 1, 1)


        self.gridLayout.addWidget(self.MainWindow_2, 0, 2, 1, 1)

        #Labels
        label_configurations = [
            { "name": "label", "text":"Sample rate:","page":"audio"},
            { "name": "label_2", "text":"Sample duration:","page":"audio"},
            { "name": "label_3", "text":"Device input:","page":"audio"},
            { "name": "label_4", "text":"Device output:","page":"audio"},
            { "name": "label_5", "text":"Audio Overlap:","page":"audio"},
            { "name": "label_6", "text":"Prompt Threshold:","page":"prompt"},
            { "name": "label_7", "text":"Special Words:","page":"prompt"},
            { "name": "label_8", "text":"Filtered Words:","page":"prompt"},
            { "name": "label_9", "text":"Model:","page":"model"},
            { "name": "label_10", "text":"Task:","page":"model"},
            { "name": "label_11", "text":"Beam Size:","page":"model"},
            { "name": "label_12", "text":"Best of:","page":"model"},
            { "name": "label_13", "text":"Patience:","page":"model"},
            { "name": "label_14", "text":"Repetition Penalty:","page":"model"},
            { "name": "label_15", "text":"Log Prob Threshold:","page":"model"},
            { "name": "label_16", "text":"No Speech Threshold:","page":"model"},
            { "name": "label_17", "text":"VAD Threshold:","page":"model"},
            { "name": "label_18", "text":"Min Silence Duration (ms):","page":"model"},
            { "name": "label_19", "text":"Please ignore this page as it is only used for testing purposes. New experimental features will be added in this section.","page":"others"},
            ]
        
        # create_label(parent,object_name,text)
        self.labels = {}
        for label_config in label_configurations:    
            object_name = label_config['name']
            text = label_config['text']
            page = label_config['page']
            if page == "audio":
                parent = self.AudioSettingPage
            elif page == "prompt":
                parent = self.PromptSettingPage
            elif page == "model":
                parent = self.ModelSettingPage
            else:
                parent = self.OtherSettingPage
            label = create_label(parent, object_name,text)
            self.labels[object_name]= label 
        
        
        
        
        
        
        
        #Others
        self.gridLayout_7.addWidget(self.labels["label_19"], 1, 0, 1, 2)
        
        #AUDIO
        self.gridLayout_2.addWidget(self.labels["label"], 0, 0, 1, 1)
        self.gridLayout_2.addWidget(self.labels["label_2"], 0, 2, 1, 1)
        self.gridLayout_2.addWidget(self.labels["label_3"], 1, 0, 1, 1)
        self.gridLayout_2.addWidget(self.labels["label_4"], 1, 2, 1, 1)
        self.gridLayout_2.addWidget(self.labels["label_5"], 3, 2, 1, 1)
        
        #Prompt
        self.gridLayout_3.addWidget(self.labels["label_6"], 1, 1, 1, 1)
        self.gridLayout_3.addWidget(self.labels["label_7"], 2, 1, 1, 1)
        self.gridLayout_3.addWidget(self.labels["label_8"], 3, 1, 1, 1)
        

        #Model
        self.gridLayout_4.addWidget(self.labels["label_9"], 0, 0, 1, 1)
        self.gridLayout_4.addWidget(self.labels["label_10"], 0, 3, 1, 1)
        self.gridLayout_4.addWidget(self.labels["label_11"], 1, 0, 1, 1)
        self.gridLayout_4.addWidget(self.labels["label_12"], 1, 3, 1, 1)
        self.gridLayout_4.addWidget(self.labels["label_13"], 2, 0, 1, 1)
        self.gridLayout_4.addWidget(self.labels["label_14"], 2, 3, 1, 1)        
        self.gridLayout_4.addWidget(self.labels["label_15"], 3, 0, 1, 1)
        self.gridLayout_4.addWidget(self.labels["label_16"], 3, 3, 1, 1)
        self.gridLayout_4.addWidget(self.labels["label_17"], 5, 0, 1, 1)
        self.gridLayout_4.addWidget(self.labels["label_18"], 5, 3, 1, 1)
        

        
        
        
        
        
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

       
        
        
        
        
        self.buttons['menuButton_1'].clicked.connect(self.Iconwid.hide)
        self.buttons['menuButton_1'].clicked.connect(self.Iconwid2.show)
        self.buttons['menuButton_2'].clicked.connect(self.Iconwid.show)
        self.buttons['menuButton_2'].clicked.connect(self.Iconwid2.hide)
        
        self.buttons['audioButton_1'].toggled.connect(self.buttons['audioButton_2'].setChecked)
        self.buttons['audioButton_1'].clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.buttons['audioButton_2'].clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        
        self.buttons['promptButton_1'].toggled.connect(self.buttons['promptButton_2'].setChecked)
        self.buttons['promptButton_1'].clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.buttons['promptButton_2'].clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        
        self.buttons['modelButton_1'].toggled.connect(self.buttons['modelButton_2'].setChecked)
        self.buttons['modelButton_1'].clicked.connect(lambda: self.stackedWidget.setCurrentIndex(2))
        self.buttons['modelButton_2'].clicked.connect(lambda: self.stackedWidget.setCurrentIndex(2))
        
        self.buttons['settingButton_1'].toggled.connect(self.buttons['settingButton_2'].setChecked)
        self.buttons['settingButton_1'].clicked.connect(lambda: self.stackedWidget.setCurrentIndex(3))
        self.buttons['settingButton_2'].clicked.connect(lambda: self.stackedWidget.setCurrentIndex(3))
        
        self.buttons['audioButton_1'].clicked.connect(self.Iconwid.hide)
        self.buttons['audioButton_1'].clicked.connect(self.Iconwid2.show)
        self.buttons['promptButton_1'].clicked.connect(self.Iconwid.hide)
        self.buttons['promptButton_1'].clicked.connect(self.Iconwid2.show)
        self.buttons['modelButton_1'].clicked.connect(self.Iconwid.hide)
        self.buttons['modelButton_1'].clicked.connect(self.Iconwid2.show)
        self.buttons['settingButton_1'].clicked.connect(self.Iconwid.hide)
        self.buttons['settingButton_1'].clicked.connect(self.Iconwid2.show)
        
        
       
        self.file_only_mode = None
        self.audio_file = None
       
        
        self.circular_audio.toggled.connect(self.audio_overlap.setEnabled)
        self.vad_filter.toggled.connect(self.vad_threshold.setEnabled)
        self.vad_filter.toggled.connect(self.min_silence_duration_ms.setEnabled)
        self.proceed_button.clicked.connect(self.proceed_configuration)
        self.save_button.clicked.connect(self.save_configuration)
        self.fileButton_1.clicked.connect(self.showFileDialog)
        self.fileButton_2.clicked.connect(self.showFileDialog)
        
        self.stackedWidget.setCurrentIndex(0)
  
        
        QMetaObject.connectSlotsByName(MainWindow)
        

    def showFileDialog(self):
        
        file_name  = QFileDialog.getOpenFileName(#parent = self, 
                                                caption = "QFileDialog.getOpenFileName()",
                                                dir = os.getcwd(),
                                                filter= "All Files (*);; Audio Files (*.mp3)")
                                                # initialFilter="Audio Files (*.mp3)")
        if file_name:
            self.file_only_mode = True
            self.audio_file = file_name[0]
        
    def post_calculation(self):
        self.parameters = {
            "add_prompt_threshold": self.add_prompt_threshold.value(),
            "prompt_reset_on_temperature": self.prompt_reset_on_temperature.isChecked(),
            "special_words": self.special_words.toPlainText(),
            "filtered_words": self.filtered_words.toPlainText(),
            "sample_rate": self.sample_rate.value(),
            "sample_duration":self.sample_duration.value(),
            "device_input":self.device_input.currentText(),
            "device_input_name":None,
            "device_output":self.device_output.currentText(),
            "device_output_name":None,
            "circular_audio": self.circular_audio.isChecked(),
            "audio_overlap":self.audio_overlap.value(),
            "model":self.model.currentText(),
            "task":self.task.currentText(),
            "beam_size":self.beam_size.value(),
            "best_of":self.best_of.value(),
            "patience":self.patience.value(),
            "repetition_penalty":self.repetition_penalty.value(),
            "log_prob_threshold":self.log_prob_threshold.value(),
            "no_speech_threshold":self.no_speech_threshold.value(),
            "condition_on_previous_text":self.condition_on_previous_text.isChecked(),
            "word_timestamps":self.word_timestamps.isChecked(),
            "vad_filter": self.vad_filter.isChecked(),
            "vad_threshold": self.vad_threshold.value(),
            "min_silence_duration_ms":self.min_silence_duration_ms.value(),
            "block_size":None,
            "file_only_mode":self.file_only_mode,
            "audio_file":self.audio_file,
            "starting_words":"vtuber,hololive,japanese and english,"
            }

        
        if self.parameters['filtered_words'] != '':
            self.parameters['filtered_words'] = {word.lower().strip() for word in self.parameters['filtered_words'].split(',')}
            self.parameters['filtered_words'] = list(self.parameters['filtered_words'])
        else:
            self.parameters['filtered_words'] = None
        
        
        if isinstance(self.parameters['device_input'],str) and len(self.parameters['device_input'])>0:
            self.parameters['device_input_name'] = self.parameters['device_input'][2:] 
            self.parameters['device_input'] = int(self.parameters['device_input'][:2]) 
            
        if isinstance(self.parameters['device_output'],str) and len(self.parameters['device_output'])>0:
            self.parameters['device_output_name'] = self.parameters['device_output'][2:]
            self.parameters['device_output'] = int(self.parameters['device_output'][:2])
        
        self.parameters['block_size']= int(self.parameters['sample_rate'] * self.parameters['sample_duration'])
        
        if self.parameters['audio_overlap'] > self.parameters['sample_duration']:
            print("USER MISUSE, setting audio_overlap to max of sample_duration")
            self.parameters['audio_overlap'] = self.parameters['sample_duration']
        
        
    def save_configuration(self):
        self.post_calculation()
        # Save both regular and fixed parameters to a file
        configuration = self.parameters
        
        with open("config_live_transcript.json", "w") as config_file:
            json.dump(configuration, config_file, indent=4)

        print("Configuration saved to 'config_live_transcript.json'.")
        QApplication.quit()

    def proceed_configuration(self):
        print("Pre-saved Configuration being used")
        QApplication.quit()
        
        
        
def main():
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
            
    window = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(window)
    window.show()
    app.exec()


if __name__ == '__main__':
    main()
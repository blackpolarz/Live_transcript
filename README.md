# Live_transcript
A simplified application of ASR models for transcribing real time streams.\
Current version: 1.7 \
OS: Windows \
Currently supported models:Faster-Whisper large-v2, Faster-Whisper large-v3

**DISCLAIMER: This is a simple application of zero-shot ASR models and its translation should not be trusted completely due to the inaccuracies of ASR.
Please take all translations with a grain of salt and it should only serve as an secondary aid to help understand the context of streams, videos or anime.
Please avoid using the translations as evidence that can potentially harm any streamers or content creators as the model tends to hallucinate and can provide
misinformation.**


## Requirements: 
1) Python 3.11
2) numpy
3) pytorch with cuda 11.8 @ https://pytorch.org/get-started/locally/
4) virtual audio cable @ https://vb-audio.com/Cable/

## Installation Guide:
1) Download the repository in zip, unzip it.

2) Pip install the requirements.txt (Might take some time due to dependancies)
```
   pip install -r requirements.txt
```
## How to run the code:
1) Go to anaconda prompt/cmd and type
```
   python Live_Transcript.py
```
2) Alternatively, create the bat file as follow: (Remember to replace DIR_ANACONDA with your activate.bat directory,
   ENV_NAME with your virtual environment and DIR_CODE with the directory of your code)
```   
  @echo off
  title LiveTranscript by blackpolar
  call DIR_ANACONDA 
  call activate ENV_NAME
  python DIR_CODE
  call conda deactivate
```
## FAQ:
1) Question: There is no transcription showing up.\
Answer: Kindly set your audio devices on windows to CABLE INPUT and CABLE OUTPUT. 
<img src="https://github.com/blackpolarz/Live_transcript/assets/126226575/9d5ffcb7-32f1-48c3-82da-14ba0dc7bdec" width=40% height=40%>

2) Question: There is no audio.\
Please go to more sound setting in the sound setting.
<img src="https://github.com/blackpolarz/Live_transcript/assets/126226575/bf7809f1-de6d-4ace-9c8a-d203d3a43386" width=40% height=40%>

Select the Recording tab,CABLE OUTPUT properties.Select the Listen tab and check the Listen to this device. \
Please change the playback through this device to your headphone or speaker. \
<img src="https://github.com/blackpolarz/Live_transcript/assets/126226575/e7f438da-23d6-4e4b-94c0-8db8d5e1491c" width=30% height=30%>  <img src="https://github.com/blackpolarz/Live_transcript/assets/126226575/972bee94-41ce-4389-b181-dfce9121427f" width=30% height=30%>

## Acknowledgement:
All copyrights belong to original authors of faster-whisper, whisper, sound-device and pytorch.








# Live_transcript
A simplified application of ASR models for transcribing real time streams.\
Current version: 1.8 \
OS: Windows \
Currently supported models:Faster-Whisper large-v2, Faster-Whisper large-v3

**DISCLAIMER: This is a simple application of zero-shot ASR models and its translation should not be trusted completely due to the inaccuracies of ASR.
Please take all translations with a grain of salt and it should only serve as an secondary aid to help understand the context of streams, videos or anime.
Please avoid using the translations as evidence that can potentially harm any streamers or content creators as the model tends to hallucinate and can provide
misinformation.**


## Requirements: 
1) Python 3.12
2) numpy
3) pytorch with cuda 12 @ https://pytorch.org/get-started/locally/
   (Note: Currently, torchaudio <= 2.3.1 as ctranslate2 does not support cudnn9) 
5) virtual audio cable @ https://vb-audio.com/Cable/

## Installation Guide:
1) Download the repository in zip, unzip it.

2) Pip install the requirements.txt (Might take some time due to dependancies)
```
   pip install -r requirements.txt
```
## How to run the code:
1) Go to anaconda prompt/cmd and type
```
   python Live_Transcript_v1.8.py
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

## CLI support:
For users who prefer Command Line Interface instead of GUI,
users can simply type:
python Live_Transcript_v1.8.py --no_gui

Users can also change the options in the parameters by typing -o, --config_file , --input_file, --output_file. 

## FAQ:
1) Question: There is no transcription showing up.\
Answer: Kindly set your audio devices on windows to CABLE INPUT and CABLE OUTPUT. 
<img src="https://github.com/blackpolarz/Live_transcript/assets/126226575/9d5ffcb7-32f1-48c3-82da-14ba0dc7bdec" width=40% height=40%>


## Acknowledgement:
All copyrights belong to original authors of faster-whisper, whisper, sound-device and pytorch.








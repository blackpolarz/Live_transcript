# -*- coding: utf-8 -*-
"""
A simplified program to transcribe live streams using Whisper AI's model.

To use, you can simply open terminal and type python Live_Transcript_v[version number] 

@author: BlackPolar
"""
import time as t
import logging
import torch
import sounddevice as sd
import sys
import queue
import numpy as np
from threading import Event
from transformers import logging as logger
logger.set_verbosity_error()

from transformers import pipeline

logging.getLogger().setLevel(logging.ERROR)


# Create a callback function to handle audio input
def audio_callback(indata, frames,time, status):
    
    if status:
        print(status, file=sys.stderr)
    
    #Audio is dual channel, hence there is a need to combine them.
    audio = np.concatenate([indata[:, 0], indata[:, 1]])
    
    if (quiet_detection(audio)): #Simple way to detect if its noisy/quiet
        try:
            q_list.put(audio[:]) 
        except queue.Full: #This condition will never happen as there is no limit. 
            pass


def RMS(audio):
    return np.sqrt(np.mean(audio**2))

def quiet_detection(audio):
    global loudness_threshold
    SMOOTHING_FACTOR = 0.25
    #Setting hard limits and dynamic thresholding
    loudness = RMS(audio)
    loudness_threshold = (1 - SMOOTHING_FACTOR) * loudness_threshold + SMOOTHING_FACTOR * loudness
    loudness_threshold = loudness_threshold * (loudness_threshold>0.0025)* (loudness_threshold<=0.01) \
                            + 0.001 *(loudness_threshold<=0.0025) + 0.01 * (loudness_threshold> 0.01)
    return (loudness > loudness_threshold)


def transcribe_translate(from_code="ja",to_code="en",debug=False):
    try:
        audio = q_list.get_nowait() 
        text = transcriber(audio)
        if (debug):
            print(f"Remaining {q_list.qsize()}: {text['text']}" )
        else:
            timestamp = t.strftime("%H:%M:%S ")
            # timestamp = datetime.now().time()
            print(f"{timestamp}: {text['text']}")
    except queue.Empty:
        Event().wait(0.1)
        pass

def setup_transcriber(model = "openai/whisper-large-v2",huggingface_accelerate_install_flag = True):
    '''
    Setup pipeline for ASR model. If huggingface accelerate is installed, you can use device_map to automatically
    adjust load on the system. It should speed up the transcription. 
    
    Set huggingface_accelerate_install_flag to False if huggingface accelerate is not installed.
    
    If transcription is taking a long time,you might want to use a smaller model. 
    
    Available models:
    openai/whisper-large-v2 (default)
    openai/whisper-medium
    openai/whisper-small
    openai/whisper-tiny
    
    '''
    
    if (huggingface_accelerate_install_flag):
        # Whisper ASR (Zero Shot)
        transcriber = pipeline(task = "automatic-speech-recognition", 
                                model= model,
                                device_map="auto")
    else:
        # Whisper ASR (Zero Shot)
        transcriber = pipeline(task = "automatic-speech-recognition", 
                                model= model)
    
    return transcriber
        
if __name__ == "__main__":
    # Define the audio capture parameters
    sample_rate = 16000
    block_size = 16000 * 3 # Capture for 5 seconds

    loudness_threshold = 0.003
    
    transcriber = setup_transcriber(model = "./models--openai--whisper-large-v2/snapshots/1f66457e6e36eeb6d89078882a39003e55c330b8",
                                    huggingface_accelerate_install_flag = True)
    
    q_list = queue.Queue()
    device_output ="CABLE Output (VB-Audio Virtual , MME"
    device_input = "CABLE Input (VB-Audio Virtual , MME"

    sd.default.device = [device_output,device_input]
    audiostream = sd.InputStream(channels=2, blocksize=block_size, samplerate=sample_rate,
                        callback=audio_callback)
    print("Program Started")
    with audiostream:
        try:
            while True:
                if (q_list.qsize()>10):
                    print("Overloaded, Sounddevice temporary put on hold")
                    sd.sleep(10) 
                transcribe_translate(from_code="ja",to_code="en")
        except KeyboardInterrupt:
            sd.stop()
            print("terminated")
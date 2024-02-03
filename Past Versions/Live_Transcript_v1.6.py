# -*- coding: utf-8 -*-
"""
A simplified program to transcribe live streams using Whisper AI's model.

To use, you can simply open terminal and type python Live_Transcript_v[version number] 

@author: BlackPolar
"""
import logging
import torch
import sounddevice as sd
import sys
import queue
import numpy as np
from threading import Event
from transformers import logging as logger
from faster_whisper import WhisperModel
logger.set_verbosity_error()


logging.getLogger().setLevel(logging.ERROR)

import json
    
from dataclasses import dataclass,field,asdict

import os

@dataclass()
class LiveTranscriptConfig:
    sample_rate: int = 16000
    sample_duration:int = 5
    block_size:int = field(init=False)
    device_input:str = "CABLE Output (VB-Audio Virtual , MME"
    device_output:str = "CABLE Input (VB-Audio Virtual , MME"
    circular_audio:bool = True
    audio_overlap:int = 2
    starting_words:str = "vtuber,hololive,japanese and english,"
    add_prompt_threshold:float = -0.7
    task:str = "translate"
    beam_size:int = 5
    best_of:int = 3
    patience:float = 1.5
    repetition_penalty:float = 1.05
    log_prob_threshold:float = -0.99
    no_speech_threshold:float = 0.8
    condition_on_previous_text:bool = True
    prompt_reset_on_temperature:float =0.4
    vad_filter:bool = True
    vad_threshold: float = 0.6
    min_silence_duration_ms: int = 1000
    debug_mode:bool = False
    
    def __post_init__(self):
        self.block_size = self.sample_rate * self.sample_duration
    
    def loadConfig(self,config_file_name):    
        with open(config_file_name, 'r') as f:
            lt_config = json.load(f)
        self.sample_rate = lt_config["sample_rate"]
        self.sample_duration = lt_config["sample_duration"]
        self.block_size = lt_config["block_size"]
        self.device_input = lt_config["device_input"]
        
        self.device_output = lt_config["device_output"]
        self.circular_audio = lt_config["circular_audio"]
        self.audio_overlap = lt_config["audio_overlap"]
        self.starting_words = lt_config["starting_words"]
        self.add_prompt_threshold = lt_config["add_prompt_threshold"]
        self.task = lt_config["task"]
        
        self.beam_size = lt_config["beam_size"]
        self.best_of = lt_config["best_of"]
        self.patience = lt_config["patience"]
        self.repetition_penalty = lt_config["repetition_penalty"]
        
        self.log_prob_threshold = lt_config["log_prob_threshold"]
        self.no_speech_threshold = lt_config["no_speech_threshold"]
        self.condition_on_previous_text = lt_config["condition_on_previous_text"]
        self.prompt_reset_on_temperature = lt_config["prompt_reset_on_temperature"]
       
        self.vad_filter = lt_config["vad_filter"]
        self.vad_threshold = lt_config["vad_threshold"]
        self.min_silence_duration_ms = lt_config["min_silence_duration_ms"]
        self.debug_mode = lt_config["debug_mode"]
        
        
        
    def writeConfig(self,config_file_name):
        with open(config_file_name, 'w') as f:
            json.dump(asdict(self), f,indent= 4)


@dataclass
class WhisperOutput:
    output_id: int
    seek: int
    start: float
    end: float
    text: str
    tokens: [int]
    temperature: float
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float
    
    def __init__(self, data:list):
        self.output_id = data[0]
        self.seek = data[1]
        self.start = data[2]
        self.end = data[3]
        self.text = data[4]
        self.tokens = data[5]
        self.temperature = data[6]
        self.avg_logprob = data[7]
        self.compression_ratio = data[8]
        self.no_speech_prob = data[9]
        if len(data)>10:
            self.optionalWord = data[10:]

# Create a callback function to handle audio input
def audio_callback(indata,frames,time, status):
    
    if status:
        print(status, file=sys.stderr)
    
    #Audio is dual channel, hence there is a need to combine them.
    audio = np.concatenate([indata[:, 0], indata[:, 1]])
    
    try:
        q_list.put(audio[:]) 
    except queue.Full: #This condition will never happen as there is no limit. 
        pass    


def transcribe_translate(transcriber,init_prompt_length,prompt='vtuber,japanese and english,hololive',debug_mode=False):
    '''
    debug_mode only used to check on prompts,avg_logprob,compression ratio and temperature of each translation
    
    
    
    
    '''
    global previous_audio_buffer
    
    
    try:
        audio = q_list.get_nowait()
        
    except queue.Empty:
        Event().wait(0.1)
        return prompt
    if (lt_options.circular_audio):
        if previous_audio_buffer is not None:
            audio = np.concatenate((previous_audio_buffer,audio))
    
        previous_audio_buffer = audio[-16000 * lt_options.audio_overlap:]
    
    if (debug_mode):
        print(f"Prompt:{prompt}",file=log_file)
    segment,info = transcriber.transcribe(audio,
                                          task = lt_options.task,
                                          beam_size= lt_options.beam_size,
                                          best_of= lt_options.best_of,
                                          patience=lt_options.patience,
                                          repetition_penalty=lt_options.repetition_penalty,
                                          log_prob_threshold = lt_options.log_prob_threshold,
                                          no_speech_threshold = lt_options.no_speech_threshold,
                                          condition_on_previous_text= lt_options.condition_on_previous_text,
                                          prompt_reset_on_temperature=lt_options.prompt_reset_on_temperature,
                                          vad_filter = lt_options.vad_filter,
                                          vad_parameters=dict(threshold=lt_options.vad_threshold,
                                                              min_silence_duration_ms=lt_options.min_silence_duration_ms),
                                          initial_prompt=prompt
                                          )
        
    segment_list = list(segment)
    if not segment_list: 
        return prompt[:init_prompt_length]
    output = WhisperOutput(segment_list[0])
    
    print(f"Remaining {q_list.qsize()}|Score {output.avg_logprob:.3f}: {output.text}")
    if (debug_mode):
        print(f"Remaining {q_list.qsize()}|Score {output.avg_logprob:.3f}: {output.text}",file=log_file) #DEBUG ONLY
    # print(isinstance(prompt,str))
    if ((output.avg_logprob > lt_options.add_prompt_threshold) & isinstance(prompt,str)):
        prompt = prompt[:init_prompt_length] + output.text
        return prompt
        # print(f"Prompt:{prompt}")        
    if((output.avg_logprob <lt_options.log_prob_threshold) & debug_mode):
        print(f"Avg_logprob: {output.avg_logprob:.5f}, Compression Ratio: {output.compression_ratio:.5f}, Temperature: {output.temperature}\n")
        print(f"Avg_logprob: {output.avg_logprob:.5f}, Compression Ratio: {output.compression_ratio:.5f}, Temperature: {output.temperature}\n",file=log_file)
    return prompt[:init_prompt_length]

    

def setup_transcriber(model = "openai/whisper-large-v2"):
    '''
    Setup transcriber for ASR model.  
    
    Available models:
    openai/whisper-large-v2 (default)
    
    
    '''
    print("Preparing transcriber")
    
    transcriber = WhisperModel(model, device="cuda", compute_type="float16")
    
    print("Transcriber setup complete")
    return transcriber
        
if __name__ == "__main__":
    # Define the audio capture parameters
    lt_options = LiveTranscriptConfig()
    
    config_file_name = 'config_live_transcript.json'
    
    if os.path.isfile(config_file_name):
        lt_options.loadConfig(config_file_name)
        print("Config loaded")
    else:
        lt_options.writeConfig(config_file_name)
        print("Default Config created")

    transcriber = setup_transcriber(model = "large-v2")
    
    q_list = queue.Queue()

    sd.default.device = [lt_options.device_input,lt_options.device_output]
    
    audiostream = sd.InputStream(samplerate=lt_options.sample_rate,
                                  blocksize=lt_options.block_size, 
                                  channels=2,
                                  dtype= 'float32', #sounddevice can only support float32 and not fp16 used in faster-whisper
                                  callback=audio_callback)
    print("Program Started")
    init_prompt = input("Special Words:")
    init_prompt = lt_options.starting_words + init_prompt 
    if (lt_options.debug_mode): #DEBUG ONLY
        log_file = open("log.txt","w",encoding='utf-8')
        print(lt_options,file=log_file)
        print(f"Initial Prompt: {init_prompt}",file=log_file)
    init_prompt_length = len(init_prompt)
    prompt = init_prompt
    
    if (lt_options.circular_audio):    
        global previous_audio_buffer
        previous_audio_buffer = None
    
    with audiostream:
        try:
            while True:
                if (q_list.qsize()>10):
                    print("Overloaded, Sounddevice temporary put on hold")
                    sd.sleep(10) 
                prompt = transcribe_translate(transcriber,
                                              init_prompt_length=init_prompt_length,
                                              prompt=prompt,
                                              debug_mode=lt_options.debug_mode)
        except KeyboardInterrupt:
            sd.stop()
            torch.cuda.empty_cache()
            if lt_options.debug_mode: #DEBUG ONLY 
                log_file.close()
            print("terminated")

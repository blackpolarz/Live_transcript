# -*- coding: utf-8 -*-
"""
A simplified program to transcribe live streams using Whisper AI's model.

To use, you can simply open terminal and type python Live_Transcript_v[version number] 

@author: BlackPolar
"""
import time as t
#import logging
import torch
import sounddevice as sd
import sys
import queue
import gc
import numpy as np
from threading import Event
from faster_whisper import WhisperModel,utils

import string



import json
from dataclasses import dataclass,field,asdict

import os
import Live_Transcript_config_gen


@dataclass()
class LiveTranscriptConfig:
    sample_rate: int = 16000
    sample_duration:int = 5
    model: str = "large-v3"
    block_size:int = field(init=False)
    device_input:str = "CABLE Output (VB-Audio Virtual , MME"
    device_output:str = "CABLE Input (VB-Audio Virtual , MME"
    circular_audio:bool = True
    audio_overlap:int = 2
    starting_words:str = "vtuber,hololive,japanese and english,"
    add_prompt_threshold:float = -0.5 
    task:str = "translate"
    beam_size:int = 5
    best_of:int = 3
    patience:float = 1.5
    repetition_penalty:float = 1.05
    log_prob_threshold:float = -0.99
    no_speech_threshold:float = 0.8
    condition_on_previous_text:bool = True
    prompt_reset_on_temperature:float = 0.2
    word_timestamps:bool = True
    vad_filter:bool = True
    vad_threshold: float = 0.6
    min_silence_duration_ms: int = 500
    debug_mode:bool = False
    file_only_mode: bool = False
    audio_file:str = ""
    special_words:str = ""
    
    def __post_init__(self):
        self.block_size = self.sample_rate * self.sample_duration
        
        
    def loadConfig(self,config_file_name):    
        with open(config_file_name, 'r') as f:
            lt_config = json.load(f)
        self.sample_rate = lt_config["sample_rate"]
        self.sample_duration = lt_config["sample_duration"]
        self.model = lt_config["model"]
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
        self.word_timestamps = lt_config["word_timestamps"]
        
        self.vad_filter = lt_config["vad_filter"]
        self.vad_threshold = lt_config["vad_threshold"]
        self.min_silence_duration_ms = lt_config["min_silence_duration_ms"]
        self.debug_mode = lt_config["debug_mode"]
        self.file_only_mode = lt_config["file_only_mode"]
        
        self.audio_file = lt_config["audio_file"]
        self.special_words = lt_config["special_words"]
        
    def writeConfig(self,config_file_name):
        with open(config_file_name, 'w') as f:
            json.dump(asdict(self), f,indent= 4)

@dataclass()
class PreviousData:
    prev_audio: np.ndarray = None
    prev_sentence : str = None

# Create a callback function to handle audio input
def audio_callback(indata,frames,time, status):
    
    if status:
        print(status, file=sys.stderr)
    
    #Audio is dual channel, hence there is a need to combine them.
    audio = np.concatenate([indata[:, 0], indata[:, 1]])
    
    try:
        q_list.put_nowait(audio[:]) 
    except queue.Full: #This condition will never happen as there is no limit. 
        pass    



def transcribe_translate(transcriber,init_prompt_length,prompt='vtuber,japanese and english,hololive',debug_mode=False,**kwarg):
    '''
    debug_mode only used to check on prompts,avg_logprob,compression ratio and temperature of each translation
    
    
    
    '''    
    
    try:
        audio = q_list.get_nowait()
    except queue.Empty:
        Event().wait(0.1)
        return prompt
    start = t.perf_counter() #Rough time to tell how long it takes to generate each segment
    
    if (lt_options.circular_audio):
        if pd.prev_audio is not None:
            audio = np.concatenate((pd.prev_audio,audio))
    
    
    segment,info = transcriber.transcribe(audio,
                                          task = lt_options.task,
                                          beam_size= lt_options.beam_size,
                                          best_of= lt_options.best_of,
                                          patience=lt_options.patience,
                                          repetition_penalty=lt_options.repetition_penalty,
                                          temperature= [0.0,0.1,0.2,0.4,0.6,0.8,1.0],
                                          log_prob_threshold = lt_options.log_prob_threshold,
                                          no_speech_threshold = lt_options.no_speech_threshold,
                                          condition_on_previous_text= lt_options.condition_on_previous_text,
                                          prompt_reset_on_temperature=lt_options.prompt_reset_on_temperature,
                                          word_timestamps = lt_options.word_timestamps,
                                          vad_filter = lt_options.vad_filter,
                                          vad_parameters=dict(threshold=lt_options.vad_threshold,
                                                              min_silence_duration_ms=lt_options.min_silence_duration_ms),
                                          initial_prompt=prompt
                                          )
    resultant_sentence,avg_score = process_segments(segment)
    
    if (debug_mode):
        segment_jp,_ = transcriber.transcribe(audio,
                                              task = "transcribe",
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
        resultant_sentence_jp = process_segments(segment_jp)
        
        
    if resultant_sentence is None:
        print("**IGNORED**")
        return prompt[:init_prompt_length]
    
    if (len(resultant_sentence) == 0):
        print("**IGNORED**")
        return prompt[:init_prompt_length]
    
    if (resultant_sentence==pd.prev_sentence):
        print("**REPEATED**")
        return prompt[:init_prompt_length]
    
    #Update previous sentence with new sentence
    pd.prev_sentence = resultant_sentence
    
    end = t.perf_counter()   
    print(f"Time taken:{end-start:.3f}|Score {avg_score:.3f}: {resultant_sentence}")
    
    if (lt_options.circular_audio):
        if(avg_score < (lt_options.log_prob_threshold*1.5)): #Indicates a potentially poor translation
            pd.prev_audio = audio[-lt_options.sample_rate * lt_options.sample_duration:] #It might just be a noisy environment with no real text. 
            #Feed the past 5seconds to next 5secs and generate from it.
        else:
            pd.prev_audio = audio[-lt_options.sample_rate * lt_options.audio_overlap:]    

    
    if (debug_mode):
        print(f"Prompt:{prompt}",file=log_file)
        print(f"Transcribed: {resultant_sentence_jp}",file=log_file)
        print(f"Score {avg_score:.3f}: {resultant_sentence}",file=log_file) #DEBUG ONLY
        
    #Condition where the score is larger than the add prompt threshold, hence we should add the output to prompt and update previous sentence
    if ((avg_score > lt_options.add_prompt_threshold) & isinstance(prompt,str)):
        prompt = prompt[:init_prompt_length] + resultant_sentence 
        
        return prompt      
    
    return prompt[:init_prompt_length]
    

    

def setup_transcriber(model = "openai/whisper-large-v2"):
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
    print("Preparing transcriber")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if torch.cuda.is_available() else "float32"
    # device = "cpu"
    # compute_type = "float32" 
    if model not in utils.available_models():
        print("No Such Model found, will be defaulting to faster-whisper-large-v2")
        transcriber = WhisperModel(model_size_or_path = "large-v2", device=device, compute_type=compute_type)
    else:
        transcriber = WhisperModel(model_size_or_path = model, device=device, compute_type=compute_type,num_workers=1)
    
    print("Transcriber setup complete")
    return transcriber

def transcribe_file(audio_file,output_file):

    segments,info = transcriber.transcribe(audio = audio_file,
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
    for segment in segments:
        # print(segment)
        print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text),file=output_file)
    
    print("File transcribe complete")


def process_segments(segment):
    sentence = []
    resultant_sentence = None
    score = 0
    num_of_segment = 0
    filtered_words=["translate","subtitle","subscribe","watching","subtitles"]
    
    for segment_data in segment:

        if not any(word in segment_data.text for word in filtered_words): 
            sentence.append(segment_data.text)
            score += segment_data.avg_logprob
            num_of_segment +=1
    if num_of_segment!=0:
        resultant_sentence = combine_strings(sentence,filtered_words)
        avg_score = score/num_of_segment
    else:
        avg_score = score
    return resultant_sentence,avg_score

def combine_strings(strings, filtered_words=None):
    if filtered_words is None:
        filtered_words = set()
    else:
        filtered_words = set([word.lower() for word in filtered_words])

    result = []
    used_words = set()
    
    for i in range(0, len(strings)):
        

        mod_strings = strings[i].translate(str.maketrans('', '', string.punctuation))
        current_string = mod_strings.strip().lower()
        current_words = current_string.split()

        # Check if any word in the current string is a filtered word
        if any(word.lower() in filtered_words for word in current_words):
            continue

        
        # Check if any word in the current string is already used
        if not any(word in used_words for word in current_words):
            if (len(result)==0):
                result.append(strings[i].strip())
                used_words.update(word.lower() for word in current_words)
                continue            
            # Check for overlapping with the last string in the result
            overlap_index = result[-1].find(current_string)
            
            if overlap_index != -1:
                # Combine strings without showing the overlap
                result[-1] += strings[i][overlap_index + len(result[-1]):]
            else:
                # Add the current string to the result with the original casing
                result.append(strings[i].strip())
                used_words.update(word.lower() for word in current_words)

    # Join the result into a sentence
    sentence = ' '.join(result)
    return sentence




if __name__ == "__main__":
    # Define the audio capture parameters
    lt_options = LiveTranscriptConfig()
    
    config_file_name = 'config_live_transcript.json'
    
    Live_Transcript_config_gen.main()
    
    
    
    lt_options.loadConfig(config_file_name)
    print("Config loaded")
 
    transcriber = setup_transcriber(model = lt_options.model)
    
    q_list = queue.Queue()
    
    sd.default.device = [lt_options.device_input,lt_options.device_output]
    
    audiostream = sd.InputStream(samplerate=lt_options.sample_rate,
                                  blocksize=lt_options.block_size, 
                                  channels=2,
                                  dtype= 'float32', #sounddevice can only support float32 and not fp16 used in faster-whisper
                                  callback=audio_callback)
    
    if (lt_options.circular_audio): 
        pd = PreviousData()
    
    print("Program Started")
    
    #GUI MODE
    init_prompt = lt_options.starting_words + lt_options.special_words 
    
    
    if (lt_options.debug_mode): #DEBUG ONLY
        log_file = open("log.txt","w",encoding='utf-8')
        print(lt_options,file=log_file)
        print(f"Initial Prompt: {init_prompt}",file=log_file)
    
    init_prompt_length = len(init_prompt)
    prompt = init_prompt
    
    if lt_options.file_only_mode:
        output_file = open("transcription-gui.txt","w",encoding='utf-8')
        print(lt_options,file= output_file)
        start = t.perf_counter()
        transcribe_file(audio_file = lt_options.audio_file,
                        output_file=output_file)
        end = t.perf_counter()
        print(f"Time taken:{end-start}",file=output_file)
        output_file.close()
    else:
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
                gc.collect()
                if lt_options.debug_mode: #DEBUG ONLY 
                    log_file.close()
                    print("terminated")

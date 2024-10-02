# -*- coding: utf-8 -*-
"""
A simplified program to transcribe live streams using Whisper AI's model.

To use, you can simply open terminal and type python Live_Transcript_v[version number] 
CLI support is also possible. 

Please refer to https://github.com/blackpolarz/Live_transcript

@author: BlackPolar
"""
import time as t
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
from typing import Optional

import os
import platform
from pprint import pprint
import argparse

#Other supporting modules
import Live_Transcript_GUI
import Win_Sound_Utility


@dataclass()
class LiveTranscriptConfig:
    sample_rate: int = 16000
    sample_duration:int = 5
    model: str = "large-v3"
    block_size:int = field(init=False)
    device_input:str = "CABLE Output (VB-Audio Virtual , MME"
    device_input_name:str = "CABLE Output (VB-Audio Virtual , MME"
    device_output:str = "CABLE Input (VB-Audio Virtual , MME"
    device_output_name:str = "CABLE Input (VB-Audio Virtual , MME"
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
    audio_file: Optional[str] = None
    special_words: Optional[str] = None
    filtered_words: Optional[str] = None
    
    def __post_init__(self):
        self.block_size = self.sample_rate * self.sample_duration
    
    def loadConfig(self,config_file_name):    
        with open(config_file_name, 'r') as f:
            lt_config = json.load(f)
        for key, value in lt_config.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                print(f"Warning: '{key}' is not a valid attribute.")
    
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




def transcribe_translate(transcriber,init_prompt_length,prompt='vtuber,japanese and english,hololive',**kwarg):
    '''
    Function to transcribe and translate any audio input.

    Parameters
    ----------
    transcriber : WhisperModel Object
        Use to transcribe audio data
    init_prompt_length : int
        Initial prompt length to reset the prompt to the original length  
    prompt : str, optional
        DESCRIPTION. The default is 'vtuber,japanese and english,hololive'.
    **kwarg : others, optional

    Returns
    -------
    prompt: str
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
    
    if (lt_options.debug_mode):
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
        
        
    if resultant_sentence is None or (len(resultant_sentence) == 0):
        print("**IGNORED**")
        pd.prev_sentence = None
        return prompt[:init_prompt_length]
    
    if (resultant_sentence==pd.prev_sentence):
        print("**REPEATED**")
        return prompt[:init_prompt_length]
    
    
    #Update previous sentence with new sentence
    pd.prev_sentence, pd.prev_audio = update_previous(resultant_sentence,audio,avg_score)
    
    
    end = t.perf_counter()   
    print(f"Time taken:{end-start:.3f}|Score {avg_score:.3f}: {resultant_sentence}")
    
    
    if (lt_options.debug_mode):
        print(f"Prompt:{prompt}",file=log_file)
        print(f"Transcribed: {resultant_sentence_jp}",file=log_file)
        print(f"Score {avg_score:.3f}: {resultant_sentence}",file=log_file) #DEBUG ONLY
        
    #Condition where the score is larger than the add prompt threshold, hence we should add the output to prompt and update previous sentence
    if ((avg_score > lt_options.add_prompt_threshold) & isinstance(prompt,str)):
        # prompt = prompt[:init_prompt_length] + output.text
        prompt = prompt[:init_prompt_length] + resultant_sentence #NEED TO VERIFY AGAIN 
        
        return prompt
    
    return prompt[:init_prompt_length]
    

    

def setup_transcriber(model = "openai/whisper-large-v2",num_workers = 2):
    '''
    Setup pipeline for ASR model. 
    
    If transcription is taking a long time,you might want to use a smaller model. 
    
    Note: We are using the faster-whisper model.
    
    Available models:
    openai/whisper-large-v3 
    openai/whisper-large-v2 (default)
    openai/whisper-medium
    openai/whisper-small
    openai/whisper-tiny
    
    '''
    print("Preparing transcriber")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if torch.cuda.is_available() else "float32"

    if model not in utils.available_models():
        print("No Such Model found, will be defaulting to faster-whisper-large-v2")
        transcriber = WhisperModel(model_size_or_path = "large-v2", device=device, compute_type=compute_type)
    else:
        transcriber = WhisperModel(model_size_or_path = model, device=device, compute_type=compute_type,num_workers=num_workers)
    
    print("Transcriber setup complete")
    return transcriber

def transcribe_file(audio_file,output_file):
    '''
    Transcribe files using the whisper model selected.

    Parameters
    ----------
    audio_file : Audio file
        Input Audio file for transcription
    output_file : Text file
        Output text file for transcription

    Returns
    -------
    None.

    '''
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
    '''
    Function used to process segment object into sentences.
    This function attempts to eliminate duplicates, reconstructs sentence and filters
    common hallucination. The avg_logprob is recalculated to provide an average score for the user
    to determine the accuracy of the text transcription/translation.
    
    Note that this is only useful in EN setting.

    Parameters
    ----------
    segment : Segment Object
        Each segment contains 
        id, 
        seek, 
        start, 
        end, 
        text, 
        tokens, 
        temperature,
        avg_logprob,
        compression_ratio,
        no_speech_prob,
        words.
    Please refer to faster-whisper github repo for more information.

    Returns
    -------
    resultant_sentence : str
        Complete sentence after processing. 
    avg_score : float
        Average score to determine the accuracy of the text.

    '''
    sentence = []
    resultant_sentence = None
    score = 0
    num_of_segment = 0
    if lt_options.filtered_words is None:
        filtered_words = {"translate","subtitle","subscribe","watching","subtitles"} 
    else:
        filtered_words = set(lt_options.filtered_words)

    for segment_data in segment:
        if not any(word.lower() in segment_data.text for word in filtered_words): 
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
    '''
    Function that combines multiple strings into proper sentences. 

    Parameters
    ----------
    strings : List[str]
        A list of sentences to be combined
    filtered_words : Set{str}, optional
        A set of common hallucinated words. 

    Returns
    -------
    sentence : str
        Processed Sentence which eliminates duplicates where possible and filter hallucinations.

    '''
    
    
    ##Redundant
    if filtered_words is None:
        filtered_words = set()
    else:
        filtered_words = set(word.lower() for word in filtered_words)

    result = []
    # used_words = set(word.lower() for word in result[0].split())
    used_words = set()
    
    
    for i in range(0, len(strings)):
        

        mod_strings = strings[i].translate(str.maketrans('', '', string.punctuation))
        current_string = mod_strings.strip().lower()
        current_words = current_string.split()

        # Check if any word in the current string is a filtered word
        # Redundant but somehow it helps as an secondary check.
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

def update_previous(resultant_sentence,audio,avg_score):
    '''
    Function used to update previous sentence and audio.

    Parameters
    ----------
    resultant_sentence : str
    audio : numpy array
    avg_score : float

    Returns
    -------
    resultant_sentence : str
    prev_audio: numpy array

    '''
    if (lt_options.circular_audio):
        if(avg_score < (lt_options.log_prob_threshold*1.5)): #Indicates a potentially poor translation
            #Feed the past 5seconds to next 5secs and generate from it.
            prev_audio = audio[-lt_options.sample_rate * lt_options.sample_duration:] #It might just be a noisy environment with no real text. 
        else:
            #Feed the audio overlaps so that sentence are complete. Might need better algorithm to have dynamic audio_overlap instead of fixed.
            prev_audio = audio[-lt_options.sample_rate * lt_options.audio_overlap:]    
        
        return resultant_sentence,prev_audio
    
    return resultant_sentence,None

def apply_options(lt_options, options):
    for option in options:
        key, value = option.split('=')
        if hasattr(lt_options, key):
            setattr(lt_options, key, value)
            print(f"{key} changed to {value}")
        else:
            print(f"Warning: {key} is not a valid option.")
    


if __name__ == "__main__":
    
    config_file_name = 'config_live_transcript.json'
    
    parser = argparse.ArgumentParser(description="Live Transcript Configuration")
    parser.add_argument('--no_gui', action='store_true', help="Run without GUI")
    parser.add_argument('-o', '--options', nargs='*', help="Modify options (key=value)")
    parser.add_argument('--config_file',type=str, help="Specify the configuration file name")
    parser.add_argument('--input_file',type=str, help="Specify the input file name to be transcribed")
    parser.add_argument('--output_file',type=str, help="Specify the output file name")
    args = parser.parse_args()
    
    # Define the audio capture parameters
    lt_options = LiveTranscriptConfig()
    
    if args.config_file:
        config_file_name = args.config_file
    
    if not args.no_gui:
        Live_Transcript_GUI.main()
    
    
    try:
        lt_options.loadConfig(config_file_name)
        print("Config loaded")
        
    except FileNotFoundError:
        print("{config_file_name} not found! Reopening GUI")
        Live_Transcript_GUI.main()
    
    if args.options:
        print("triggered")
        apply_options(lt_options, args.options)
    
    if args.input_file:
        lt_options.file_only_mode = True
        lt_options.audio_file = args.input_file    
    
    if args.output_file:
        output_file_name = args.output_file
    
    pprint(lt_options)
    
    if platform.system() == 'Windows':
        Win_Sound_Utility.main()  
    
    transcriber = setup_transcriber(model = lt_options.model,
                                    num_workers= 6)
    
    q_list = queue.Queue()
    
    sd.default.device = [lt_options.device_input,lt_options.device_output]

    #Using InputStream instead of Stream as Stream has significant delay, making 
    #the audio not match with the video.
    audiostream = sd.InputStream(samplerate=lt_options.sample_rate,
                                  blocksize=lt_options.block_size, 
                                  channels=2,
                                  dtype= 'float32', #sounddevice can only support float32 and not fp16 used in faster-whisper
                                  callback=audio_callback)
    

    
    
    if (lt_options.circular_audio): 
        pd = PreviousData()
    
    print("Program Started")
    
    #Setup initial prompt
    if lt_options.special_words is None:
        init_prompt = lt_options.starting_words
    else:
        init_prompt = lt_options.starting_words + lt_options.special_words 
    
    init_prompt_length = len(init_prompt)
    prompt = init_prompt[:]
    
    if (lt_options.debug_mode): #DEBUG ONLY
        log_file = open("log.txt","w",encoding='utf-8')
        print(lt_options,file=log_file)
        print(f"Initial Prompt: {init_prompt}",file=log_file)
    
    
    if lt_options.file_only_mode:
        
        output_file_name = args.output_file or "transcription.txt"
        output_file = open(output_file_name,"w",encoding='utf-8')
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
                        if (q_list.qsize()>15):
                            print("Reseting Queue to prevent overloaded")
                            q_list = queue.Queue()
                            sd.sleep(50)
                            continue
                        print("Overloaded, Sounddevice temporary put on hold")
                        sd.sleep(10) 
                    prompt = transcribe_translate(transcriber,
                                                  init_prompt_length=init_prompt_length,
                                                  prompt=prompt)
            except KeyboardInterrupt:
                sd.stop()
                torch.cuda.empty_cache()
                gc.collect()
                print("Program Ended")
                
                if lt_options.debug_mode: #DEBUG ONLY 
                    log_file.close()
                    print("terminated")
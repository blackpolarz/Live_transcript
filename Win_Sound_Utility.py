# -*- coding: utf-8 -*-
"""
Created on Tue Aug 20 20:47:41 2024

@author: Blackpolar
"""

#Code adapted from 
#https://stackoverflow.com/questions/57929296/reverse-engineer-listen-to-this-device-on-windows-reverse-engineer-windows-whe


from comtypes import GUID
from comtypes.automation import VT_BOOL, VT_LPWSTR, VT_EMPTY
from comtypes.persist import STGM_READWRITE
from pycaw.api.mmdeviceapi import PROPERTYKEY

from pycaw.api.mmdeviceapi.depend import PROPVARIANT
from pycaw.utils import AudioUtilities

import json

#Hardcoded values to modify the listen tab
LISTEN_SETTING_GUID = "{24DBB0FC-9311-4B3D-9CF0-18FF155639D4}"
CHECKBOX_PID = 1
LISTENING_DEVICE_PID = 0

def main():
    config_file_name = 'config_live_transcript.json'
    with open(config_file_name, 'r') as f:
        lt_config = json.load(f)
    microphone_name = lt_config["device_input_name"] 
    if microphone_name is None:
        raise Exception("Invalid Input Audio device, Please check your config.")
    listening_device_name = lt_config["device_output_name"]  #Set to None to use the default playback device
    enable_listening = True
    store = get_device_store(microphone_name)
    if store is None:
        print("failed to open property store")
        exit(1)

    set_listening_checkbox(store, enable_listening)
    set_listening_device(store, listening_device_name)

#Write to the checkbox property
def set_listening_checkbox(property_store, value:bool):
    checkbox_pk = PROPERTYKEY()
    checkbox_pk.fmtid = GUID(LISTEN_SETTING_GUID)
    checkbox_pk.pid = CHECKBOX_PID

    new_value = PROPVARIANT(VT_BOOL)
    new_value.union.boolVal = value
    property_store.SetValue(checkbox_pk, new_value)

#Write to the device property
def set_listening_device(property_store, output_device_name):
    if output_device_name is not None:
        listening_device_guid = get_GUID_from_name(output_device_name)
    else:
        listening_device_guid = None

    device_pk = PROPERTYKEY()
    device_pk.fmtid = GUID(LISTEN_SETTING_GUID)
    device_pk.pid = LISTENING_DEVICE_PID

    if listening_device_guid is not None:
        new_value = PROPVARIANT(VT_LPWSTR)
        new_value.union.pwszVal = listening_device_guid
    else:
        new_value = PROPVARIANT(VT_EMPTY)

    property_store.SetValue(device_pk, new_value)

#Gets the device store from the device name
def get_device_store(device_name:str):
    device_guid = get_GUID_from_name(device_name)
    enumerator = AudioUtilities.GetDeviceEnumerator()
    dev = enumerator.GetDevice(device_guid)

    store = dev.OpenPropertyStore(STGM_READWRITE)
    return store

#This is just a helper method to turn a device name into a GUID.
def get_GUID_from_name(device_name:str) -> str:
    input_devices = get_list_of_active_coreaudio_devices("input")
    for device in input_devices:
        #Using approximate match instead of ==
        if device_name in device.FriendlyName:
            return device.id
    output_devices = get_list_of_active_coreaudio_devices("output")
    for device in output_devices:
        #Using approximate match instead of ==
        if device_name in device.FriendlyName:
            return device.id
    raise ValueError("Device not found!")

#Helper method to get all (active) devices
def get_list_of_active_coreaudio_devices(device_type:str) -> list:
    import comtypes
    from pycaw.pycaw import AudioUtilities, IMMDeviceEnumerator, EDataFlow, DEVICE_STATE
    from pycaw.constants import CLSID_MMDeviceEnumerator

    if device_type != "output" and device_type != "input":
        raise ValueError("Invalid audio device type.")

    if device_type == "output":
        EDataFlowValue = EDataFlow.eRender.value
    else:
        EDataFlowValue = EDataFlow.eCapture.value
    # Code to enumerate devices adapted from https://github.com/AndreMiras/pycaw/issues/50#issuecomment-981069603

    devices = list()
    device_enumerator = comtypes.CoCreateInstance(
        CLSID_MMDeviceEnumerator,
        IMMDeviceEnumerator,
        comtypes.CLSCTX_INPROC_SERVER)
    if device_enumerator is None:
        raise ValueError("Couldn't find any devices.")
    collection = device_enumerator.EnumAudioEndpoints(EDataFlowValue, DEVICE_STATE.ACTIVE.value)
    if collection is None:
        raise ValueError("Couldn't find any devices.")

    count = collection.GetCount()
    for i in range(count):
        dev = collection.Item(i)
        if dev is not None:
            if not ": None" in str(AudioUtilities.CreateDevice(dev)):
                devices.append(AudioUtilities.CreateDevice(dev))

    return devices

if __name__ == "__main__":
    main()
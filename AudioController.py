import threading
import subprocess
import DisplayController
from time import sleep
from Globals import global_variables
from Config import global_config
from Logger import log, INFO, WARNING, ERROR


# Variables meant specifically for the Audio Controller
audio_thread_count = 0


def fix_audio_path(input_path):
    """
    Fixes the audio path string to be usable by commands outside of Python. While Python automatically handles spaces
    inside of path strings, commands executed using subprocess.call() do not. This essentially replaces all spaces
    with a backslash plus a space. Example: " " -> "\ "
    :param input_path: Input path in need of backslashes behind the spaces.
    :return:
    """
    output_path = input_path.replace(" ", "\\ ")
    return output_path


def audio_logic(input_folder_index, input_file_index):
    """
    Takes in a folder_index and file_index. If that file_index should exist in the folder specified AND the maximum
    audio thread limit hasn't been hit, start up an audio thread that will play the audio file specified.
    :param input_folder_index: An integer corresponding to global_variables.file.folder_names
    :param input_file_index: An integer corresponding to global_variables.file.file_names
    :return:
    """
    file_paths = global_variables.file.file_paths[input_folder_index]
    if len(file_paths) - 1 >= input_file_index:
        if global_config.audio.max_sound_threads > global_variables.audio.thread_count:
            good_file_path = fix_audio_path(file_paths[input_file_index])
            audio_thread = threading.Thread(target=play_audio_file, args=(good_file_path,))
            # audio_thread.daemon = True
            audio_thread.start()
        else:
            pass
    else:
        pass


def play_audio_file(pathtofile):
    global_variables.audio.thread_count += 1
    DisplayController.frame_top.update_thread_count()
    # subprocess.call("paplay --device=PythonSoundboardOutput " + pathtofile, shell=True, stdout=subprocess.PIPE)
    audio = subprocess.Popen("exec paplay --device=PythonSoundboardOutput " + pathtofile, shell=True, stdout=subprocess.PIPE)

    while audio.poll() is None:
        if global_variables.audio.kill_audio is True:
            audio.terminate()
            break
        else:
            sleep(global_config.audio.polling_rate)

    global_variables.audio.thread_count -= 1
    DisplayController.frame_top.update_thread_count()
    return 0


def start_audio_setup():
    audio_start_command = """ pactl load-module module-null-sink sink_name=PythonSoundboardOutput 
    sink_properties=device.description="Python_Soundboard_Output" rate=48000 """
    loopback_start_command = """ pactl load-module module-loopback source=PythonSoundboardOutput.monitor 
    latency_msec=5 """
    subprocess.call(audio_start_command, shell=True)
    if global_config.audio.create_loopback is True:
        subprocess.call(loopback_start_command, shell=True)


def end_audio_setup():
    global_variables.audio.kill_audio = True
    sleep(global_config.audio.polling_rate)
    global_variables.audio.kill_audio = False
    audio_end_command = """ pactl unload-module module-null-sink """
    subprocess.call(audio_end_command, shell=True)
    loopback_end_command = """ pactl unload-module module-loopback """
    subprocess.call(loopback_end_command, shell=True)





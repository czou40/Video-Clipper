from pydub import AudioSegment
from pydub.effects import normalize
from moviepy.editor import *
import speech_recognition as sr
import glob
import json
import os



def extract_audio(file_path):
    video = VideoFileClip(file_path)
    audio = video.audio
    new_file_name = os.path.splitext(file_path)[0] + " - Audio.mp3"
    audio.write_audiofile(new_file_name)
    return new_file_name


def clip_audio(file_path, file_format, directory, step=100, threshold=1500):
    print("Starting audio clipping")
    audio = AudioSegment.from_file(file_path, format=file_format)
    print("Loading finished")
    slices = list(audio[::step])
    print("Segmenting finished")
    length = len(slices)
    isInterval = [False for i in range(length)]
    interval_start = []
    interval_end = []
    curr = 0
    prev = 0
    nex = 0
    for i in range(length):
        if i % 1000 == 0:
            print("Analyzing, current progress: {0}/{1}".format(i, length))
        if i > 0:
            prev = curr
            curr = nex
            if i < length - 1:
                nex = slices[i + 1].max
            else:
                nex = 0
            if max(prev, curr, nex) >= threshold:
                isInterval[i] = True
                if i == 0 or not isInterval[i - 1]:
                    interval_start.append(i)
            else:
                if i > 0 and isInterval[i - 1]:
                    interval_end.append(i)
    if isInterval[length - 1] and len(interval_start) != len(interval_end):
        interval_end.append(length - 1)
    print("Analysis finished")
    length = len(interval_start)
    interval_in_seconds_start = []
    interval_in_seconds_end = []
    if not os.path.exists(directory):
        os.makedirs(directory)
    for i in range(length):
        if i % 20 == 0:
            print("Exporting, current progress: {0}/{1}".format(i, length))
        interval_in_seconds_start.append(interval_start[i] * step / 1000)
        interval_in_seconds_end.append((interval_end[i] + 1) * step / 1000)
        new_audio = AudioSegment.empty()
        for j in range(interval_start[i], interval_end[i] + 1):
            new_audio += slices[j]
        new_audio.export(directory + "/" + str(i) + ".wav", format="wav")
    print("Audio clipping finished")
    return interval_in_seconds_start, interval_in_seconds_end


def clip_video(video, intervals, directory):
    start = intervals[0]
    end = intervals[1]
    length = len(start)
    for i in range(length):
        if i < length - 1:
            clipped = video.subclip(start[i], end[i])
        else:
            clipped = video.subclip(start[i])
        clipped.write_videofile(directory + "/" + str(i) + ".mp4")


def rename(file_path):
    result = recognize(file_path + ".wav")
    if result == "":
        os.rename(file_path + ".wav",
                  os.path.dirname(file_path) + r'/Unknown - ' + os.path.basename(file_path) + ".wav")
        os.rename(file_path + ".mp4",
                  os.path.dirname(file_path) + r'/Unknown - ' + os.path.basename(file_path) + ".mp4")
    else:
        os.rename(file_path + ".wav",
                  os.path.dirname(file_path) + r'/' + result + ' - ' + os.path.basename(file_path) + ".wav")
        os.rename(file_path + ".mp4",
                  os.path.dirname(file_path) + r'/' + result + ' - ' + os.path.basename(file_path) + ".mp4")


def recognize(file_path):
    print("Starting renaming files")
    AUDIO_FILE = file_path
    r = sr.Recognizer()
    with sr.AudioFile(AUDIO_FILE) as source:
        audio = r.record(source)
    credentials = {
        # fill in your credentials
   }
    try:
        result = r.recognize_google_cloud(audio, credentials_json=json.dumps(credentials), language="cmn-CN").strip()
        print("Audio {0}: {1}".format(os.path.basename(file_path), result))
        return result
    except sr.UnknownValueError:
        print("Google Cloud Speech could not understand audio " + os.path.basename(file_path))
        return ""
    except sr.RequestError as e:
        print("Could not request results from Google Cloud Speech service; {0}".format(e))
        return ""


def rename_all(directory):
    files = glob.glob(directory + "/*.wav")
    for i in files:
        rename(os.path.splitext(i)[0])


def process_video(file_path):
    save_directory = os.path.join(os.path.dirname(file_path), "result")
    os.makedirs(save_directory)
    audio_file_path = extract_audio(file_path)
    intervals = clip_audio(audio_file_path, "mp3", save_directory, step=100, threshold=1500)
    clip_video(VideoFileClip(file_path), intervals, save_directory)
    rename_all(save_directory)
    return save_directory

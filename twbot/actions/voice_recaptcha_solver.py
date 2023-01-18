import os
import pydub
import psutil
import subprocess
import speech_recognition as sr

from speechbrain.pretrained import EncoderDecoderASR
from pydub import AudioSegment
from surviral_avd.settings import BASE_DIR

if not os.path.exists(os.path.join(BASE_DIR, 'captcha')):
    os.mkdir(os.path.join(BASE_DIR, 'captcha'))
captcha_audio_path = os.path.join(BASE_DIR, 'captcha/output.wav')


# def increase_audio_sound():
#     audio = AudioSegment.from_wav(os.path.normpath(captcha_audio_path))

#     # increase volume by 30 dB
#     audio = audio + 30

#     os.remove(captcha_audio_path)

#     # save the output
#     audio.export(captcha_audio_path, "wav")


def start_recording():
    if os.path.exists(captcha_audio_path):
        os.remove(captcha_audio_path)

    output_path = captcha_audio_path
    # record_p = f"ffmpeg -f pulse -i default {output_path}"
    record_p = f"arecord -d 5 -f U8 {output_path}"
    p = subprocess.Popen([record_p], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    return p


def stop_recording(record_process):
    process = psutil.Process(record_process.pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()


def load_audio():
    wav_path = captcha_audio_path.split(".")[0] + ".wav"
    sound = pydub.AudioSegment.from_mp3(os.path.normpath(captcha_audio_path))
    sound.export(os.path.normpath(captcha_audio_path), format="wav")
    # increase_audio_sound()
    sample_audio = sr.AudioFile(os.path.normpath(wav_path))
    return sample_audio


def audio_to_text(sample_audio=None):
    try:
        # r = sr.Recognizer()
        # with sample_audio as source:
        # audio = r.record(source)
        # result_text = r.recognize_google(audio)
        asr_model = EncoderDecoderASR.from_hparams(source="speechbrain/asr-transformer-transformerlm-librispeech",
                                                   savedir="pretrained_models/asr-transformer-transformerlm-librispeech",
                                                   run_opts={"device": "cpu"})
        result_text = asr_model.transcribe_file(captcha_audio_path)
        print("[INFO] Recaptcha Passcode: %s" % result_text)
        return result_text
    except Exception as e:
        return False

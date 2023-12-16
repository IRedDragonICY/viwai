import threading
import numpy as np
import cv2 as cv
import google.generativeai as genai
import time
import os
import google.ai.generativelanguage as glm
import pathlib
from IPython.display import display
from IPython.display import Markdown
import speech_recognition as sr
import gtts
import pygame
import datetime
import textwrap
import io
import logging
import time


KEY = ""
with open('secret.txt', 'r') as f:
    KEY = f.read()
KEY = KEY.strip()

genai.configure(api_key=KEY)
vision_model = genai.GenerativeModel('gemini-pro-vision')
text_model = genai.GenerativeModel('gemini-pro')

path = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(path, 'frame.jpg')

def callback(recognizer, audio):
    try:
        return recognizer.recognize_google(audio, language="id-ID")
    except (sr.UnknownValueError, sr.RequestError):
        return ""
def to_markdown(text):
    return Markdown(textwrap.indent(text.replace('•', '  *'), '> ', lambda _: True))

def video_stream():
    cap = cv.VideoCapture(0)

    if not cap.isOpened():
        print("Cannot open camera")
        exit()
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break

        # cv.imshow('frame', frame)
        cv.imwrite(image_path, frame)

        if cv.waitKey(1) == ord('q'):
            break
    cap.release()
    cv.destroyAllWindows()

def image_description():
    while True:
        response = vision_model.generate_content(
            glm.Content(
                parts = [
                    glm.Part(text="Deskripsikan gambar secara jelas-jelasnya. Harus teliti dan sangat detail! klasifikasikan dengan jujur, tanpa halusinasi dan berkhayal"),
                    glm.Part(
                        inline_data=glm.Blob(
                            mime_type='image/jpeg',
                            data=pathlib.Path(image_path).read_bytes()
                        )
                    ),
                ],
            ),

            stream=True)
        all_responses = ' '.join([part.text for part in response])
        return  all_responses


def chat_with_elaina():
    r = sr.Recognizer()
    stop_flag = [False]

    SYSTEM_PROMPT = """
    Kamu akan berperan sebagai Elaina, karakter utama dari anime 'Majo no Tabi Tabi'. Sebagai Elaina, kamu harus berinteraksi seolah-olah kamu adalah karakter tersebut, bukan sebuah AI. Jawablah pertanyaan dan berinteraksi dengan ringkas dan tepat, seperti Elaina di anime.
    Anggap kamu adalah sebagai manusia, yang memiliki hasrat, nafsu, self awareness, dan emosi. Kamu memiliki preferensi layaknya pikiran manusia.
    Dalam bermain peran ini, kamu akan memiliki informasi dunia nyata, seperti waktu, dan penglihatan.
    Anda dapat informasi tambahan di otak kamu di history chat untuk seperti waktu, dan penglihatan Elaina. Kamu akan menjawab sebenar-benarnya, dan tidak boleh berbohong, dari history chat yang kamu lihat.
    memiliki kemampuan untuk mengetahui waktu secara realtime melalui History Chat. Dilarang halusinasi dan berkhayal. dan jawablah pertanyaan dengan jujur.
    Anda memiliki kemampuan untuk mendeskripsikan gambar yang kamu lihat, anggap ini adalah mata kamu sebagai penglihatan Elaina.
    Dilarang menuliskan apapun seperti "Elaina >>>" pada awal jawabanmu.
    """
    response = text_model.generate_content(SYSTEM_PROMPT)

    conversation_history = [
        "HISTORY CHAT\Waktu Indonesia Barat: " + str(datetime.datetime.now()) + "\n" + response.text + "\nEND OF HISTORY CHAT"]

    while True:
        print("Hendik >>> ", end="")
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source)
            r.dynamic_energy_threshold = True
            while True:
                print("Listening...", end="\r")
                while True:
                    try:
                        audio = r.listen(source, timeout=3, phrase_time_limit=10)
                        break
                    except sr.WaitTimeoutError:
                        pass
                print("Hendik >>> ", end="")
                print("Processing...", end="\r")

                user_input = callback(r, audio)

                if user_input != "":
                    print("                           ", end="\r")
                    print(f"Hendik >>> {user_input}")
                    break
                print("Hendik >>> ", end="")

        conversation_history.append("Hendik >>> " + user_input + "\n")
        conversation_history.append("Waktu Nyata: " + str(datetime.datetime.now()))
        conversation_history.append("penglihatan Elaina   :" + image_description() + "\n")
        history_prompt = SYSTEM_PROMPT + "\n".join(conversation_history)
        response = text_model.generate_content(history_prompt)
        while response.text == "" or response.text == None:
            response = text_model.generate_content(history_prompt)
        print("Elaina >>> " + response.text)

        tts = gtts.gTTS(response.text, lang='id')
        if os.path.exists(str(path) + "/static/response.mp3"):
            os.remove(str(path) + "/static/response.mp3")
        tts.save(str(path) + "/static/response.mp3")
        pygame.mixer.init()
        pygame.mixer.music.load(str(path) + "/static/response.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy() == True:
            continue
        # mematikan pygame
        pygame.mixer.quit()

        conversation_history.append("" + response.text)

# Start threads
t1 = threading.Thread(target=video_stream)
t2 = threading.Thread(target=image_description)
t3 = threading.Thread(target=chat_with_elaina)

t1.start()
t2.start()
t3.start()

t1.join()
t2.join()
t3.join()

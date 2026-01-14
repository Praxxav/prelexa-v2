import queue
import threading
import sounddevice as sd
from google.cloud import speech
from google.oauth2 import service_account

RATE = 16000
CHUNK = int(RATE / 10)

credentials = service_account.Credentials.from_service_account_file(
    r"D:\Prescalelabs\acquired-voice-434104-k8-d06a45cf4cfc.json"
)

client = speech.SpeechClient(credentials=credentials)


def stream_transcript():
    audio_queue = queue.Queue()

    def callback(indata, frames, time, status):
        if status:
            print(status)
        audio_queue.put(bytes(indata))

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="en-US",
        enable_automatic_punctuation=True,
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=False,
    )

    def request_generator():
        while True:
            chunk = audio_queue.get()
            if chunk is None:
                return
            yield speech.StreamingRecognizeRequest(audio_content=chunk)

    with sd.RawInputStream(
        samplerate=RATE,
        blocksize=CHUNK,
        dtype="int16",
        channels=1,
        callback=callback,
    ):
        responses = client.streaming_recognize(
            streaming_config,
            request_generator(),
        )

        for response in responses:
            for result in response.results:
                if result.is_final:
                    yield result.alternatives[0].transcript

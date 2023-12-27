import base64
import io
import json
import logging
import threading

from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError  # pants: no-infer-dep

log = logging.getLogger()


class PollyInprocRunner(threading.Thread):
    def __init__(self, input_queue, output_queue, sentinel, access_key, secret_key):
        super().__init__(name="InprocRunner", daemon=True)

        # for interoperability with the main asyncio loop
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.sentinel = sentinel

        self.session = Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        self.polly = self.session.client("polly")

    def run(self):
        while True:
            code_text = self.input_queue.get()
            request = json.loads(code_text)

            content_type = "application/octet-stream"
            encoded_audio = ""
            try:
                response = self.polly.synthesize_speech(
                    Text=request.get("text"),
                    VoiceId=request.get("voiceId"),
                    TextType=request.get("textType", "text"),
                    OutputFormat="ogg_vorbis",
                )
            except (BotoCoreError, ClientError) as err:
                self.output_queue.put([b"stderr", str(err).encode("utf8")])
                self.output_queue.put(self.sentinel)
                self.input_queue.task_done()
                continue
            else:
                content_type = response.get("ContentType").encode("ascii")
                data_stream = response.get("AudioStream")
                buffer = io.BytesIO()
                while True:
                    chunk = data_stream.read(4096)
                    if not chunk:
                        break
                    buffer.write(chunk)
                try:
                    encoded_audio = (b"data:%s;base64," % content_type) + base64.b64encode(
                        buffer.getvalue()
                    )
                    buffer.close()
                except Exception as e:
                    log.error(str(e))

            self.output_queue.put([
                b"media",
                b'{"type":"%s","data":"%s"}' % (content_type, encoded_audio),
            ])
            self.output_queue.put(self.sentinel)
            self.input_queue.task_done()

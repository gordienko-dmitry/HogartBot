import xml.etree.ElementTree as XmlElementTree
import subprocess
import httplib2
import uuid
import os

from http.client import HTTPResponse
from typing import Optional

YANDEX_ASR_HOST: str = 'asr.yandex.net'
YANDEX_ASR_PATH: str = '/asr_xml'
CHUNK_SIZE: int = 1024 ** 2


def convert_to_pcm16b16000r(in_bytes: bytes=None) -> bytes:
    """Convert file to pcm_s16le via ffmpeg."""

    file_uid: str = uuid.uuid4().hex
    filename: str = f'./speech/in_{file_uid}.oga'
    with open(filename, 'wb') as temp_in_file:
        temp_in_file.write(in_bytes)
        temp_in_file.close()

    command: list = ['ffmpeg',
                     '-i', filename,
                     '-f', 's16le',
                     '-acodec', 'pcm_s16le',
                     '-ar', '16000',  # ouput will have 16000 Hz
                     '-'
                     ]

    pipe = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=10 ** 8)
    out_bytes = pipe.stdout.read(88200 * 4)

    if temp_in_file:
        os.remove(filename)

    return out_bytes


def speech_to_text(filename: Optional[str] = None, file_in_bytes: Optional[bytes] = None,
                   request_id: str = uuid.uuid4().hex, topic: str = 'queries', lang: str = 'ru-RU',
                   key: str = '') -> str:
    """Convert voice file or bytes of voice into text via yandex service."""

    if filename:
        with open(filename, 'br') as file:
            file_in_bytes = file.read()

    if not file_in_bytes:
        raise Exception('Neither file name nor bytes provided.')

    # Конвертирование в нужный формат
    voice_in_correct_format: bytes = convert_to_pcm16b16000r(in_bytes=file_in_bytes)

    # Формирование тела запроса к Yandex API
    url: str = YANDEX_ASR_PATH + '?uuid=%s&key=%s&topic=%s&lang=%s' % (
        request_id,
        key,
        topic,
        lang
    )

    # Считывание блока байтов
    chunks: list = read_chunks(CHUNK_SIZE, voice_in_correct_format)

    response: HTTPResponse = _get_yandex_speech_response(url, chunks)

    response_text: str = response.read()
    return _get_text_from_response_text(response_text)


def _get_text_from_response_text(response_text: str) -> str:
    """Getting text from response string."""

    xml = XmlElementTree.fromstring(response_text)
    if int(xml.attrib['success']) != 1:
        raise SpeechException('No text found.\n\nResponse:\n%s' % (response_text))

    max_confidence: float = - float("inf")
    text: str = ''

    for child in xml:
        if float(child.attrib['confidence']) > max_confidence:
            text = child.text
            max_confidence = float(child.attrib['confidence'])

    if max_confidence == - float("inf"):
        raise SpeechException('No text found.\n\nResponse:\n%s' % (response_text))

    return text


def _get_yandex_speech_response(url: str, chunks: list) -> HTTPResponse:
    """Getting response after sends voice bytes to yandex server."""
    connection = httplib2.HTTPConnectionWithTimeout(YANDEX_ASR_HOST)
    connection.connect()
    connection.putrequest('POST', url)
    connection.putheader('Transfer-Encoding', 'chunked')
    connection.putheader('Content-Type', 'audio/x-pcm;bit=16;rate=16000')
    connection.endheaders()

    # Отправка байтов блоками
    for chunk in chunks:
        connection.send(('%s\r\n' % hex(len(chunk))[2:]).encode())
        connection.send(chunk)
        connection.send('\r\n'.encode())

    connection.send('0\r\n\r\n'.encode())
    response: HTTPResponse = connection.getresponse()
    if response.getcode() != 200:
        SpeechException('Unknown error.\nCode: %s\n\n%s' % (response.getcode(), response.read()))
    return response


def read_chunks(chunk_size: int, bytes: bytes) -> list:
    """Convert bytes into list of byte chunks."""
    chunks: list = []
    while bytes:
        chunk = bytes[:chunk_size]
        bytes = bytes[chunk_size:]
        chunks.append(chunk)

    return chunks


# Создание своего исключения
class SpeechException(Exception):
    pass


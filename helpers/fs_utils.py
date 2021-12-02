import sys
import shutil
import os
import pathlib
import magic
import tarfile
import subprocess
import time
import math
import json
import sys
from io import BytesIO
from mutagen.mp3 import MP3
from mutagen.id3 import ID3


from PIL import Image
from mutagen import File


VIDEO_SUFFIXES = ("M4V", "MP4", "MOV", "FLV", "WMV", "3GP", "MPG", "WEBM", "MKV", "AVI")


def get_mime_type(file_path):
    mime = magic.Magic(mime=True)
    mime_type = mime.from_file(file_path)
    mime_type = mime_type or "text/plain"
    return mime_type



def get_media_info(path):
    try:
        result = subprocess.check_output(["ffprobe", "-hide_banner", "-loglevel", "error", "-print_format",
                                          "json", "-show_format", path]).decode('utf-8')
        fields = json.loads(result)['format']
    except Exception as e:
        return 0, None, None
    try:
        duration = round(float(fields['duration']))
    except:
        duration = 0
    try:
        artist = str(fields['tags']['artist'])
    except:
        artist = None
    try:
        title = str(fields['tags']['title'])
    except:
        title = None
    return duration, artist, title

def get_cover(path):
    song_path = os.path.join(path)
    track = MP3(song_path)
    tags = ID3(song_path)
    pict = tags.getall("APIC:")[0].data
    im = Image.open(BytesIO(pict))
    with open(f"{path}.jpeg", "w") as thumb_f:
        im.save(thumb_f)
    return f"{path}.jpeg"

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

from PIL import Image
from mutagen import File


VIDEO_SUFFIXES = ("M4V", "MP4", "MOV", "FLV", "WMV", "3GP", "MPG", "WEBM", "MKV", "AVI")


def get_mime_type(file_path):
    mime = magic.Magic(mime=True)
    mime_type = mime.from_file(file_path)
    mime_type = mime_type or "text/plain"
    return mime_type

def take_ss(video_file):
    des_dir = 'Thumbnails'
    if not os.path.exists(des_dir):
        os.mkdir(des_dir)
    des_dir = os.path.join(des_dir, f"{time.time()}.jpg")
    duration = get_media_info(video_file)[0]
    if duration == 0:
        duration = 3
    duration = duration // 2
    try:
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(duration),
                        "-i", video_file, "-vframes", "1", des_dir])
    except:
        return None

    if not os.path.lexists(des_dir):
        return None

    Image.open(des_dir).convert("RGB").save(des_dir)
    img = Image.open(des_dir)
    img.resize((480, 320))
    img.save(des_dir, "JPEG")
    return des_dir



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
    print(path)
    afile = File(path) # mutagen can automatically detect format and type of tags
    thumb = afile.tags['APIC:'].data # access APIC frame and grab the image
    return thumb

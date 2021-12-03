import asyncio
import os
import time
import subprocess
from config import Config
from pyrogram.types import Message


async def MetaData(filePath:str, user_id: int):
	print("Extracting MetaData")
	subprocess.call(f"ffmpeg -i '{filePath}' -f ffmetadata ./downloads/{str(user_id)}/metadatatemp.txt" ,shell=True)
	return f'./downloads/{str(user_id)}/metadatatemp.txt'


async def MergeAudio(input_file: str, user_id: int, meta_data: str, message: Message, format_: str):
	"""
	This is for Merging audios Together!
	:param input_file: input.txt file's location.
	:param user_id: Pass user_id as integer.
	:param message: Pass Editable Message for Showing FFmpeg Progress.
	:param format_: Pass File Extension.
	:return: This will return Merged audio File Path
	"""
	output_vid = f"downloads/{str(user_id)}/merged.{format_.lower()}"
	file_generator_command = [
		"ffmpeg",
		"-f",
		"concat",
		"-safe",
		"0",
		"-i",
		input_file,
        "-i",
        meta_data,
		"-map",
		"0",
		"-map_metadata",
		"1",
		"-c",
		"copy",
		output_vid
	]
	process = None
	try:
		process = await asyncio.create_subprocess_exec(
			*file_generator_command,
			stdout=asyncio.subprocess.PIPE,
			stderr=asyncio.subprocess.PIPE,
		)
	except NotImplementedError:
		await message.edit(
			text="Unable to Execute FFmpeg Command! Got `NotImplementedError` ...\n\nPlease run bot in a Linux/Unix Environment."
		)
		await asyncio.sleep(10)
		return None
	await message.edit("Merging Audio Now ...\n\nPlease Keep Patience ...")
	stdout, stderr = await process.communicate()
	e_response = stderr.decode().strip()
	t_response = stdout.decode().strip()
	print(e_response)
	print(t_response)
	if os.path.lexists(output_vid):
		return output_vid
	else:
		return None




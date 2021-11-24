import time
from pyrogram import Client
from pyrogram.types import CallbackQuery
from helpers.display_progress import progress_for_pyrogram
import os
import re


async def uploadVideo(c: Client,cb: CallbackQuery,merged_video_path,video_thumbnail,width,height,duration,file_size,upload_mode:bool):
	try:
		sent_ = None

		# Temporary hack for uploading everything as audio irrespective
		# of the user settings.
		# TODO: Remove the setting completely from the bot.
		upload_mode = False

		audio_file_name = os.path.basename(merged_video_path)
		audio_file_name = re.sub(r"\s\s*", ".", audio_file_name)
		audio_file_name = re.sub(r"__*", ".", audio_file_name)

		if upload_mode is False:
			c_time = time.time()
			sent_ = await c.send_audio(
				chat_id=cb.message.chat.id,
				audio=merged_video_path,
				duration=duration,
				caption=f"**{audio_file_name}**",
				file_name=audio_file_name,
				progress=progress_for_pyrogram,
				progress_args=(
					"Uploading file as audio",
					cb.message,
					c_time
				)
			)
		else:
			c_time = time.time()
			sent_ = await c.send_document(
				chat_id=cb.message.chat.id,
				document=merged_video_path,
				caption=f"** {merged_video_path.rsplit('/',1)[-1]}**",
				progress=progress_for_pyrogram,
				progress_args=(
					"Uploading file as document",
					cb.message,
					c_time
				)
			)
	except Exception as err:
		print(err)
		await cb.message.edit("Failed to upload")

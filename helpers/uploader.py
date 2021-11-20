import time
import asyncio
from pyrogram import Client
from pyrogram.types import InlineKeyboardButton,InlineKeyboardMarkup,CallbackQuery
from helpers.display_progress import progress_for_pyrogram,humanbytes
from config import Config
from hachoir.metadata import extractMetadata


async def uploadVideo(c: Client,cb: CallbackQuery,merged_video_path,width,height,duration,file_size,upload_mode:bool):
	try:
		sent_ = None
		if upload_mode is False:
			c_time = time.time()
			metadata = extractMetadata(createParser(up_path))
                        if metadata.has("duration"):
                        	duration = metadata.get('duration').seconds
                    	title = metadata.get("title") if metadata.has("title") else None
                    	artist = metadata.get("artist") if metadata.has("artist") else None
			sent_ = await c.send_audio(
				chat_id=cb.message.chat.id,
				audio=merged_video_path,
				duration=duration,
				caption=cap_mono,
				parse_mode="html",
				performer=artist,
                                title=title,
				caption=f"**File Name: {merged_video_path.rsplit('/',1)[-1]}**",
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
				caption=f"**File Name: {merged_video_path.rsplit('/',1)[-1]}**",
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

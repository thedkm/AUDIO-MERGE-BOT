import asyncio
import os
import shutil
import string
import time
import shutil, psutil
import re
from sys import executable

import pyrogram
from hachoir import metadata
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image
from pyrogram import Client, filters
from pyrogram.errors import MessageNotModified
from pyrogram.errors.exceptions.flood_420 import FloodWait
from pyrogram.methods.utilities.idle import idle
from pyrogram.types import (CallbackQuery, InlineKeyboardButton,InlineKeyboardMarkup, Message)
from pyromod import listen

from config import Config
from helpers import database
from helpers.display_progress import progress_for_pyrogram
from helpers.ffmpeg import MergeAudio, MetaData
from helpers.uploader import uploadAudio
from helpers.utils import get_readable_time, get_readable_file_size
from helpers.rclone_upload import rclone_driver, rclone_upload
from helpers.fs_utils import  get_media_info

botStartTime = time.time()

mergeApp = Client(
	name="audio-merge-bot",
	api_hash=Config.API_HASH,
	api_id=Config.API_ID,
	bot_token=Config.BOT_TOKEN,
	workers=300
)


if os.path.exists('./downloads') == False:
	os.makedirs('./downloads')


queueDB={}
formatDB={}
replyDB={}

@mergeApp.on_message( filters.command(['login']) & filters.private & ~filters.edited )
async def allowUser(c:Client, m: Message):
	passwd = m.text.split()[-1]
	if passwd == Config.PASSWORD:
		await database.allowUser(uid=m.from_user.id)
		await m.reply_text(
			text=f"**Login passed ✅,**\n  ⚡ Now you can you me!!",
			quote=True
		)
	else:
		await m.reply_text(
			text=f"**Login failed ❌,**\n  🛡️ Unfortunately you can't use me",
			quote=True
		)
	return

@mergeApp.on_message(filters.command(['stats']) & filters.private & filters.user(Config.OWNER))
async def stats_handler(c:Client, m:Message):
    currentTime = get_readable_time(time.time() - botStartTime)
    total, used, free = shutil.disk_usage('.')
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(psutil.net_io_counters().bytes_sent)
    recv = get_readable_file_size(psutil.net_io_counters().bytes_recv)
    cpuUsage = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    stats = f'<b>「 💠 BOT STATISTICS 」</b>\n' \
            f'<b></b>\n' \
            f'<b>⏳ Bot Uptime : {currentTime}</b>\n' \
            f'<b>💾 Total Disk Space : {total}</b>\n' \
            f'<b>📀 Total Used Space : {used}</b>\n' \
            f'<b>💿 Total Free Space : {free}</b>\n' \
            f'<b>🔺 Total Upload : {sent}</b>\n' \
            f'<b>🔻 Total Download : {recv}</b>\n' \
            f'<b>🖥 CPU : {cpuUsage}%</b>\n' \
            f'<b>⚙️ RAM : {memory}%</b>\n' \
            f'<b>💿 DISK : {disk}%</b>'
    await m.reply_text(stats,quote=True)

@mergeApp.on_message(filters.command(['broadcast']) & filters.private & filters.user(Config.OWNER))
async def broadcast_handler(c:Client, m:Message):
	msg = m.reply_to_message
	userList = await database.broadcast()
	len = userList.collection.count_documents({})
	for i in range(len):
		try:
			await msg.copy(chat_id=userList[i]['_id'])
		except FloodWait as e:
			await asyncio.sleep(e.x)
			await msg.copy(chat_id=userList[i]['_id'])
		except Exception:
			await database.deleteUser(userList[i]['_id'])
			pass
		print(f"Message sent to {userList[i]['name']} ")
		await asyncio.sleep(2)
	await m.reply_text(
		text="🤓 __Broadcast completed sucessfully__",
		quote=True
	)

@mergeApp.on_message(filters.command(['start']) & filters.private & ~filters.edited)
async def start_handler(c: Client, m: Message):
	await database.addUser(uid=m.from_user.id,fname=m.from_user.first_name, lname=m.from_user.last_name)
	if await database.allowedUser(uid=m.from_user.id) is False:
		res = await m.reply_text(
			text=f"Hi **{m.from_user.first_name}**\n\n 🛡️ Unfortunately you can't use me",
			quote=True
		)
		return
	res = await m.reply_text(
		text=f"Hi **{m.from_user.first_name}**\n\n ⚡ I am a MP3 Merger bot\n\n😎 I can merge Telegram files!, And upload it to telegram\n\n**Owner: @{Config.OWNER_USERNAME}** ",
		quote=True
	)


@mergeApp.on_message((filters.document | filters.audio) & filters.private & ~filters.edited)
async def Audio_handler(c: Client, m: Message):
	if await database.allowedUser(uid=m.from_user.id) is False:
		res = await m.reply_text(
			text=f"Hi **{m.from_user.first_name}**\n\n 🛡️ Unfortunately you can't use me ",
			quote=True
		)
		return
	media = m.audio or m.document
	if media.file_name is None:
		await m.reply_text('File Not Found')
		return
	if media.file_name.rsplit(sep='.')[-1].lower() in 'conf':
		await m.reply_text(
			text="**Config file found, Do you want to save it?**",
			reply_markup = InlineKeyboardMarkup(
				[
					[
						InlineKeyboardButton("✅ Yes", callback_data=f"rclone_save"),
						InlineKeyboardButton("❌ No", callback_data='rclone_discard')
					]
				]
			),
			quote=True
		)
		return
	if media.file_name.split(sep='.')[-1].lower() not in ['mp3']:
		await m.reply_text("This Format not Allowed!\nOnly send MP3", quote=True)
		return
	if queueDB.get(m.from_user.id, None) is None:
		formatDB.update({m.from_user.id: media.file_name.rsplit(".", 1)[-1].lower()})
	editable = await m.reply_text("Please Wait ...", quote=True)
	MessageText = "Okay,\nNow Send Me Next Audio or Press **Merge Now** Button!"
	if queueDB.get(m.from_user.id, None) is None:
		queueDB.update({m.from_user.id: []})
	if (len(queueDB.get(m.from_user.id)) >= 0) and (len(queueDB.get(m.from_user.id))<100 ):
		queueDB.get(m.from_user.id).append(m.message_id)
		if len(queueDB.get(m.from_user.id)) == 1:
			await editable.edit(
				'**Send me some more Audio to merge them into single file**',parse_mode='markdown'
			)
			return
		if queueDB.get(m.from_user.id, None) is None:
			formatDB.update({m.from_user.id: media.file_name.split(sep='.')[-1].lower()})
		if replyDB.get(m.from_user.id, None) is not None:
			await c.delete_messages(chat_id=m.chat.id, message_ids=replyDB.get(m.from_user.id))
		if len(queueDB.get(m.from_user.id)) == 100:
			MessageText = "Okay, Now Just Press **Merge Now** Button Plox!"
		markup = await MakeButtons(c, m, queueDB)
		reply_ = await m.reply_text(
			text=MessageText,
			reply_markup=InlineKeyboardMarkup(markup),
			quote=True
		)
		replyDB.update({m.from_user.id: reply_.message_id})
	elif len(queueDB.get(m.from_user.id)) > 100:
		markup = await MakeButtons(c,m,queueDB)
		await editable.text(
			"Max 50 Audio allowed",
			reply_markup=InlineKeyboardMarkup(markup)
		)



@mergeApp.on_message(filters.command(['help']) & filters.private & ~filters.edited)
async def help_msg(c: Client, m: Message):
	await m.reply_text(
		text='''**Follow These Steps:


1) Send two or more Your Audio Which you want to merge
2) After sending all files select merge options
3) Select the upload mode.
4) Select rename if you want to give custom file name else press default**''',
		quote=True,
		reply_markup=InlineKeyboardMarkup(
			[
				[
					InlineKeyboardButton("Close 🔐", callback_data="close")
				]
			]
		)
	)

@mergeApp.on_message( filters.command(['about']) & filters.private & ~filters.edited )
async def about_handler(c:Client,m:Message):
	await m.reply_text(
		text='''
	**\n\n ⚡ I am a MP3 Merger bot\n\n😎 I Can merge upto 50 MP3s Files into Single MP3, And upload it to Telegram.		''',
		quote=True,
		reply_markup=InlineKeyboardMarkup(
			[
				[
					InlineKeyboardButton("Owner", url="https://t.me/SherlockSr"),
                    InlineKeyboardButton("Repo", url="https://github.com/thedkm/MP3-MERGE-BOT")
				]

			]
		)
	)




@mergeApp.on_callback_query()
async def callback(c: Client, cb: CallbackQuery):

	if cb.data == 'merge':
		await cb.message.edit(
			text='Where do you want to upload?',
			reply_markup=InlineKeyboardMarkup(
				[
					[
						InlineKeyboardButton('📤 To Telegram', callback_data = 'to_telegram'),
						InlineKeyboardButton('🌫️ To Drive', callback_data = 'to_drive')
					]
				]
			)
		)

	elif cb.data == 'to_drive':
		try:
			urc = await database.getUserRcloneConfig(cb.from_user.id)
			await c.download_media(message=urc,file_name=f"userdata/{cb.from_user.id}/rclone.conf")
		except Exception as err:
			await cb.message.reply_text("Rclone not Found, Unable to upload to drive")
		if os.path.exists(f"userdata/{cb.from_user.id}/rclone.conf") is False:
			await cb.message.delete()
			await delete_all(root=f"downloads/{cb.from_user.id}/")
			queueDB.update({cb.from_user.id: []})
			formatDB.update({cb.from_user.id: None})
			return
		Config.upload_to_drive.update({f'{cb.from_user.id}':True})
		await cb.message.edit(
			text="Okay I'll upload to drive\nDo you want to rename?",
			reply_markup=InlineKeyboardMarkup(
				[
					[
						InlineKeyboardButton('👆 Default', callback_data='rename_NO'),
						InlineKeyboardButton('✍️ Rename', callback_data='rename_YES')
					]
				]
			)
		)
	elif cb.data == 'to_telegram':
		Config.upload_to_drive.update({f'{cb.from_user.id}':False})
		await cb.message.edit(
			text='How do yo want to upload file',
			reply_markup=InlineKeyboardMarkup(
				[
					[
						InlineKeyboardButton('🎧Audio', callback_data='Audio'),
						InlineKeyboardButton('📁 File', callback_data='document')
					]
				]
			)
		)
	elif cb.data == 'document':
		Config.upload_as_doc.update({f'{cb.from_user.id}':True})
		await cb.message.edit(
			text='Do you want to rename?',
			reply_markup=InlineKeyboardMarkup(
				[
					[
						InlineKeyboardButton('👆 Default', callback_data='rename_NO'),
						InlineKeyboardButton('✍️ Rename', callback_data='rename_YES')
					]
				]
			)
		)
	elif cb.data == 'Audio':
		Config.upload_as_doc.update({f'{cb.from_user.id}':False})
		await cb.message.edit(
			text='Do you want to rename?',
			reply_markup=InlineKeyboardMarkup(
				[
					[
						InlineKeyboardButton('👆 Default', callback_data='rename_NO'),
						InlineKeyboardButton('✍️ Rename', callback_data='rename_YES')
					]
				]
			)
		)

	elif cb.data.startswith('rclone_'):
		if 'save' in cb.data:
			fileId = cb.message.reply_to_message.document.file_id
			print(fileId)
			await c.download_media(
				message=cb.message.reply_to_message,
				file_name=f"./userdata/{cb.from_user.id}/rclone.conf"
			)
			await database.addUserRcloneConfig(cb, fileId)
		else:
			await cb.message.delete()

	elif cb.data.startswith('rename_'):
		if 'YES' in cb.data:
			await mergeNow(c,cb,f"./downloads/{str(cb.from_user.id)}/_merged.mp3", rename=True)
		if 'NO' in cb.data:
			await mergeNow(c,cb,new_file_name = f"./downloads/{str(cb.from_user.id)}/_merged.mp3", rename=False)

	elif cb.data == 'cancel':
		await delete_all(root=f"downloads/{cb.from_user.id}/")
		queueDB.update({cb.from_user.id: []})
		formatDB.update({cb.from_user.id: None})
		await cb.message.edit("Sucessfully Cancelled")
		await asyncio.sleep(5)
		await cb.message.delete(True)
		return

	elif cb.data == 'close':
		await cb.message.delete(True)

	elif cb.data.startswith('showFileName_'):
		m = await c.get_messages(chat_id=cb.message.chat.id,message_ids=int(cb.data.rsplit("_",1)[-1]))
		try:
			await cb.message.edit(
				text=f"File Name: {m.Audio.file_name}",
				reply_markup=InlineKeyboardMarkup(
					[
						[
							InlineKeyboardButton("Remove",callback_data=f"removeFile_{str(m.message_id)}"),
							InlineKeyboardButton("Back", callback_data="back")
						]
					]
				)
			)
		except:
			await cb.message.edit(
				text=f"File Name: {m.document.file_name}",
				reply_markup=InlineKeyboardMarkup(
					[
						[
							InlineKeyboardButton("Remove",callback_data=f"removeFile_{str(m.message_id)}"),
							InlineKeyboardButton("Back", callback_data="back")
						]
					]
				)
			)

	elif cb.data == 'back':
		await showQueue(c,cb)

	elif cb.data.startswith('removeFile_'):
		queueDB.get(cb.from_user.id).remove(int(cb.data.split("_", 1)[-1]))
		await showQueue(c,cb)

async def showQueue(c:Client, cb: CallbackQuery):
	try:
		markup = await MakeButtons(c,cb.message,queueDB)
		await cb.message.edit(
			text="Okay,\nNow Send Me Next Audio or Press **Merge Now** Button!",
			reply_markup=InlineKeyboardMarkup(markup)
		)
	except ValueError:
		await cb.message.edit('Send Some more Audio')


async def mergeNow(c:Client, cb:CallbackQuery,new_file_name: str, rename: bool):
	omess = cb.message.reply_to_message
	# print(omess.message_id)
	vid_list = list()
	await cb.message.edit('⭕ Processing...')
	duration = 0
	list_message_ids = queueDB.get(cb.from_user.id,None)
	list_message_ids.sort()
	input_ = f"./downloads/{cb.from_user.id}/input.txt"
	if list_message_ids is None:
		await cb.answer("Queue Empty",show_alert=True)
		await cb.message.delete(True)
		return
	if not os.path.exists(f'./downloads/{cb.from_user.id}/'):
		os.makedirs(f'./downloads/{cb.from_user.id}/')
	for i in (await c.get_messages(chat_id=cb.from_user.id,message_ids=list_message_ids)):
		media = i.audio or i.document
		try:
			await cb.message.edit(f'📥 Downloading...{media.file_name}')
			await asyncio.sleep(2)
		except MessageNotModified :
			queueDB.get(cb.from_user.id).remove(i.message_id)
			await cb.message.edit("❗ File Skipped!")
			await asyncio.sleep(3)
			continue
		file_dl_path = None
		try:
			c_time = time.time()
			file_dl_path = await c.download_media(
				message=i,
				file_name=f"./downloads/{cb.from_user.id}/{i.message_id}/",
				progress=progress_for_pyrogram,
				progress_args=(
					'🚀 Downloading...',
					cb.message,
					c_time
				)
			)
		except Exception as downloadErr:
			print(f"Failed to download Error: {downloadErr}")
			queueDB.get(cb.from_user.id).remove(i.message_id)
			await cb.message.edit("❗File Skipped!")
			await asyncio.sleep(3)
			continue
		metadata = extractMetadata(createParser(file_dl_path))
		try:
			if metadata.has("duration"):
				duration += metadata.get('duration').seconds
			vid_list.append(f"file '{file_dl_path}'")
		except:
			await delete_all(root=f'./downloads/{cb.from_user.id}')
			queueDB.update({cb.from_user.id: []})
			formatDB.update({cb.from_user.id: None})
			await cb.message.edit('⚠️ Audio is corrupted!!')
			return
	_cache = list()
	for i in range(len(vid_list)):
		if vid_list[i] not in _cache:
			_cache.append(vid_list[i])
	vid_list = _cache
	await cb.message.edit(f"🔀 Trying to merge Audio ...")
	with open(input_,'w') as _list:
		_list.write("\n".join(sorted(vid_list)))

	meta_data_path = await MetaData(
		filePath=file_dl_path,
		user_id=cb.from_user.id,

	)

	merged_Audio_path = await MergeAudio(
		input_file=input_,
        meta_data=meta_data_path,
		user_id=cb.from_user.id,
		message=cb.message,
		format_='mp3'
	)
	if merged_Audio_path is None:
		await cb.message.edit("❌ Failed to merge Audio !")
		await delete_all(root=f'./downloads/{cb.from_user.id}')
		queueDB.update({cb.from_user.id: []})
		formatDB.update({cb.from_user.id: None})
		return
	await cb.message.edit("✅ Sucessfully Merged Audio !")
	print(f"Audio merged for: {cb.from_user.first_name} ")
	await asyncio.sleep(3)
	file_size = os.path.getsize(merged_Audio_path)
	os.rename(merged_Audio_path,new_file_name)
	merged_Audio_path = new_file_name
	if Config.upload_to_drive[f'{cb.from_user.id}']:
		await rclone_driver(omess,cb,merged_Audio_path)
		await delete_all(root=f'./downloads/{cb.from_user.id}')
		queueDB.update({cb.from_user.id: []})
		formatDB.update({cb.from_user.id: None})
		return
	if file_size > 2044723200:
		await cb.message.edit("Audio is Larger than 2GB Can't Upload")
		await delete_all(root=f'./downloads/{cb.from_user.id}')
		queueDB.update({cb.from_user.id: []})
		formatDB.update({cb.from_user.id: None})
		return

	await cb.message.edit("🎧 Extracting Audio Data ...")
	duration = 0
	title = ""
	artist = " "
	try:
		metadata = extractMetadata(createParser(merged_Audio_path))
		if metadata.has("duration"):
			duration = metadata.get("duration").seconds
		if metadata.has("title"):
			title = metadata.get("title")
		if metadata.has("artist"):
			artist = metadata.get("artist")

	except:
		await delete_all(root=f'./downloads/{cb.from_user.id}')
		queueDB.update({cb.from_user.id: []})
		formatDB.update({cb.from_user.id: None})
		await cb.message.edit("⭕ Merged Audio is corrupted")
		return

	title = re.sub(r"\.*\s*-\s*[pP]art.*", "", title)

	final_file_name = title.replace(" ", "_")
	if rename:
		await cb.message.edit(
			f'Current filename (automatically detected): **{final_file_name}.mp3**\n\nSend me new file name without extension: ',
			parse_mode='markdown'
		)
		res: Message = await c.listen( cb.message.chat.id, timeout=300 )
		if res.text :
			ascii_ = e = ''.join([i if (i in string.digits or i in string.ascii_letters or i == " ") else " " for i in res.text])
			final_file_name = f"./downloads/{str(cb.from_user.id)}/{ascii_.replace(' ', '_')}.mp3"
			# await mergeNow(c,cb,new_file_name, rename=True)
			os.rename(merged_Audio_path,final_file_name)
	else:
		final_file_name = f"./downloads/{str(cb.from_user.id)}/{final_file_name}.mp3"
		# await mergeNow(c,cb,new_file_name = f"./downloads/{str(cb.from_user.id)}/{str(title)}.mp3", rename=False)
		os.rename(merged_Audio_path,final_file_name)

	await cb.message.edit(f"🔄 Renamed Merged Audio to\n **{final_file_name.rsplit('/',1)[-1]}**")
	await asyncio.sleep(1)

	await uploadAudio(
		c=c,
		cb=cb,
		merged_Audio_path=final_file_name,
		title=title,
		artist=artist,
		duration=duration,
		file_size=os.path.getsize(final_file_name),
		upload_mode=Config.upload_as_doc[f'{cb.from_user.id}']
	)
	await cb.message.delete(True)
	await delete_all(root=f'./downloads/{cb.from_user.id}')
	queueDB.update({cb.from_user.id: []})
	formatDB.update({cb.from_user.id: None})
	return

async def delete_all(root):
	try:
		shutil.rmtree(root)
	except Exception as e:
		print(e)

async def MakeButtons(bot: Client, m: Message, db: dict):
	markup = []
	for i in (await bot.get_messages(chat_id=m.chat.id, message_ids=db.get(m.chat.id))):
		media = i.audio or i.document or None
		if media is None:
			continue
		else:
			markup.append([InlineKeyboardButton(f"{media.file_name}", callback_data=f"showFileName_{str(i.message_id)}")])
	markup.append([InlineKeyboardButton("🔗 Merge Now", callback_data="merge")])
	markup.append([InlineKeyboardButton("💥 Clear Files", callback_data="cancel")])
	return markup


@mergeApp.on_message(filters.command(['restart']) & filters.private & ~filters.edited & filters.user(Config.OWNER))
async def restart_bot(c: Client, m: Message):

	reply_msg = await m.reply_text(
		text="Restarting...",
		quote=True
	)

	current_process = psutil.Process()
	for child in current_process.children(recursive=True):
		child.kill()

	# Remove all downloads
	await delete_all(root=f'./downloads')

	with open('.restartmsg', 'w') as f:
		f.truncate(0)
		f.write(f"{reply_msg.chat.id}\n{reply_msg.message_id}")

	os.execl(executable, executable, "bot.py")

mergeApp.start()

if os.path.exists('.restartmsg'):
	file_data = []
	with open('.restartmsg', 'r') as f:
		file_data = f.readlines()
	if len(file_data) >= 2:
		chat_id = int(file_data[0].strip())
		msg_id = int(file_data[1].strip())
		_ = mergeApp.send_message(
				chat_id=chat_id,
				reply_to_message_id=msg_id,
				text="Successfully Restarted"
				)
	os.remove('.restartmsg')

idle()

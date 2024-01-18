import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import random
import string
import requests

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=";", intents=intents)

download_path = "DOWNLOAD/PATH/LOCATION/" # CHANGE ME
file_id_map = {}


@bot.event
async def on_ready():
    await bot.tree.sync()
    await bot.change_presence(status=discord.Status.online)
    print(f"We have logged in as {bot.user}")


def generate_unique_id(length=7):
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


def add_file(unique_id, file_path):
    file_id_map[unique_id] = file_path


def generate_download_link(file_path):
    unique_id = generate_unique_id()
    success = add_file_to_flask_app(unique_id, file_path)
    if success:
        server_url = "http://YOUR.DOMAIN/" # CHANGE ME
        return f"{server_url}{unique_id}"
    else:
        return None


def add_file_to_flask_app(unique_id, file_path):
    flask_url = "http://localhost:5000/add_mapping"
    data = {"unique_id": unique_id, "file_path": file_path}
    response = requests.post(flask_url, json=data)
    return response.status_code == 200


async def delete_file_after_delay(unique_id, delay):
    await asyncio.sleep(delay)
    flask_url = f"http://localhost:5000/delete_file/{unique_id}"
    response = requests.post(flask_url)


def download_video(url, format="mp4", quality="highest"):
    ydl_opts = {
        "outtmpl": download_path + "%(title)s.%(ext)s",
        "postprocessors": [],
    }

    if format == "mp4":
        # Select video quality
        ydl_opts["format"] = (
            "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
            if quality == "highest"
            else "worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst[ext=mp4]/worst"
        )
    elif format == "mp3":
        # Select audio quality
        ydl_opts["format"] = (
            "bestaudio/best" if quality == "highest" else "worstaudio/worst"
        )
        ydl_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192" if quality == "highest" else "128",
            }
        ]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get("title", None)
            file_extension = "mp3" if format == "mp3" else "mp4"
            return f"{download_path}{video_title}.{file_extension}", video_title
    except Exception as e:
        print(f"Error downloading video: {e}")
        return None, None


@bot.tree.command(name="download", description="Download a YouTube video")
@app_commands.describe(
    url="URL of the YouTube video", format="Video format", quality="Video/Audio quality"
)
@app_commands.choices(
    format=[
        discord.app_commands.Choice(name="mp4", value="mp4"),
        discord.app_commands.Choice(name="mp3", value="mp3"),
    ],
    quality=[
        discord.app_commands.Choice(name="highest", value="highest"),
        discord.app_commands.Choice(name="lowest", value="lowest"),
    ],
)
async def slash_command(
    interaction: discord.Interaction,
    url: str,
    format: str = "mp4",
    quality: str = "highest",
):
    try:
        await interaction.response.send_message(
            f"Downloading video from {url}...", ephemeral=True
        )
        file_path, video_title = download_video(url, format, quality)
        if file_path and video_title:
            download_link = generate_download_link(file_path)
            await interaction.edit_original_response(
                content=f"Download link (available for 10 minutes): {download_link}"
            )
            unique_id = download_link.split("/")[-1]
            asyncio.create_task(delete_file_after_delay(unique_id, 600))
        else:
            await interaction.edit_original_response(
                content="Failed to download video."
            )
    except Exception as e:
        await interaction.edit_original_response(content=f"An error occurred: {e}")


bot.run("BOT_TOKEN") # CHANGE ME

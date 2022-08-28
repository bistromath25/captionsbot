import aiohttp
import discord
import mimetypes
import requests
import textwrap
from discord.ext import commands
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from random import randint

DISCORD_TOKEN = "discord bot token"
SUPPORTED_MIMETYPES = ["image/jpeg", "image/png", "image/webp"]
FONT_FILE = "impact.ttf"
SPOIL_REDDIT_NSFW = True

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="+", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} connected to Discord!")


@bot.command(name="caption", aliases=["c"], brief="Add a caption to an image", help="""Add a caption to an attached image. Usage:
             
+caption <caption_text> <image_web_url | attatched image>

Supported image formats: PNG, JPEG, WebP. Caption text must be wrapped in double-quotes.
""")

async def caption(ctx, caption_text=None, image_web_url=None):
    if not caption_text:
        await ctx.message.reply("Caption text not found, please try again.")
        return
    
    if ctx.message.attachments:
        image_url = ctx.message.attachments[0].url
        if mimetypes.guess_type(image_url)[0] not in SUPPORTED_MIMETYPES:
            await ctx.message.reply("Image format not supported, please upload a PNG, JPEG, or WebP image instead.")
            return
    elif image_web_url:
        image_url = image_web_url
        if mimetypes.guess_type(image_url)[0] not in SUPPORTED_MIMETYPES:
            await ctx.message.reply("Image format not supported, please link a PNG, JPEG, or WebP image instead.")
            return
    else:
        await ctx.message.reply("Image not found, please try again.")
        return

    response = requests.get(image_url)
    image_filename = ctx.message.attachments[0].filename if ctx.message.attachments else image_url.split("/")[-1]
    final_image = caption_image(BytesIO(response.content), caption_text)
    await ctx.message.reply(file=discord.File(BytesIO(final_image), filename=f"captioned-{image_filename}"))

  
@bot.command(name="reddit",  aliases=["r"], brief="Fetches a post from Reddit", help="""Fetches a random post from Reddit. Usage:

+reddit <subreddit>

If the subreddit does not exist, r/memes will be used.
""")

async def reddit(ctx, subreddit="memes"):
    async with aiohttp.ClientSession() as cs:
        try:
            async with cs.get(f"https://www.reddit.com/r/{subreddit}/new.json?sort=hot") as req:
                res = await req.json()
        except:
            async with cs.get("https://www.reddit.com/r/memes/new.json?sort=hot") as req:
                res = await req.json()
        
        data = res['data']['children'][randint(0, 25)]['data']
        while mimetypes.guess_type(data['url'])[0] not in SUPPORTED_MIMETYPES:
            data = res['data']['children'][randint(0, 25)]['data']

        image_url = data['url']
        response = requests.get(image_url)
        image_filename = image_url.split("/")[-1]
        final_image = caption_image(BytesIO(response.content))
        if SPOIL_REDDIT_NSFW and data['over_18']:
            image_filename = f"SPOILER_{image_filename}"
        await ctx.message.reply(file=discord.File(BytesIO(final_image), filename=image_filename))


def caption_image(image_file, caption=None, font_file=FONT_FILE):
    img = Image.open(image_file)
    
    if caption:
        draw = ImageDraw.Draw(img)

        font_size = int(img.width/16)
        font = ImageFont.truetype(font_file, font_size)

        caption = textwrap.fill(text=caption, width=img.width/(font_size/2))
        caption_w, caption_h = draw.textsize(caption, font=font)
    
        draw.text(((img.width-caption_w)/2, (img.height-caption_h)/8), # position
                  caption, # text
                  (255,255,255), # color
                  font=font, # font
                  stroke_width=2, # text outline width
                  stroke_fill=(0,0,0)) # text outline color

    with BytesIO() as img_bytes:
        img.save(img_bytes, format=img.format)
        content = img_bytes.getvalue()
    
    return content

bot.run(DISCORD_TOKEN)
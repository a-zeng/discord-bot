import requests
import time
import datetime
import discord
import os
from dotenv import load_dotenv
from discord import File, User
from discord.ext import commands
import asyncio
from bs4 import BeautifulSoup

# Define list of URLs and other info (URL, stock, still_in_stock, product name, last checked)
url_list = [#["https://www.microcenter.com/product/510223/asus-b450-i-rog-strix-gaming-amd-am4-mitx-motherboard?storeid=121", '', 0, "ASUS B450-I", 0],
            #["https://www.microcenter.com/product/510838/gigabyte-b450i-aorus-pro-wifi-amd-am4-mini-itx-motherboard?storeid=121", '', 0, "Gigabyte B450I", 0]
            ["https://www.microcenter.com/search/search_results.aspx?Ntt=GeForce+RTX+3060+Ti&searchButton=search&storeid=121", '', 0, "RTX 3060 Ti", 0],
            ["https://www.microcenter.com/search/search_results.aspx?Ntt=rtx+3070+graphics+card&searchButton=search&storeid=121", '', 0, "RTX 3070", 0]]
polling_freq = 300                                                              # in seconds

# Setting up environment
load_dotenv()

# Discord bot set up
TOKEN = os.getenv('DISCORD_TOKEN')
# SERVER = 'Doodooland'
bot = commands.Bot(command_prefix='dd.', description="In fact a piece of doodoo")
vc = 1

# Scrapes the stock of the URL from the Microcenter website and returns the stock
def scrape_stock(url):
    print("Scraping " + url + "...")
    response = requests.get(url)
    soup_ = BeautifulSoup(response.content, 'html.parser')
    tablist = soup_.find('div', class_="my-store-only")
    stock_string = tablist.find('li').text
    print(stock_string)
    store_stock = str(stock_string.split(" ")[0])
    return store_stock

# Event that triggers once the bot is ready
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name='with its own doodoo'))
    print('--------------------\nLogged in as ' + bot.user.name)
    print('ID: ' + str(bot.user.id) + '\n' + str(datetime.datetime.now()) + '\n--------------------')
    global vc

    try:
        doohole_channel = bot.get_channel(808025131690754089)
        print('Connected to #' + str(doohole_channel))
        vc = await doohole_channel.connect()
        print('Entered the doohole')
    except Exception as e:
        print(e)

# Command that plays a soundbite when someone joins the voice channel
@bot.event
async def on_voice_state_update(member, before, after):
    # print("Member: " + str(member))
    # print("Before: " + str(before))
    # print("After: " + str(after))
    global vc

    if member != "Doodoo Bot#1143" and before.channel is None and after.channel.name == "Doodoo Bot's Doohole":
        print("Someone joined my doohole!")
        fart = vc.play(discord.FFmpegPCMAudio("fart.mp3"))
        # while vc.is_playing():
        # await asyncio.sleep(0.1)
        await asyncio.sleep(0.75)
        print("Done farting")
        await member.move_to(None)

    if member != "Doodoo Bot#1143" and after.channel is None: # and before.channel.name == "Doodoo Bot's Doohole":
        vc.stop()

# Command that provides last updated information in url_list to user
@bot.command()
async def stock(ctx):
    print("Returning stock info from url_list")
    for i in range(len(url_list)):
        url = url_list[i][0]
        stock_ = url_list[i][1]
        name = url_list[i][3]
        formatted_time = url_list[i][4].strftime('%b %d at %H:%M')
        embed = discord.Embed(title=name+' --- '+stock_,
                              url=url,
                              description='Last checked '+formatted_time
                              )
        await ctx.send(embed=embed)

# Command that replies with bonk sound clip
@bot.command()
async def bonk(ctx):
    # await ctx.send("bonk")
    await ctx.send(file=File('bonk.wav'))

# Command that sends out an annoying reminder every minute until dealt with
@bot.command()
@commands.is_owner()
async def annoy_reminder(ctx, user: User, reminder: str):
    counter = 0
    print("Reminding user: " + user.name)
    while True:
        async for message in user.history(limit=5):
            if message.author != bot.user:
                counter += 1
        if counter >= 3:
            print("User: " + user.name + " has responded to the reminders")
            await user.send("Quota satisfied, committing sepuku")
            await user.send(file=File('bonk.wav'))
            return

        await user.send("Oi remember to " + reminder + "!\n" +
                        "This will repeat every minute until I detect three or more messages from you!\n"
                        "(I will check every minute)")

        await asyncio.sleep(60)

# Command that changes the polling frequency
@bot.command()
@commands.is_owner()
async def change_polling_freq(ctx, new_freq: int):
    global polling_freq
    polling_freq = new_freq
    print("Changed polling_freq to " + str(polling_freq) + " seconds")
    await ctx.send("Polling frequency set to " + str(polling_freq) + " seconds")

# Looping event that constantly fetches stock
async def fetch_stock():
    await bot.wait_until_ready()
    global url_list, channel_computer_parts
    try:
        channel_computer_parts = bot.get_channel(717484895714410517)
        print('Connecting to #' + str(channel_computer_parts))
    except Exception as e:
        print(e)

    while not bot.is_closed():
        try:
            print("Fetching HTML...")

            for i in range(len(url_list)):                                      # Iterate through URLs in url_list
                url = url_list[i][0]
                stock = url_list[i][1] = scrape_stock(url)                      # Set the stock to the value scraped
                still_in_stock = url_list[i][2]
                name = url_list[i][3]
                last_checked = url_list[i][4] = datetime.datetime.now()
                print(str(last_checked) + " - Fetched " + name + ": " + stock)

                if stock != "0":                                         # If in stock
                    if still_in_stock == 0:                                     # If just in stock
                        await channel_computer_parts.send(name + " is in stock at MicroCenter! - " + stock + "\n" + url)
                        url_list[i][2] = 1
                else:                                                           # If sold out
                    # await channel_computer_parts.send(name + " is NOT in stock at MicroCenter! \n" + url)
                    if still_in_stock == 1:
                        await channel_computer_parts.send(name + " is NO LONGER in stock at MicroCenter! - " + stock + "\n" + url)
                        url_list[i][2] = 0

            print(url_list)                                                     # Print url_list for telemetry

            await asyncio.sleep(polling_freq)
        except Exception as e:
            print(e)
            await asyncio.sleep(polling_freq)

bot.loop.create_task(fetch_stock())
bot.run(TOKEN)



import requests
import time
import datetime
import discord
import os
import csv
from dotenv import load_dotenv
from discord import File, User
from discord.ext import commands
import asyncio
from bs4 import BeautifulSoup
import random


# Add items to item list from CSV
item_list = []


# Define list of URLs and other info (URL, stock, still_in_stock, product name, last checked, vendor)
class CheckItem:

    def __init__(self, search, product_name, vendor, freq):
        self.search = search
        self.url = "a"
        self.name = product_name
        self.vendor = vendor
        self.stock = "0"
        self.in_stock = False
        self.last_checked = datetime.datetime.now()
        self.polling_frequency = freq
        self.use_sku = False

        if vendor == "BestBuy":
            try:
                int(self.search)
                self.use_sku = True
            except ValueError:
                self.url = search
        else:
            self.url = search

    def update_last_checked(self):
        self.last_checked = datetime.datetime.now()

    def print_data(self):
        print(" " + str(self.last_checked) + " - Fetched " + self.name + " from " + self.vendor + ": " + self.stock)

    def update_stock(self, n):
        self.stock = n

    # Scrapes the stock of the URL from the Microcenter website and returns the stock
    def scrape_mc(self):
        print("Scraping " + self.search + "...")
        response = requests.get(self.search)
        soup_ = BeautifulSoup(response.content, 'html.parser')
        tablist = soup_.find('div', class_="my-store-only")
        stock_string = tablist.find('li').text
        store_stock = str(stock_string.split(" ")[0])
        return store_stock

    # Scrapes the stock of the URL from the Best Buy website and returns the stock
    def scrape_bb(self):
        print("Scraping " + self.search + "...")
        return str(0)

    # Scrapes the stock of SKU using the Best Buy API and returns the stock
    def scrape_bb_api(self):
        print("Scraping SKU: " + self.search + "...")
        api_url = "https://api.bestbuy.com/v1/products(sku=" + self.search + ")?apiKey=" + BB_API_KEY + \
                  "&sort=url.asc&show=name,onlineAvailability,url&format=json"
        try:
            response = requests.get(api_url)
            query_result = response.json()
            for product in query_result["products"]:
                self.name = "Best Buy - " + product['name']
                self.url = product['url']
                if product['onlineAvailability']:
                    return "In Stock"

        except Exception as err:
            print(f'Other error occurred: {err}')

        return str(0)

    # Determines which scraping method to use and prints data
    def scrape_stock(self):
        if self.vendor == "MicroCenter":
            self.stock = self.scrape_mc()
        elif self.vendor == "BestBuy":
            if self.use_sku:
                self.stock = self.scrape_bb_api()
            else:
                self.stock = self.scrape_bb()

        self.print_data()
        self.update_last_checked()
        return True


# Refreshes the database
def refresh_database():
    print("Pulling changes to database .csv files")
    with open('database/item_list.csv', 'r') as item_file:
        reader = csv.reader(item_file, delimiter=",")
        for row in reader:
            item_list.append(CheckItem(row[0], row[1], row[2], int(row[3])))


refresh_database()
fart_vc = [["Doodoo Bot's Doohole", 808025131690754089],
           ["Wastierlands", 815646531309797468]]
vc = 1

farts = [["fart-extra.mp3", 15],
         ["vv-wet-fart.mp3", 5],
         ["nuclear-fart.mp3", 1],
         ["bonk.wav", 3],
         ["stinky.mp3", 8],
         ["awaken-pillar-men.mp3", 0.1]]

users_in_channel = []

farts_t = list(map(list, zip(*farts)))      # Transposes farts
fvc_n = 1
after_hours_polling_freq = 600  # in seconds
vc_refresh_freq = 24    # in hours

# Setting up environment
load_dotenv()

# Discord bot set up
TOKEN = os.getenv('DISCORD_TOKEN')
BB_API_KEY = os.getenv('BEST_BUY_API_KEY')
bot = commands.Bot(command_prefix='dd.', description="In fact a piece of doodoo")


# Event that triggers once the bot is ready
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name='with its own doodoo'))
    print('--------------------\nLogged in as ' + bot.user.name)
    print('ID: ' + str(bot.user.id) + '\n' + str(datetime.datetime.now()) + '\n--------------------')
    global vc

    try:
        doohole_channel = bot.get_channel(fart_vc[fvc_n][1])
        print('Connected to #' + str(doohole_channel))
        vc = await doohole_channel.connect(reconnect=True)
        print('Entered the doohole')
    except Exception as e:
        print(e)


# Command that plays a soundbite when someone joins the voice channel
@bot.event
async def on_voice_state_update(member, before, after):
    await bot.wait_until_ready()
    global vc, users_in_channel
    if member.bot:
        return None  # End command if the member is a bot

    try:
        if after.channel.name == fart_vc[fvc_n][0]:
            print("-------------------- Relevant voice activity on " + str(datetime.datetime.now().strftime('%b %d at %H:%M:%S')) + " --------------------")
            print("Users in channel: " + str(users_in_channel) + " | " + str(member) + " joined my doohole!")
            users_in_channel.append(str(member))

            # Choose the fart and play it
            chosen_fart = random.choices(farts_t[0], farts_t[1], k=1)[0]
            print("Playing " + str(chosen_fart))
            await asyncio.sleep(0.2)
            sound_loc = "sounds" + os.sep + chosen_fart
            fart = vc.play(discord.FFmpegPCMAudio(sound_loc))

            # While sound is playing and the user is still in the channel
            while vc.is_playing():
                await asyncio.sleep(0.1)
                for usr in users_in_channel:
                    if usr == str(member): break
                if not users_in_channel:
                    print("No users in channel, stopping music")
                    vc.stop()
                    return

            for usr in users_in_channel:
                if usr == str(member):
                    print("Attempting to eject " + str(member))
                    await member.move_to(None)

    except Exception as e:
        pass
        # print("  ERROR - " + str(e))

    users_in_channel = [usr for usr in users_in_channel if usr != str(member)] if after.channel is None else []


@bot.command(help='Changes the doohole voice channel')
@commands.is_owner()
async def doohole(ctx, *args):
    global vc, fvc_n
    print("Arguments for dd.doohole: " + str(args))
    if len(args) < 1:
        embed = discord.Embed(title="Available Dooholes to Enter:",
                              description="Add the number as an argument to this command")
        inc = 0
        for fvc in fart_vc:
            embed.add_field(name=inc, value=fvc[0])
            inc += 1
        await ctx.send(embed=embed)
    else:
        try:
            fvc_n = int(args[0])
            await ctx.send("Swapping to " + fart_vc[fvc_n][0])
            print("Entering " + fart_vc[fvc_n][0])
            await vc.disconnect()
            vc = await bot.get_channel(fart_vc[fvc_n][1]).connect(reconnect=True)
            print("Successfully entered")
            print("fvc_n: " + str(fvc_n))

        except Exception as e:
            await ctx.send("Encountered an error while connecting")
            print(e)


@bot.command(help='Chances of getting a certain fart when joining its lair')
async def fartchance(ctx):
    embed = discord.Embed(title="Fart Chances:",
                          description="Percent chance of a specific fart noise occurring")
    f_sum = sum(farts_t[1])
    for fart in farts:
        chance = str(round(fart[1] / f_sum * 100, 2)) + "%"
        embed.add_field(name=fart[0], value=chance)
    await ctx.send(embed=embed)


# Command that provides last updated information in url_list to user
@bot.command()
async def stock(ctx):
    print("Returning stock info from url_list")
    embed = discord.Embed(title="Current Stock",
                          description='From the item list',
                          color=0x28a45a)
    for item in item_list:
        embed.add_field(name=item.name + " --- " + item.stock + " in stock  |  Last checked " + str(item.last_checked.strftime('%b %d at %H:%M:%S')),
                        value=item.url,
                        inline=False)
    await ctx.send(embed=embed)


# Command that replies with bonk sound clip
@bot.command()
async def bonk(ctx):
    # await ctx.send("bonk")
    await ctx.send(file=File('sounds/bonk.wav'))


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
    global after_hours_polling_freq
    after_hours_polling_freq = new_freq
    print("Changed polling_freq to " + str(after_hours_polling_freq) + " seconds")
    await ctx.send("Polling frequency set to " + str(after_hours_polling_freq) + " seconds")


# Command that refreshes the running memory using data from the bot's database
@bot.command()
@commands.is_owner()
async def refresh_database(ctx):
    refresh_database()
    await ctx.send("Refreshed the database")


# Looping event that constantly fetches stock
async def fetch_stock(item):
    await bot.wait_until_ready()
    global item_list, vc
    try:
        channel_computer_parts = bot.get_channel(717484895714410517)
        print('Connecting to #' + str(channel_computer_parts))
    except Exception as e:
        print(e)

    while not bot.is_closed():
        try:
            print("-------------------- Fetching HTML... --------------------")
            item.scrape_stock()

            if not item.in_stock and item.stock != "0":   # If item was not in stock and some stock reported
                await channel_computer_parts.send("<@&827997603869884487> " +
                    item.name + " is in stock at " + item.vendor + "! - " + item.stock + "\n" + item.url)
                item.in_stock = True
            elif item.in_stock and item.stock == "0":     # If item was in stock and no more stock reported
                await channel_computer_parts.send("<@&827997603869884487> " +
                    item.name + " is NO LONGER in stock at " + item.vendor + "! - " + item.stock + "\n" + item.url)
                item.in_stock = False

        except Exception as e:
            print(e)

        current_hour = int(datetime.datetime.now().strftime('%H'))
        current_day = int(datetime.datetime.now().strftime('%u'))

        # If between 8 AM and 4 PM and not on the weekend
        if 8 <= current_hour <= 16 and current_day != 6 and current_day != 7:
            await asyncio.sleep(item.polling_frequency)
        else:
            await asyncio.sleep(after_hours_polling_freq)


# Refreshes the bot's connection to the voice channel it currently resides in
async def refresh_connection():
    global vc, fart_vc, fvc_n, vc_refresh_freq
    await asyncio.sleep(10)
    await bot.wait_until_ready()
    await vc.disconnect()
    vc = await bot.get_channel(fart_vc[fvc_n][1]).connect(reconnect=True)
    print("Refreshing connection to " + fart_vc[fvc_n][0] + ", waiting " + str(vc_refresh_freq) + " hours")
    await asyncio.sleep(vc_refresh_freq * 3600)


# Run the bot and create the async tasks
for i in item_list:
    bot.loop.create_task(fetch_stock(i))
bot.loop.create_task(refresh_connection())
bot.run(TOKEN)

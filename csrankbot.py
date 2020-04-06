
#need to install these packages
#pip install pillow
#pip install selenium
#pip install discord.py
#also requires chromedriver https://chromedriver.chromium.org/

import discord
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from PIL import Image
from io import BytesIO
import sqlite3

#run createdb.py once to create the database
def createConn():
    conn = sqlite3.connect("users.db")
    return(conn)


async def getImg(uid, channel):
    print('Fetching ranks for '+uid)
    options = webdriver.ChromeOptions()
    options.headless = True
    #specifying a user agent allows the webdriver to run in headless without the website blocking it from entering
    #headless doesn't seem to work on raspberry pi in my testing and need to run it with desktop active
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36")
    #set path to chromedriver, can be absolute or relative
    CHROMEDRIVER_PATH = "/home/pi/csrankbot/chromedriver"
    driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, chrome_options=options)
    driver.get("https://csgostats.gg/player/"+uid+"#/live")
    driver.set_window_size(1920, 1080)
    try:
        #sleep for a while just to make sure page is loaded can be altered or removed if wanted
        time.sleep(4)
        element = driver.find_element_by_id('live-match-section')
        location = element.location
        size = element.size
        png = driver.get_screenshot_as_png()
        driver.quit()

        im = Image.open(BytesIO(png))

        #values 120, 12, 320, and 24 may need to be changed depending on how the site renders
        #seems to be different depending on certain factors
        left = location['x'] + 120
        top = location['y'] + 12
        right = location['x'] + size['width'] - 320
        bottom = location['y'] + size['height'] - 24


        im = im.crop((left, top, right, bottom))
        #add a filepath here can be relative or absolute
        fp = "/home/pi/csrankbot/ranks.png"
        im.save(fp)
        #i assume this works with absolute path rather than relative but haven't tested it
        #but i set it to an absolute path here
        await channel.send(file=discord.File(fp))
        return
    except NoSuchElementException:
        await channel.send("Could not fetch ranks. This is likely due to an invalid steamID64 being set. You can set your steamID64 with the .setid command.")
        return


class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        print('Message from {0.author}: {0.content}'.format(message))


        #.setid command
        if message.content.lower().startswith(".setid"):
            args = message.content.split()
            if(len(args) >= 2):
                #check user's ID exists
                conn = createConn()
                c = conn.cursor()
                c.execute('SELECT * FROM users WHERE discordID = "%s"' % message.author)
                result = c.fetchone()
                if result:
                    #alter existing entry in db
                    c.execute('UPDATE users SET steamID = "%s" WHERE discordID = "%s";' % (args[1], message.author))
                    await message.channel.send("Your steamID64 has been changed from \"%s\" to \"%s\"" % (result[1], args[1]))
                else:
                    #add entry to db
                    c.execute('INSERT INTO users (discordID,steamID) VALUES ("%s","%s");' % (message.author, args[1]))
                    await message.channel.send("Your steamID64 has been set to \"%s\"" % args[1])

                conn.commit()
                conn.close()
            else:
                await message.channel.send("Please set an ID")

        #.ranks command
        if message.content.lower() == ".ranks":
            conn = createConn()
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE discordID = "%s"' % message.author)
            result = c.fetchone()
            conn.close()
            if result:
                await message.channel.send("Fetching...")
                await getImg(result[1], message.channel)
            else:
                await message.channel.send("Your steamID64 is not set! Please set it using the .setid command.")


client = MyClient()

#set discord bot token here
MY_TOKEN = ""

client.run(MY_TOKEN)


import discord
import os
import requests
import pdb
import easyocr
import cv2
import matplotlib.pyplot as plt
import re
import shutil
from PIL import Image
imagePath = "C:\\Users\\Crang\\OneDrive\\ClubRepoV3\\Desktop\\Machine Learning projects\\Los Altos Hacks\\pictures"
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.attachments:
        doxable = None
        if isinstance(message.channel, discord.TextChannel):
            for attachment in message.attachments:
                #pdb.set_trace()
                if attachment.filename.endswith(('.png', '.jpg', '.jpeg')):
                        #pdb.set_trace()
                        response = requests.get(attachment.url)
                        filePath = os.path.join(imagePath, attachment.filename)
                        with open(filePath, 'wb') as file:
                            file.write(response.content)
                        doxable = detectDox(filePath)
                        if(doxable[0]):
                            #print(doxable)
                            await message.delete()
                            textmsg = f"Sensitive information was detected in your media.\n\nWhat would you like to do?\n**1) Blur each element one at a time\n2) Blur all\n3) Continue to post the image.**"
                            #pdb.set_trace()
                            newPath, edges, width = saveHighlight(filePath, doxable[1])
                            user = await client.fetch_user(message.author.id)
                            file = discord.File(newPath)
                            await user.send(textmsg, file=file)

                            def checkResponse(m):
                                 return m.author == user and isinstance(m.channel, discord.DMChannel)
                            
                            responseMessage = await client.wait_for('message', check=checkResponse)

                            responseContent = responseMessage.content
                            outPath = os.path.join(os.path.dirname(imagePath), "Altered Images", attachment.filename)
                            tempPath = os.path.join(os.path.dirname(imagePath), "Temp", attachment.filename)
                            shutil.copyfile(os.path.join(imagePath, attachment.filename), outPath)
                            shutil.copyfile(outPath, tempPath)
                            channel = client.get_channel(message.channel.id)
                            if responseContent == '1':
                                for detected in edges:
                                    image = blur(detected, outPath)
                                    image.save(tempPath, fmt='%d')
                                    tempfile = discord.File(tempPath)
                                    await user.send("Blur this?", file=tempfile)
                                    msg = await client.wait_for('message', check=checkResponse)
                                    content = msg.content
                                    content = content.lower()
                                    if 'y' in content:
                                        shutil.move(tempPath, outPath, copy_function=shutil.copy2)
                                outfile = discord.File(outPath)
                                await user.send("Final Image", file=outfile)
                                outfile = discord.File(outPath)
                                await channel.send(f'Image sent by <@{message.author.id}> | Verified by SensitiveRemover.', file=outfile)
                            elif responseContent == '2':
                                for detected in edges:
                                    image = blur(detected, outPath)
                                    image.save(outPath, fmt='%d')
                                await user.send("Blurred Image:", file=discord.File(outPath))
                                file = discord.File(outPath)
                                await channel.send(f'Image sent by <@{message.author.id}> | Verified by SensitiveRemover.', file=file)
                            elif responseContent == '3':
                                file = discord.File(outPath)
                                await channel.send(f'Image sent by <@{message.author.id}> | Verified by SensitiveRemover.', file=file)
                            else:
                                await user.send("ok buddy ur not slick")
                            os.remove(outPath)
                            os.remove(newPath)
                            break



def detectDox(image):
    reader = easyocr.Reader(['en'])
    result = reader.readtext(image, paragraph=True)
    for detected in result:
         if isSensitive(detected[1])[0]:
            return (True, result)
    return (False, result)

def saveHighlight(image, result):
    newPath = os.path.join(os.path.dirname(os.path.dirname(image)), "Filtered Images", os.path.basename(image))
    imageSize = (Image.open(image)).size
    widthRect = int(((imageSize[0] + imageSize[1]) * 0.00210526316) + 0.5)
    newFileCV2 = cv2.imread(image)
    listEdges = []
    for detected in result:
        text = detected[1]
        if isSensitive(text)[0]:
            greenRectangle(detected, newFileCV2, widthRect)
            listEdges.append(detected)
    image = cv2.cvtColor(newFileCV2, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(image.astype('uint8'))
    image.save(newPath, fmt='%d')
    return (newPath, listEdges, widthRect)

def greenRectangle(detectTup, image, width):
     startPoint = tuple(detectTup[0][0])
     endPoint = tuple(detectTup[0][2])
     cv2.rectangle(image, startPoint, endPoint, (0, 255, 0), width)

def blur(points, img):
    imageCV2 = cv2.imread(img)
    imageCV2 = cv2.cvtColor(imageCV2, cv2.COLOR_BGR2RGB)
    startPoint = points[0][0]
    endPoint = points[0][2]
    roi = imageCV2[startPoint[1]:endPoint[1], startPoint[0]:endPoint[0]]
    blur = cv2.GaussianBlur(roi, (171, 171), 0)
    imageCV2[startPoint[1]:endPoint[1], startPoint[0]:endPoint[0]] = blur
    image = Image.fromarray(imageCV2.astype('uint8'))
    return image

def isSensitive(text):
     # street name?
     unModtext = text
     text = text.lower()
     if re.search('\\w*\\s?rd', text) or re.search('\\w*\\s?st', text) or re.search('\\w*\\s?ave', text) or re.search('\\w*\\s?av', text) or re.search('\\w*\\s?ct', text):
          return (True, unModtext)
     #dates
     if re.search('\\d+/\\d+/\\d{2,4}', text):
          return (True, unModtext)
     # phone numbers
     if re.search('\\d?.{3,5}-?\\d{3}-?\\d{4}', text):
          return (True, unModtext)
     return (False, unModtext)

#detectDox("C:\\Users\\Sphi0\\OneDrive\\Documents\\Python Projects\\Ok\\Imagens\\bigassjawline.png")

client.run('MTIyNjM0MTcxNzkwMTQ0MzA5Mw.GUTNuj.GbeuvsGwh2VX4kzTfGA0ThZqKEYG9uRAJ1bqE0')
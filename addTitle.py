from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageColor
#ttfont = ImageFont.truetype("/Library/Fonts/宋体.ttf",20)  #这里我之前使用Arial.ttf时不能打出中文，用华文细黑就可以
im = Image.open("mywordcloud2020.png")
draw = ImageDraw.Draw(im)
font = ImageFont.truetype(r'C:\Windows\Fonts\simhei.ttf',15)

draw.text((10,10),'震惊！2020年您在QQ中\n说得最多的话居然是...', fill=(254,67,101),font=font)

im.save('withTitle2020.png')
im.show()
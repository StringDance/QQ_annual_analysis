"""
思路:
在 QQ消息管理器中将自己的消息记录生成 txt文件。
遍历此文件,将自己说过的话筛选出来并生成一个新的 txt文件。
对这个新的 txt文件使用结巴分词计算出词频.这里使用自定义的 Wordcloud（为了方便，也可以用Python第三方库 wordcloud）画出来.
"""
import re
import jieba
import numpy as np
import random
import math
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageColor

# 全部消息记录记录了你的所有聊天记录，有数百万行，而我们仅需要筛选出自己说的话。
txt = open("全部消息记录.txt", "r", encoding='utf-8')
# 自己说的话保存在 myWordsIn2020.txt中
txtName='myWordsIn2020.txt'
wordsTxt = open(txtName,'w',encoding='utf-8')
for line in txt:
    # 阅读全部消息记录.txt可以发现，聊天记录的格式是：
    # time nickname
    # sentences
    # 或
    # time nickname<qq_mail>
    # sentences
    # 或
    # time nickname(qq_number)
    # sentences
    qq_number='123456'
    # 若改过多次昵称（群昵称也属于）则需要用多个变量
    qq_nickname='你的昵称'
    # 若在QQ资料中改过多次邮箱则需要用多个变量
    qq_mail1='your_email@qq.com'
    qq_mail2='your_email@qq.com'
    if line.startswith('2020') and (qq_number in line or qq_nickname in line or qq_mail1 in line or qq_mail2 in line):
        line=next(txt)
        wordsTxt.write(line)
        wordsTxt.write("\n")


# 根据传入的文本文件生成词频列表，格式是{word1:3,word2:1,...,wordN:M}
def perphraseList(filename):
    txt = open(filename, "r", encoding='utf-8').read()
    # 将需要屏蔽的词语放入excludes，例如人名等无意义或错误划分的词语，常见的划分错误可能是没有将 @后的昵称屏蔽导致将昵称当作句子并划分成词语
    excludes = {'图片','表情','全体成员'}
    words = jieba.lcut(txt)
    counts = {}
    # 匹配两个字以上的中文（一个字的一般是语气词和连接词，意义不大）
    zh_pattern = re.compile(u'[\u4e00-\u9fa5]{2,}')
    # 仅匹配长度1-2的英文。这个设定因人而异。
    en_pattern=re.compile('[a-zA-Z]{1,2}')
    for word in words:
        # 跳过长度为3以上的英文。这个设定因人而异。
        if en_pattern.search(word):
            continue
        else:
            # 如果是中文就放入词频计数器
            if zh_pattern.search(word):
                rword = word
            else:
                continue
        counts[rword] = counts.get(rword, 0) + 1
    # 将 excludes中的词删掉
    for word in excludes:
        del (counts[word])
    items = list(counts.items())
    # 按照词频从大到小排序
    items.sort(key=lambda x: x[1], reverse=True)
    return items


class Region:
    size = 50
    height = 0
    width = 0

    def __init__(self, width, height, size):
        self.regions = {}
        self.size = size

    def add_sprite(self, sprite, x, y):
        width = sprite.img.size[0]
        height = sprite.img.size[1]
        from_x = (x // self.size)
        from_y = (y // self.size)
        to_x = ((x + width) // self.size)
        to_y = ((y + height) // self.size)
        for i in range(from_x, to_x + 1):
            for j in range(from_y, to_y + 1):
                key = '{}-{}'.format(i, j)
                if not key in self.regions:
                    self.regions[key] = []
                self.regions[key].append(sprite)

    def check_sprite(self, sprite, x, y):
        width = sprite.img.size[0]
        height = sprite.img.size[1]
        from_x = (x // self.size)
        from_y = (y // self.size)
        to_x = ((x + width) // self.size)
        to_y = ((y + height) // self.size)
        region_need_to_check = []
        for i in range(from_x, to_x + 1):
            for j in range(from_y, to_y + 1):
                key = '{}-{}'.format(i, j)
                if key in self.regions:
                    region_need_to_check = list(set(region_need_to_check + self.regions[key]))
        return region_need_to_check


class QuadTree:
    x1 = 0
    y1 = 0
    x2 = 0
    y2 = 0
    width = 0
    height = 0
    children = None

    def __init__(self, x1, y1, x2, y2):
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2


class Sprite:
    text = ''
    rotate = 0
    x = None
    y = None
    tree = None
    font_size = None
    img = None

    def build_tree(self):
        integral = np.cumsum(np.cumsum(np.asarray(self.img), axis=1), axis=0)
        width = self.img.size[0]
        height = self.img.size[1]

        self.tree = self._build_tree(integral, 1, 1, width - 2, height - 2)

    def _build_tree(self, integral, x1, y1, x2, y2):
        area = integral[y1 - 1, x1 - 1] + integral[y2, x2]
        area -= integral[y1 - 1, x2] + integral[y2, x1 - 1]
        if not area:
            # 区域内没有像素
            return None

        # 区域内有像素，继续划分
        children = []
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)

        tree = QuadTree(x1, y1, x2, y2)

        # 四叉树最小矩形边长, 该值越大, 速度越快, 但结果越不精确
        min_rect_size = 2
        if x2 - x1 > min_rect_size or y2 - y1 > min_rect_size:
            c0 = self._build_tree(integral, x1, y1, cx, cy)
            c1 = self._build_tree(integral, cx, y1, x2, cy)
            c2 = self._build_tree(integral, x1, cy, cx, y2)
            c3 = self._build_tree(integral, cx, cy, x2, y2)
            if c0:
                children.append(c0)
            if c1:
                children.append(c1)
            if c2:
                children.append(c2)
            if c3:
                children.append(c3)
            if len(children):
                tree.children = children
        return tree


# 矩形重叠检测
def rect_collide(a, b, x1, y1, x2, y2):
    return y1 + a.y2 > y2 + b.y1 and y1 + a.y1 < y2 + b.y2 and x1 + a.x2 > x2 + b.x1 and x1 + a.x1 < x2 + b.x2


# 四叉树重叠检测
def overlaps(tree, other_tree, x1, y1, x2, y2):
    if rect_collide(tree, other_tree, x1, y1, x2, y2):
        if not tree.children:
            if not other_tree.children:
                return True
            else:
                for i in range(0, len(other_tree.children)):
                    if overlaps(tree, other_tree.children[i], x1, y1, x2, y2):
                        return True

        else:
            for i in range(0, len(tree.children)):
                if overlaps(other_tree, tree.children[i], x2, y2, x1, y1):
                    return True

    return False


# [布局] 阿基米德螺线
def archimedean_spiral(width, height):
    def sprial(t, offset=0):
        t = offset + t / 5
        x = int(t * math.cos(t) + (width) // 2)
        y = int(t * math.sin(t) + (height) // 2)
        return x, y, t

    return sprial


# [布局] 矩形螺线
def rectangular_sprial(width, height):
    # 螺旋步长, 该值越大, 速度越快, 但结果越不精确
    dy = dx = 10
    x = y = 0

    def sprial(t, offset=0):
        t = t + offset
        nonlocal x, y
        sign = -1 if t < 0 else 1
        num = int(math.sqrt(1 + 4 * sign * t) - sign) & 3
        if num == 0:
            x += dx
        elif num == 1:
            y += dy
        elif num == 2:
            x -= dx
        else:
            y -= dy
        return x + (width) // 2, y + (height) // 2, t

    return sprial


def find_position(sprite, bounds, offset=0):
    global width, height
    dt = 0
    sprial = rectangular_sprial(width, height)
    i = 0
    while True:
        dt += 1
        x, y, ret = sprial(dt, offset)
        if x > width - sprite.img.size[0] or x < 0 or y > height - sprite.img.size[1] or y < 0:
            break

        placed = bounds.check_sprite(sprite, x, y)
        ok = True
        i += len(placed)

        for p in placed:
            if overlaps(sprite.tree, p.tree, x, y, p.x, p.y):
                ok = False
                break
        if ok:
            return x, y, ret
    return None, None, None


# 词语列表
# txtName='myWordsIn2020.txt'
words = perphraseList(txtName)
words = sorted(words, key=lambda k: -k[1])

# 字体文件
font_file = 'C:/Windows/Fonts/SIMHEI.ttf'

# 画布
# 可自定义长和宽，越大生成所需时间越长,能放的词也就越多，一些出现次数极少的词也包含在内
width = 800
height = 800
img = Image.new("RGBA", (width, height), (255, 255, 255, 255))
draw = ImageDraw.Draw(img)

# [优化] 策略1: 平面分隔区域
bounds = Region(width, height, 50)

# 形状遮罩
mask_sprite = Sprite()
# ----------------这里要自己提供一张图----------------
mask = Image.open('panda.jpg').convert('L').resize((width, height))
mask_sprite.x = 0
mask_sprite.y = 0
mask_sprite.img = mask
mask_sprite.build_tree()
# bounds.add_sprite(mask_sprite, 0, 0)

# 颜色映射
# ----------------这里也要自己提供一张图----------------
color_mask = Image.open('bg2.jpg').resize((width, height))

# 计算四叉树
sprites = []
for (word, size) in words:
    sprite = Sprite()
    sprite.text = word
    sprite.font_size = int(math.sqrt(size) * 4)
    if sprite.font_size < 10:
        sprite.font_size = 10

    font = ImageFont.truetype(font_file, sprite.font_size)
    font = ImageFont.TransposedFont(font)
    size = font.getsize(word)

    # 绘制字符
    img_txt = Image.new('L', (size[0] + 2, size[1] + 2))  # 留边距, 简化运算
    draw_txt = ImageDraw.Draw(img_txt)
    draw_txt.text((1, 1), word, font=font, fill=255)  # 留边距, 简化运算

    # 随机角度旋转
    sprite.rotate = random.randint(-45, 45)
    img_txt = img_txt.rotate(sprite.rotate, resample=Image.NEAREST, expand=1)
    sprite.img = img_txt

    sprite.build_tree()
    sprites.append(sprite)

# 开始放置词语
# [优化] 策略2: 略过低概率区域
prev_sprite = None
offset = 0
i = 0

while i < len(sprites):
    sprite = sprites[i]
    font = ImageFont.truetype(font_file, sprite.font_size)
    font = ImageFont.TransposedFont(font)

    # 判断与上一个词语面积是否差不多
    if not (prev_sprite and (
            (sprite.img.size[0] * sprite.img.size[1]) / (prev_sprite.img.size[0] * prev_sprite.img.size[1]) > 0.8)):
        offset = 0

    # 寻找位置
    x, y, offset = find_position(sprite, bounds, offset)

    # 退出策略, 根据需要调整
    if x == None:
        if not prev_sprite:
            break
        prev_sprite = None
        offset = 0
        continue

    if x > width or x < 0 or y > height or y < 0:
        if not prev_sprite:
            break
        prev_sprite = None
        offset = 0
        continue

    # 找到一个位置
    print('放置第 {} 个词语: {} at {} {}'.format(i, sprite.text, x, y))

    i += 1
    prev_sprite = sprite
    bounds.add_sprite(sprite, x, y)
    sprite.x = x
    sprite.y = y

    # 在画布上绘制单词
    size = font.getsize(sprite.text)
    img_txt = Image.new('RGBA', (size[0] + 2, size[1] + 2))
    draw_txt = ImageDraw.Draw(img_txt)
    color = color_mask.getpixel((x, y))  # 从颜色映射提取颜色

    draw_txt.text((1, 1), sprite.text, font=font, fill=color)

    # 部分系统中, PIL 库绘制的文字边缘有黑边, 手动去除
    r, g, b, a = img_txt.split()
    r = r.point(lambda x: color[0])
    g = g.point(lambda x: color[1])
    b = b.point(lambda x: color[2])
    img_txt = Image.merge('RGBA', (r, g, b, a))

    img_txt = img_txt.rotate(sprite.rotate, resample=Image.BILINEAR, expand=1)
    img.alpha_composite(img_txt, (x, y))

img.show()
img.save('mywordcloud2020.png', 'PNG')





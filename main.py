# coding: u8

from __future__ import print_function, unicode_literals

import colorsys
import itertools
import math
import os
import os.path as osp
import platform
import random
import subprocess
import time
import traceback

from PIL import Image, ImageDraw

# check python version
if int(platform.python_version_tuple()[0]) == 2:
    range = xrange
    zip = itertools.izip
else:
    defalut_range = range
    range = lambda *args: defalut_range(*(int(arg) for arg in args))


class Otsu(object):
    ''''''

    def __init__(self, path, debug=False):
        # 小人色取的是紫黑色
        self.hero_color = (56, 56, 97, 255)
        # 获取截图图片 打开并确认给定的图像文件。这个是一个懒操作；该函数只会读文件头
        self.im = Image.open(path)
        # 宽高
        self.w, self.h = self.im.size
        # 真实的图像数据直到试图处理该数据才会从文件读取（调用load()方法将强行加载图像数据）
        self.pixels = self.im.load()
        # ImageDraw模块的函数 创建一个可以在给定图像上绘图的对象。
        self.draw = ImageDraw.Draw(self.im)
        # 小人的坐标
        self.hero_pos = self.find_hero()
        print('hero pos:', self.hero_pos)

        # 判断小人是否在屏幕左边
        is_hero_on_left = self.hero_pos[0] < self.w / 2

        # 获取背景颜色hsv形式
        bg_hsv = self.get_background_hsv()
        print('background hsv:', bg_hsv)
        #找出目标快顶端，和最左边缘或者最右边缘坐标
        top_most, lr_most = self.find_most(is_hero_on_left, bg_hsv)
        print('top most pos：', top_most)
        print('left/right most pos', lr_most)
        #中心点取top的横坐标，左边缘或者右边缘的纵坐标 这个太粗糙 TODO 需要优化
        self.center_pos = top_most[0], lr_most[1]
        print('center pos', self.center_pos)
        #绘制上面的几个点坐标
        self.draw_pos(self.hero_pos)
        self.draw_pos(top_most)
        self.draw_pos(lr_most)
        self.draw_pos(self.center_pos)

        cx, cy = self.center_pos
        hx, hy = self.hero_pos
        #绘制一条跳跃直线
        self.draw.line((cx, cy, hx, hy), fill=(0, 255, 0), width=8)
        #保存处理过的图片
        self.im.save(path + '.debug.png')

        if debug:
            self.im.show()
            self.erase_background(bg_hsv)
            self.im.show()

    def find_hero(self):
        hero_poses = []
        for y in range(self.h / 3, self.h * 2 / 3):#从上下扫
            for x in range(self.w): # 从左到右
                # is purple 检测小人颜色的位置
                if self.pixels[x, y] == self.hero_color:
                    # 将小人色的坐标存储在hero_poses集合中
                    hero_poses.append((x, y))
        # calc the avg pos 计算出中心点的位置;int直接就四舍五入
        return [int(sum(i) / len(i)) for i in zip(*hero_poses)]

    def rgb_to_hsv(self, r, g, b, a=255):
        h, s, v = colorsys.rgb_to_hsv(r / 255., g / 255., b / 255.)
        return int(h * 255.), int(s * 255.), int(v * 255.)

    def get_background_hsv(self):
        # use the (10, 0.42h) as the background color
        bg_color = self.pixels[10, self.h * .42]
        return self.rgb_to_hsv(*bg_color)

    def erase_background(self, bg_hsv):
        for y in range(self.h / 4, self.h * 2 / 3):
            for x in range(self.w):
                h, s, v = self.rgb_to_hsv(*self.pixels[x, y])
                if self.is_same_color(h, s, v, bg_hsv):
                    self.im.putpixel((x, y), (0, 0, 0))
                else:
                    self.im.putpixel((x, y), (255, 255, 255))

    def find_most(self, is_hero_on_left, bg_hsv):
        hero_radius = 50
        if is_hero_on_left:
            # 如果小人在左边，就在右上选择目标 PIL 坐标系左上角（0,0）
            # top most is on the right, scan from right
            from_x = self.w - 1
            to_x = self.hero_pos[0] + hero_radius
            # 坐标反向移动
            step = -1
        else:
            # 如果小人在右边，就在左上选择目标 PIL 坐标系左上角（0,0）
            # top most is on the left, scan from left
            # 寻找目标的坐标起始为0开始
            from_x = 0
            # 寻找目标的坐标终止为小人左边结束
            to_x = self.hero_pos[0] - hero_radius
            #坐标正向移动
            step = 1
        # 寻找目标的Y坐标起始为四分之一？ 终止为小人top
        from_y, to_y = self.h / 4, self.hero_pos[1]
        #
        top_most = self.find_top_most(bg_hsv, from_x, to_x, from_y, to_y, step)
        lr_most = self.find_lr_most(bg_hsv, from_x, to_x, from_y, to_y, step)
        return top_most, lr_most

    def find_top_most(self, bg_hsv, from_x, to_x, from_y, to_y, step):
        for y in range(from_y, to_y):  # 上下扫
            for x in range(from_x, to_x, step):  # 左右扫
                h, s, v = self.rgb_to_hsv(*self.pixels[x, y])
                # 不一样的坐标块记录下来 （最上的坐标）
                if not self.is_same_color(h, s, v, bg_hsv):
                    return x, y

    def find_lr_most(self, bg_hsv, from_x, to_x, from_y, to_y, step):
        for x in range(from_x, to_x, step):  # 左右扫
            for y in range(from_y, to_y):  # 上下扫
                h, s, v = self.rgb_to_hsv(*self.pixels[x, y])
                #  # 不一样的坐标块记录下来 （左边缘坐标或者右边缘坐标）
                if not self.is_same_color(h, s, v, bg_hsv):
                    return x, y

    def is_same_color(self, h, s, v, bg_hsv):
        '''判断是否颜色相同'''
        bg_h, bg_s, bg_v = bg_hsv

        # yellow background(lightter background)
        if 30 < bg_h < 40:
            diff = 8
        # other background(darker background)
        else:
            diff = 15

        return (abs(h - bg_h) < diff) and (abs(s - bg_s) < 20)

    def draw_pos(self, pos, color=(0, 255, 0)):
        x, y = pos
        r = 25
        self.draw.ellipse((x, y, x + r, y + r), fill=color, outline=color)

    def get_holding(self):
        line_length = int(math.sqrt(
            pow(self.center_pos[0] - self.hero_pos[0], 2) + \
            pow(self.center_pos[1] - self.hero_pos[1], 2)
        ))

        length_time = line_length * 1.4
        #按的时间和目标长度的线性关系
        holding = min(950, max(length_time, 300))

        print('length, duration, holding: ', line_length, length_time, holding)
        print()

        return int(holding)


def run_cmd(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                         stdin=subprocess.PIPE, shell=True)
    stdout, stderr = p.communicate()
    if stderr:
        print(stderr)
    p.wait()
    return stdout, stderr


# directory where screenshot image will be saved in.
# if you use Windows, e.g 'c:/wechat_micro_jump_game_screenshot'
# 截屏图片存放目录
screenshot_directory = '/tmp/wechat_micro_jump_game_screenshot'
if not osp.exists(screenshot_directory):
    os.makedirs(screenshot_directory)

jump_times = itertools.count(0)
while True:
    try:
        debug = False

        if debug:
            # your last failed image name
            fn = '75.png'
            fp = osp.join(screenshot_directory, fn)
        else:
            fn = str(next(jump_times)) + '.png'
            # 生成文件times.png
            fp = osp.join(screenshot_directory, fn)
            # adb shell 截屏指令 且保存到手机/sdcard/s.png
            run_cmd('adb shell screencap -p /sdcard/s.png')
            # adb shell 指令 将手机图片pull到本地
            run_cmd('adb pull /sdcard/s.png {}'.format(fp))
        # 打印图片路径信息
        print(fp)
        # 实例化 Otsu
        otsu = Otsu(fp, debug=debug)
        #计算需要长按的时间
        holding = otsu.get_holding()

        if debug:
            raise KeyboardInterrupt
        else:
            # random tap position
            # anti-wechat detect
            rand_x = lambda: random.randint(0, otsu.w)
            rand_y = lambda: random.randint(0, otsu.h * 3 / 4)
            x1, y1 = rand_x(), rand_y()
            x2, y2 = rand_x(), rand_y()
            #swipe <x1> <y1> <x2> <y2> [duration(ms)]
            # 关于swipe同tap是一样的，只是他是模拟滑动的事件，给出起点和终点的坐标即可。
            # 例如从屏幕(250, 250), 到屏幕(300, 300)即adb shell input swipe 250 250 300 300
            run_cmd('adb shell input swipe {0} {1} {2} {3} {4}'.format(
                x1, y1, x2, y2, holding))
            time.sleep(random.uniform(0.8, 1.0))
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except:
        traceback.print_exc()
        time.sleep(2)
        break

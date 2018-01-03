# -*- coding: utf-8 -*-
# @Time    : 1/3/18 12:14 PM
# @Author  : liyao
# @Email   : hbally@126.com
# @File    : test_main.py
# @Software: PyCharm


if __name__== "__main__":
    defalut_range = range
    range1 = lambda *args: defalut_range(*(int(arg) for arg in args))

    print("range : %s " % range1(10))

    for x in range(10,0,-1):
        print("range : %s " % x)

    hero_poses = []
    hero_poses.append((10,10))
    hero_poses.append((12, 12))
    hero_poses.append((14, 14))
    hero_poses.append((15, 15))
    hero_poses.append((16, 16))
    hero_poses.append((18, 18))
    hero_poses.append((20, 20))
    print([int(sum(i) / len(i)) for i in zip(*hero_poses)])
    print([i for i in zip(*hero_poses)])

    test = 2 < 4
    print(" test <<<<<  %s " % test)
    test = 2 < 1
    print(" test <<<<<  %s " % test)
#! /usr/bin/python

import os.path
import subprocess
import sys
import random
from functools import partial
from getch import getch
from grep import grep
from config import Config
from player import *

def getDictPath():
    return os.path.join(os.environ['HOME'], '.voctrain')
    
def getPath(level):
    return os.path.join(getDictPath(), "%.02d" % level)

def getFile(level, word):
    return os.path.join(getPath(level), word)

def init():
    for level in range(Config.minLevel, Config.maxLevel+1):
        path = getPath(level)
        try:
            os.stat(path)
        except OSError:
            os.mkdir(path)

def edit(level, word):
    file = getFile(level, word)
    try:
        edit = os.environ['EDITOR']
    except KeyError:
        edit = 'vi'

    proc = subprocess.Popen([edit, file])
    proc.wait()

def line():
    sys.stdout.write("-" * 80 + "\n")

def display(level, word):
    line()
    file = getFile(level, word)
    f = open(file, "r")
    sys.stdout.write(f.read())
    f.close()
    line()

def setLevel(level, word, newLevel):
    assert (newLevel > Config.minLevel and newLevel < Config.maxLevel), "new level is %d" % newLevel

    file = getFile(level, word)
    newFile = getFile(newLevel, word)

    os.rename(file, newFile)

def loadLevel(level):
    path = getPath(level)
    words = os.listdir(path)
    random.shuffle(words)
    return words    

def count(level):
    path = getPath(level)
    words = os.listdir(path)
    return len(words)

def find(word):
    for (dirpath, dirnames, filenames) in os.walk(getDictPath()):
        if word in filenames:
            return int(os.path.split(dirpath)[-1])

    return None

def train(level):
    words = loadLevel(level)
    for i in range(len(words)):
        word = words[i]
        sys.stdout.write("[%4d/%4d] " % (i+1, len(words)))
        sys.stdout.write(word)
        sys.stdin.readline()
        display(level, word)

        quitFlag = [False]
        def quit():
            quitFlag[0] = True
            return True

        def correct():
            if level != Config.maxLevel:
                setLevel(level, word, level+1)
            return 1
                
        def incorrect():
            if level != Config.minLevel:
                setLevel(level, word, level-1)
            return 1

        def menu():
            return Menu("correct?", (
                ("yes", "y", correct),
                ("no", "n", incorrect),
                ("edit", "e", partial(edit, level, word)),
                ("quit", "q", quit),
                                ), quit=False, default='n')
 
        play(menu)
        if quitFlag[0]:
            break

def add():
    sys.stdout.write("enter new word: ")
    sys.stdout.flush()
    word = sys.stdin.readline().strip()

    content = grep(word)
    if content:
        sys.stdout.write("found the following translation:\n")
        line()
        sys.stdout.write(content)
        line()
    else:
        sys.stdout.write("not translation found\n")

    level = find(word)
    if level:
        sys.stdout.write("word already exists in level %d\n" % level)
        display(level, word)

        def merge():
            if content:
                file = getFile(level, word)
                f = open(file, "a")
                f.write(content)
                f.close()
            edit(level, word)

        def menu():
            return Menu("what to do?", (
                ("edit", "e", partial(edit, level, word)), 
                ("move to level %d" % Config.minLevel, "m", partial(setLevel, level, word, Config.minLevel)),
                ("merge translations", "g", merge),
                    ))
        play(menu)
    else: 
        def create():
            if content:
                file = getFile(Config.minLevel, word)
                f = open(file, "w")
                f.write(content)
                f.close()
                edit(Config.minLevel, word) 
            return True

        def menu():
            return Menu("what to do?", (
                ("add word", "a", create),))
    
        play(menu)


def selectLevelMenu():
    menu = Menu("select level", quit=False, delim='\n', footer='\n> ')
    for i in range(Config.minLevel, Config.maxLevel+1):
        menu.addOption(Option("level %d [%d words]" % (i, count(i)), str(i), partial(train, i)))
    menu.addQuitOption()
    return menu

def mainMenu():
    return Menu("main menu", (
        ("select level", "s", partial(play, selectLevelMenu)),
        ("add word", "a", add),
    ))

init()
sys.stdout.write("Welcome to voctrain!\n")
play(mainMenu)
sys.stdout.write("Good bye.\n")

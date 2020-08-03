#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This is part of FORTFLAG by Degani Luca


import colorama
from colorama import Fore, Back, Style
colorama.init()
# from https://www.devdungeon.com/content/colorize-terminal-output-python https://github.com/tartley/colorama


class BeautyLogger:
    def __init__(self, label):
        self.label = label

    def printInfo(self, s):
        print(Fore.BLUE + "[-] " + self.label + ": " + Style.RESET_ALL + s)

    def printError(self, s):
        print(Fore.RED + "[!] " + self.label + ": " + s + Style.RESET_ALL)

    def printWarn(self, s):
        print(Fore.YELLOW + "[*] " + self.label + ": " + s + Style.RESET_ALL)

    def printGoodNews(self, s):
        print(Fore.GREEN + "[-] " + self.label + ": " + Style.RESET_ALL + s)

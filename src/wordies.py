from pdb import set_trace
import random
import re
import time
from os import name, system

import pyinputplus as pyip
from colorama import just_fix_windows_console
from english_words import get_english_words_set
from termcolor import colored

just_fix_windows_console()
web2lowerset = get_english_words_set(['web2'], lower=True)

# Clearing the Screen
keyboard_rows = []
keyboard_rows.append("QWERTYUIOP")
keyboard_rows.append(" ASDFGHJKL")
keyboard_rows.append("   ZXCVBNM")
"""
TODO: Print a head with rules and *menu
TODO: Add a console histogram of correct guess frequency
TODO: Prettify prompts and errors with colored. 
TODO: Keep everything lowercase until printing
TODO: For README, explain customizability
TODO: Consider a web version with a python template language or convert to javascript.
"""

class Wordies():
  def __init__(self, word_list) -> None:
    self.guesses_used = 0
    self.letters_guessed = set()
    self.max_guesses = 6
    self.answer = ""
    self.answer_len = 5
    self.answers = word_list
    self.board = []
    self.guess_correct = False
    self.valid_letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    self.display = {}
    self.DEFAULT_COLOR = "white"
    self.CORRECT_PLACE_BG = "green"
    self.WRONG_PLACE_BG = "on_yellow"
    self.EMPTY_SQUARE = "[   ]"
    self.EMPTY_SQUARE_BG = "on_blue"
    self.RIGHT_PLACE_BG = "on_green"
    self.WRONG_LETTER_BG = "on_light_grey"
    self.keyboard_rows = keyboard_rows
    self.show_debug = False
    self.show_clue = False

  def debug(self):
    print("Debug:")
    print("guesses_left: ", self.max_guesses - self.guesses_used)
    print("answer: ", self.answer)

  def setWordAnswer(self):
    rand_index = random.randint(0, len(self.answers) - 1)
    self.answer = self.answers[rand_index].lower()

  def setKeybordLetterBg(self, letter):
    letter = letter.lower()
    if letter in self.letters_guessed:
      if letter in self.answer.lower():
        return "on_green"
      else:
        return "on_light_grey"
    return "on_black"

  def guessWord(self):
    while not self.guess_correct and self.guesses_used < self.max_guesses:
      guess = input("Guess a Word ->: ").lower().strip()
      if self.validateGuess(guess):
        self.letters_guessed.update(list(guess.lower()))
        self.addGuessToBoard(guess)
      self.printBoard()
    if self.guess_correct:
      print("You Won in " + str(self.guesses_used) + " Guesses")
    else:
      if self.guesses_used == self.max_guesses:
        print(f"Out of guesses, the answer was {self.answer}")

  def processMenu(self, prompt):
    prompt = prompt.lower()
    #set_trace()
    if prompt == "*clue":
      self.show_clue = not self.show_clue
    elif prompt == "*debug":
      self.show_debug = not self.show_debug
    else:
      print("menu: use *clue or *debug or guess a word")
      time.sleep(2)

  def reset(self):
    answer = pyip.inputYesNo("Play again?")
    if answer != "yes":
      print("Thanks for playing!")
      return
    else:
      self.__init__(self.answers)
      self.start()

  @staticmethod
  def printError(error):
    #set_trace()
    top = colored("Invalid guess!", "white", "on_red")
    if error == "BAD_LEN":
      detail = colored("Word must be 5 letters long", "yellow", "on_dark_grey")
    elif error == "ONLY_ABC":
      detail = colored("Word must only contain letters from A-Z", "white",
                       "on_blue")
    elif error == "NOT_A_WORD":
      detail = colored("This Guess is not in our word list", "black",
                       "on_white")
    else:
      detail = colored("Try Again!")
    print(top + "\n" + detail)
    time.sleep(2)

  def addGuessToBoard(self, guess):
    guess_row = []
    for i in range(len(guess)):
      if guess[i] in self.answer:
        bg = self.RIGHT_PLACE_BG if guess[i] == self.answer[
            i] else self.WRONG_PLACE_BG
        guess_row.append({
            "letter": "[ " + guess[i] + " ]",
            "color": self.DEFAULT_COLOR,
            "bg": bg
        })
      else:
        guess_row.append({
            "letter": "[ " + guess[i] + " ]",
            "color": self.DEFAULT_COLOR,
            "bg": self.WRONG_LETTER_BG
        })

    self.display[self.guesses_used] = guess_row
    self.guesses_used += 1

  @staticmethod
  def clear():
    _ = system('cls') if name == 'nt' else system('clear')

  def validateGuess(self, guess):
    #set_trace()
    if guess[0] == "*":
      self.processMenu(guess)
      return False
    elif guess == self.answer:
      self.guess_correct = True
      return True
    elif len(guess) != 5:
      self.printError("BAD_LEN")
      return False
    elif guess.lower() not in web2lowerset:
      self.printError("NOT_A_WORD")
      return False
    elif re.search(guess, "[^A-Z]"):
      self.printError("ONLY_ABC")
      return False
    return True

  def setInitialDisplay(self):
    empty_tile = {
        'letter': self.EMPTY_SQUARE,
        'color': self.DEFAULT_COLOR,
        'bg': self.EMPTY_SQUARE_BG
    }
    row = [empty_tile for i in range(self.answer_len)]
    self.display = [row for j in range(self.max_guesses)]

  def printKeyboard(self):
    print("\n")
    for row in keyboard_rows:
      print_row = ""
      for letter in row:
        if letter == " ":
          print_row += letter * 3
        else:
          bg = self.setKeybordLetterBg(letter)
          print_row += colored("[ " + letter.upper() + " ]", "white", bg)
      print(print_row)

  def printBoard(self):
    Wordies.clear()
    for i in range(len(self.display)):
      line = ""
      for j in self.display[i]:
        text = colored(j["letter"].upper(), j["color"], j["bg"])
        line += text
      print(f"\n{line}")
    self.printKeyboard()
    if self.show_debug:
      self.debug()
    if self.show_clue:
      print(f"CLUE: {self.answer[0].upper()}" + "*" * 3 + f"{self.answer[-1].upper()}")

  def start(self):
    self.setInitialDisplay()
    self.setWordAnswer()
    self.printBoard()
    self.guessWord()
    self.reset()
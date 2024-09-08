from src import wordies
from src import clues

def start():
    game = wordies.Wordies(clues.answers)
    game.start()
    
if __name__ == 'main':
    start()
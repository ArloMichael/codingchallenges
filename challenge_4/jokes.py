import time
import argparse
from random import choice

parser = argparse.ArgumentParser(description="Dad Jokes")
parser.add_argument("--add", nargs=2, metavar=("SETUP", "PUNCHLINE"), type=str, help="Add a new joke pair (setup and punchline)")

args = parser.parse_args()

if not args.add:
    def typewriter(text, delay=0.05):
        for char in text:
            print(char, end="", flush=True)
            time.sleep(delay)
        print()

    with open("jokes.txt", "r") as file:
        jokes = [joke.strip().split("<>") for joke in file.readlines()]

    result = choice(jokes)
    typewriter(result[0])
    time.sleep(0.3)
    typewriter("...", delay=0.6)
    print("\033[A\033[K", end="")
    typewriter(result[1])

else:
    with open("jokes.txt", "a") as file:
        file.write("<>".join(args.add) + "\n")
    print(f"Added {' '.join(args.add)} to the database.")
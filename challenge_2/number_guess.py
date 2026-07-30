import argparse
from random import randint

parser = argparse.ArgumentParser(description="Number Guessing Game")
parser.add_argument("--difficulty", choices=["easy", "normal", "hard"], default="normal", help="Select the difficulty")

args = parser.parse_args()

difficulty_map = {
    "easy": {"range": (1, 50), "guess_limit": None},
    "normal": {"range": (1, 100), "guess_limit": 5},
    "hard": {"range": (1, 100), "guess_limit": 1},
}


mode = difficulty_map[args.difficulty]

print(f"Difficulty: {args.difficulty.upper()}")

running = True

while running:
    number = randint(*mode["range"])
    
    for i in range(1, mode["guess_limit"] + 1):
        while True:
            try:
                guess = int(input(f"Guess No. {i}: "))
                break
            except ValueError:
                print("Invalid input! Please try again.")

        if i == mode["guess_limit"]:
            break

        if guess == number:
            break

        if guess < number:
            print("Too low. Try a higher number.")

        if guess > number:
            print("Too high. Try a lower number.")

    if guess != number:
        print(f"Fail. The correct number was {number}.\n")

    elif guess == number:
        print("Correct! Good job.\n")

    while True:
        try:
            user = input("Would you like to play again? [YES, NO]: ")
            if user == "YES":
                break
            elif user == "NO":
                running = False
                break
            else:
                print("Not a valid input, try again.")
        except ValueError:
            print("Not a valid input, try again.")
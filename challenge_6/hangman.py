import re
from random import choice


def is_valid(s):
    return bool(re.fullmatch(r"[A-Za-z]", s))


def clear_two_lines():
    print("\033[2F\033[J", end="", flush=True)


with open("words.txt", "r") as file:
    words = [line.strip() for line in file if line.strip()]

word = choice(words).upper()
word_list = list(word)
display = ["_"] * len(word)
message = ""

for attempt in range(1, 7):
    while True:
        print(" ".join(display))
        guess = input(
            f"{message}Guess No. {attempt}: "
        ).upper()

        clear_two_lines()

        if is_valid(guess):
            message = ""
            break

        message = "INVALID. "

    if guess in word_list:
        for i, letter in enumerate(word_list):
            if letter == guess:
                display[i] = letter

    if display == word_list:
        print(" ".join(display))
        print("You won!")
        break
else:
    print(" ".join(display))
    print(f"The word was: {word}.")
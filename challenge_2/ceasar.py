import argparse

parser = argparse.ArgumentParser(description="Ceasar Cypher")
parser.add_argument("text", type=str, help="The text to shift")

args = parser.parse_args()

print("".join([chr(x) for x in [ord(char) + 1 for char in args.text]]))
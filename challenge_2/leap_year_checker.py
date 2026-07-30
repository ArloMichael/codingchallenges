import argparse

parser = argparse.ArgumentParser(description="Leap Year Checker")
parser.add_argument("year", type=int, help="The year to check")

args = parser.parse_args()

print(args.year % 4 == 0 and (args.year % 100 != 0 or args.year % 400 == 0))
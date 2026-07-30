import argparse
import sounddevice as sd
import pyfxr

parser = argparse.ArgumentParser(description="FizzBuzz CLI")
parser.add_argument("--range", dest="number_range", nargs=2, type=int, metavar=("start", "stop"), default=(1, 100), help="Specify a range")
parser.add_argument("--fizz", default="Fizz", help="Choose the text printed for multiples of 3")
parser.add_argument("--buzz", default="Buzz", help="Choose the printed for multiples of 5")
parser.add_argument("--fizzbuzz", default=None, help="Choose the printed for multiples of both 3 and 5")
parser.add_argument("--sound", action="store_true", help="Enable sound effects")

args = parser.parse_args()

start, stop = args.number_range
fizzbuzz = args.fizzbuzz or f"{args.fizz}{args.buzz}"


for i in range(start, stop + 1):
    if (i % 3 == 0) and (i % 5 == 0):
        print(fizzbuzz)

        if args.sound:
            sd.play(pyfxr.explosion(), pyfxr.SAMPLE_RATE, blocking=True)

        continue

    if i % 3 == 0:
        print(args.fizz)

        if args.sound:
            sd.play(pyfxr.jump(), pyfxr.SAMPLE_RATE, blocking=True)

        continue

    if i % 5 == 0:
        print(args.buzz)

        if args.sound:
            sd.play(pyfxr.hurt(), pyfxr.SAMPLE_RATE, blocking=True)

        continue

    print(i)
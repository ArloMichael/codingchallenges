import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description="Digital Diary")
subparsers = parser.add_subparsers(dest="mode", help="Select operation mode")

read_parser = subparsers.add_parser("read", help="Read a diary")
read_parser.add_argument("filepath", type=Path, help="File")

append_parser = subparsers.add_parser("append", help="Append to a diary")
append_parser.add_argument("filepath", type=Path, help="File")
append_parser.add_argument("text", type=str, help="Text to add")


create_parser = subparsers.add_parser("create", help="Create a diary")
create_parser.add_argument("filepath", type=Path, help="File")

args = parser.parse_args()

exists = args.filepath.is_file()

if args.mode == "create":
    if exists:
        print("File already exists, please choose a different file path or operation mode.")
    else:
        with open(args.filepath, "w") as file:
            file.write("")

elif args.mode == "append":
    if not exists:
        print("File does not exist. Check filename or use the 'create' subcommand.")
    else:
        from datetime import date

        today = date.today()
        formatted_date = today.strftime("%d/%m/%Y")

        with open(args.filepath, "a") as file:
            file.write(f"{formatted_date}: {args.text}\n")

elif args.mode == "read":
    if not exists:
        print("File does not exist. Check filename or use the 'create' subcommand.")
    else:
        print()
        with open(args.filepath, "r") as file:
            print(file.read())
import argparse

studentsGrades = {
    "Alice": {
            "Maths": 88,
            "Science": 90,
            "History": 76,
            "English": 94,
            },
    "Ben": {
            "Maths": 78,
            "Science": 80,
            "History": 88,
            "English": 85,
            },
    "Clara": {
            "Maths": 82,
            "Science": 94,
            "History": 60,
            "English": 99,
            },
    "Suzy": {
            "Maths": 62,
            "Science": 64,
            "History": 50,
            "English": 41,
            },
    "Paul": {
            "Maths": 80,
            "Science": 95,
            "History": 65,
            "English": 85,
            },
    "Jane": {
            "Maths": 81,
            "Science": 75,
            "History": 84,
            "English": 85,
            },
}

def mark_to_grade(mark):
    if mark >= 90:
        return "A"
    elif mark >= 80:
        return "B"
    elif mark >= 70:
        return "C"
    elif mark >= 60:
        return "D"
    elif mark >= 50:
        return "E"
    else:
        return "F"

def generate_report(name):
    avg = sum(studentsGrades[name].values()) / len(studentsGrades[name].values())
    subject_lines = ""
    for subject, grade in studentsGrades[name].items():
        subject_lines += f"{subject}: {grade}\n"

    return (
        f"NAME: {name}\n"
        f"SUBJECTS:\n{subject_lines}"
        f"AVG MARK: {avg}\n"
        f"AVG GRADE: {mark_to_grade(avg)}\n"
        f"WORST SUBJECT: {min(studentsGrades[name], key=lambda subject: studentsGrades[name][subject])}\n"
        f"BEST SUBJECT: {max(studentsGrades[name], key=lambda subject: studentsGrades[name][subject])}\n"
    )


parser = argparse.ArgumentParser(description="Report Card Generator")
subparsers = parser.add_subparsers(dest="mode", help="Select the mode")

one_parser = subparsers.add_parser("generate", help="Generates a report for one student")
one_parser.add_argument("name", choices=list(studentsGrades.keys()), help="Student name")
one_parser.add_argument("--graph", action="store_true", help="Display a bar graph of grades")

all_parser = subparsers.add_parser("generate_all", help="Generates a report for every student")

update_parser = subparsers.add_parser("update", help="Add or update a student's grade")
update_parser.add_argument("name", help="Student name")
update_parser.add_argument("subject", help="Subject name")
update_parser.add_argument("grade", type=int, choices=range(0, 101), help="Grade from 0 to 100")


args = parser.parse_args()

if args.mode == "generate":
    print()
    print(generate_report(args.name))

    if args.graph:
        import matplotlib.pyplot as plt

        plt.bar(list(studentsGrades[args.name].keys()), list(studentsGrades[args.name].values()), color='skyblue', edgecolor='black', width=0.6)

        plt.title('Subject Breakdown')
        plt.xlabel('Mark')
        plt.ylabel('Subject')

        plt.show()
        
elif args.mode == "generate_all":
    print()
    for name in list(studentsGrades.keys()):
        print(generate_report(name))

elif args.mode == "update":
    if args.name not in studentsGrades:
        studentsGrades[args.name] = {}

    studentsGrades[args.name][args.subject] = args.grade
    print()
    print(generate_report(args.name))

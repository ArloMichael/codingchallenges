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

subjects = list(next(iter(studentsGrades.values())).keys())
print("HIGHEST GRADES:\n")
for subject in subjects:
    top_student = max(studentsGrades, key=lambda name: studentsGrades[name][subject])
    print(f"{subject}: {top_student} ({studentsGrades[top_student][subject]})")

print("\nLOWEST GRADES:\n")
for subject in subjects:
    lowest_student = min(studentsGrades, key=lambda name: studentsGrades[name][subject])
    print(f"{subject}: {studentsGrades[lowest_student][subject]}")

top_student = max(studentsGrades, key=lambda name: sum(studentsGrades[name].values()))
print(f"\nTOP GRADE: {top_student}")

import json
import uuid
from pathlib import Path
from datetime import datetime

RAW_FOLDER = Path("raw")
RAW_FOLDER.mkdir(exist_ok=True)


def save_capture(capture_type, content):
    note_id = str(uuid.uuid4())

    data = {
        "id": note_id,
        "timestamp": datetime.now().isoformat(),
        "type": capture_type,
        "content": content,
    }

    file_path = RAW_FOLDER / f"{note_id}.json"

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

    print("\n✅ Saved Successfully!")
    print(f"📁 {file_path}")


def capture_note():
    note = input("Enter your note: ")
    save_capture("note", note)


def capture_link():
    link = input("Enter URL: ")
    save_capture("link", link)


def capture_file():
    file_path = input("Enter file path: ")

    path = Path(file_path)

    if not path.exists():
        print("❌ File not found!")
        return

    data = {
        "filename": path.name,
        "extension": path.suffix,
        "location": str(path.resolve())
    }

    save_capture("file", data)


def main():

    print("\n===== SecondSelf Capture =====")
    print("1. Capture Note")
    print("2. Capture Link")
    print("3. Capture File")

    choice = input("\nChoose (1-3): ")

    if choice == "1":
        capture_note()

    elif choice == "2":
        capture_link()

    elif choice == "3":
        capture_file()

    else:
        print("Invalid Choice")


if __name__ == "__main__":
    main()
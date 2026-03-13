import pickle
from collections import UserDict
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Callable

# --- КЛАСИ ДЛЯ ДАНИХ (ЛОГІКА) ---


class Field:
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value: str):
        if not self._validate(value):
            raise ValueError("Phone number must be 10 digits.")
        super().__init__(value)

    def _validate(self, value: str) -> bool:
        return len(value) == 10 and value.isdigit()


class Birthday(Field):
    def __init__(self, value: str):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    def __str__(self) -> str:
        return self.value.strftime("%d.%m.%Y")


class Record:
    def __init__(self, name: str):
        self.name = Name(name)
        self.phones: List[Phone] = []
        self.birthday: Optional[Birthday] = None

    def add_phone(self, phone_number: str):
        self.phones.append(Phone(phone_number))

    def edit_phone(self, old_number: str, new_number: str):
        phone_obj = self.find_phone(old_number)
        if not phone_obj:
            raise ValueError(f"Phone {old_number} not found.")
        new_phone = Phone(new_number)
        index = self.phones.index(phone_obj)
        self.phones[index] = new_phone

    def find_phone(self, phone_number: str) -> Optional[Phone]:
        for phone in self.phones:
            if phone.value == phone_number:
                return phone
        return None

    def add_birthday(self, date_str: str):
        self.birthday = Birthday(date_str)

    def __str__(self) -> str:
        phones = "; ".join(p.value for p in self.phones)
        birthday = f", birthday: {self.birthday}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {phones}{birthday}"


class AddressBook(UserDict):
    def add_record(self, record: Record):
        self.data[record.name.value] = record

    def find(self, name: str) -> Optional[Record]:
        return self.data.get(name)

    def get_upcoming_birthdays(self) -> List[dict]:
        upcoming = []
        today = datetime.today().date()
        for record in self.data.values():
            if not record.birthday:
                continue
            bday = record.birthday.value.replace(year=today.year)
            if bday < today:
                bday = bday.replace(year=today.year + 1)
            if 0 <= (bday - today).days <= 7:
                if bday.weekday() >= 5:
                    bday += timedelta(days=(7 - bday.weekday()))
                upcoming.append(
                    {"name": record.name.value, "congratulation_date": bday.strftime("%d.%m.%Y")})
        return upcoming

# --- ФУНКЦІЇ ЗБЕРЕЖЕННЯ ТА ЗАВАНТАЖЕННЯ (НОВЕ) ---


def save_data(book, filename="addressbook.pkl"):
    """Серіалізація адресної книги у файл."""
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"):
    """Десеріалізація адресної книги з файлу."""
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  # Повертаємо нову книгу, якщо файл відсутній

# --- ОБРОБКА КОМАНД ---


def input_error(func: Callable) -> Callable:
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e)
        except KeyError:
            return "Contact not found."
        except IndexError:
            return "Enter the argument for the command."
    return inner


def parse_input(user_input: str) -> Tuple[str, List[str]]:
    if not user_input.strip():
        return "", []
    cmd, *args = user_input.split()
    return cmd.strip().lower(), args


@input_error
def add_contact(args, book):
    name, phone, *_ = args
    record = book.find(name)
    if record is None:
        record = Record(name)
        book.add_record(record)
        record.add_phone(phone)
        return "Contact added."
    record.add_phone(phone)
    return "Phone added to existing contact."

# --- ОСНОВНИЙ ЦИКЛ ---


def main():
    # Завантажуємо дані при старті
    book = load_data()
    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            # Зберігаємо дані перед виходом
            save_data(book)
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "all":
            for record in book.data.values():
                print(record)
        elif command == "add-birthday":
            if len(args) < 2:
                print("Enter name and birthday.")
                continue
            name, date = args
            record = book.find(name)
            if record:
                print(record.add_birthday(date) or "Birthday added.")
            else:
                print("Contact not found.")
        elif command == "birthdays":
            upcoming = book.get_upcoming_birthdays()
            for entry in upcoming:
                print(f"{entry['name']}: {entry['congratulation_date']}")
        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()

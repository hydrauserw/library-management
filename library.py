#  Система управления библиотекой «Читай-Город». Автоматизация учёта и выдачи книг, регистрации читателей

import json
import os
from datetime import datetime, timedelta


#  КАТАЛОГ КНИГ

BOOKS_CATALOG = {
    "1": {"title": "Преступление и наказание", "author": "Ф.М. Достоевский", "year": 1866, "copies": 3},
    "2": {"title": "Мастер и Маргарита", "author": "М.А. Булгаков", "year": 1967, "copies": 2},
    "3": {"title": "1984", "author": "Дж. Оруэлл", "year": 1949, "copies": 4},
    "4": {"title": "Гарри Поттер и Философский камень", "author": "Дж. Роулинг", "year": 1997, "copies": 5},
    "5": {"title": "Война и мир", "author": "Л.Н. Толстой", "year": 1869, "copies": 2},
    "6": {"title": "Идиот", "author": "Ф.М. Достоевский", "year": 1869, "copies": 3},
    "7": {"title": "Старик и море", "author": "Э. Хемингуэй", "year": 1952, "copies": 4},
    "8": {"title": "Алхимик", "author": "П. Коэльо", "year": 1988, "copies": 6},
}

BOOKS_FILE = "library_books.json"
READERS_FILE = "library_readers.json"
LOANS_FILE = "library_loans.json"


#  ФАЙЛЫ


def load_json(filename, default):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def init_library():
    if not os.path.exists(BOOKS_FILE):
        books = []
        for code, info in BOOKS_CATALOG.items():
            books.append({
                "id": code,
                **info,
                "available": info["copies"]
            })
        save_json(BOOKS_FILE, books)
    if not os.path.exists(READERS_FILE):
        save_json(READERS_FILE, [])
    if not os.path.exists(LOANS_FILE):
        save_json(LOANS_FILE, [])


#  ВЫВОД


def print_books(books):
    print("\n" + "=" * 70)
    print("                    📚 КАТАЛОГ БИБЛИОТЕКИ")
    print("=" * 70)
    print(f"  {'ID':<4} {'Название':<30} {'Автор':<20} {'Ост.':>4}")
    print("-" * 70)
    for b in books:
        status = "✓" if b["available"] > 0 else "✗"
        print(f"  {b['id']:<4} {b['title']:<30} {b['author']:<20} {b['available']:>2} {status}")
    print("=" * 70)


def print_readers(readers, loans):
    if not readers:
        print("\nЧитателей пока нет.")
        return
    print("\n" + "=" * 50)
    print(f"  {'ID':<4} {'ФИО':<20} {'Год рег.':<8} {'Книг на руках':>10}")
    print("-" * 50)
    for r in readers:
        # считаем сколько книг сейчас на руках
        cnt = sum(1 for l in loans if l["reader_id"] == str(r["id"]) and l["returned"] is None)
        print(f"  {r['id']:<4} {r['name']:<20} {r['reg_year']:<8} {cnt:>10}")
    print("=" * 50)


def print_loan_card(loan, books, readers):
    book = next((b for b in books if b["id"] == loan["book_id"]), {})
    reader = next((r for r in readers if r["id"] == loan["reader_id"]), {})

    print("\n" + "=" * 50)
    print(f"         ВЫДАЧА № {loan['id']}")
    print("=" * 50)
    print(f"  Книга:    {book.get('title', '—')} ({book.get('author', '—')})")
    print(f"  Читатель: {reader.get('name', '—')} (ID: {reader.get('id', '—')})")
    print(f"  Выдана:   {loan['date_issued']}")
    print(f"  Вернуть до: {loan['due_date']}")
    status = "✓ Возвращена" if loan["returned"] else "⏳ На руках"
    if loan["returned"]:
        status += f" ({loan['returned']})"
    print(f"  Статус:   {status}")
    print("=" * 50)


#  ОСНОВНЫЕ ФУНКЦИИ


def add_reader(readers):
    print("\n──── РЕГИСТРАЦИЯ ЧИТАТЕЛЯ ────")
    name = input("ФИО читателя: ").strip()
    if not name:
        print("Имя не может быть пустым.")
        return readers

    new_id = len(readers) + 1
    readers.append({
        "id": new_id,
        "name": name,
        "reg_year": datetime.now().year
    })
    save_json(READERS_FILE, readers)
    print(f"Читатель '{name}' зарегистрирован под ID: {new_id}")
    return readers


def issue_book(books, readers, loans):
    print("\n──── ВЫДАЧА КНИГИ ────")

    print_books(books)
    book_id = input("\nID книги: ").strip()
    book = next((b for b in books if b["id"] == book_id), None)
    if not book or book["available"] <= 0:
        print("Книга не найдена или недоступна.")
        return books, readers, loans

    print_readers(readers, loans)
    reader_id = input("ID читателя: ").strip()
    reader = next((r for r in readers if str(r["id"]) == reader_id), None)
    if not reader:
        print("Читатель не найден.")
        return books, readers, loans

    # не больше 3 книг на руках
    active = sum(1 for l in loans if l["reader_id"] == reader_id and not l["returned"])
    if active >= 3:
        print("У читателя уже 3 книги на руках (лимит).")
        return books, readers, loans

    now = datetime.now()
    loan = {
        "id": len(loans) + 1,
        "book_id": book_id,
        "reader_id": reader_id,
        "date_issued": now.strftime("%d.%m.%Y"),
        "due_date": (now + timedelta(days=14)).strftime("%d.%m.%Y"),
        "returned": None
    }

    book["available"] -= 1
    loans.append(loan)
    save_json(BOOKS_FILE, books)
    save_json(LOANS_FILE, loans)

    print_loan_card(loan, books, readers)
    print("Книга успешно выдана!")
    return books, readers, loans


def return_book(books, loans):
    print("\n──── ВОЗВРАТ КНИГИ ────")

    active_loans = [l for l in loans if not l["returned"]]
    if not active_loans:
        print("Нет активных выдач.")
        return books, loans

    print("\nАктивные выдачи:")
    for l in active_loans:
        book = next((b for b in books if b["id"] == l["book_id"]), {})
        print(f"  №{l['id']}: {book.get('title', '—')} — до {l['due_date']}")

    loan_id = input("\nНомер выдачи для возврата: ").strip()
    loan = next((l for l in loans if str(l["id"]) == loan_id and not l["returned"]), None)
    if not loan:
        print("Выдача не найдена или уже закрыта.")
        return books, loans

    loan["returned"] = datetime.now().strftime("%d.%m.%Y")

    book = next((b for b in books if b["id"] == loan["book_id"]), None)
    if book:
        book["available"] += 1

    save_json(BOOKS_FILE, books)
    save_json(LOANS_FILE, loans)
    print(f"Книга возвращена {loan['returned']}")
    return books, loans


def statistics(books, readers, loans):
    print("\n" + "=" * 44)
    print("         СТАТИСТИКА БИБЛИОТЕКИ")
    print("=" * 44)

    total = sum(b["copies"] for b in books)
    available = sum(b["available"] for b in books)

    active_loans = [l for l in loans if not l["returned"]]
    returned = [l for l in loans if l["returned"]]

    today = datetime.now()
    overdue = [l for l in active_loans
               if datetime.strptime(l["due_date"], "%d.%m.%Y") < today]

    print(f"  Всего экземпляров:  {total:>5}")
    print(f"  Доступно:           {available:>5}")
    print(f"  На руках:           {total - available:>5}")
    print("-" * 44)
    print(f"  Читателей:          {len(readers):>5}")
    print(f"  Активных выдач:     {len(active_loans):>5}")
    print(f"  Возвращено:         {len(returned):>5}")
    print(f"  ⚠️ Просрочено:       {len(overdue):>5}")

    if books:
        popular = max(books, key=lambda b: b["copies"] - b["available"])
        print(f"   Популярная: {popular['title']}")
    print("=" * 44)


#  ГЛАВНЫЙ ЦИКЛ


def main():
    init_library()
    books = load_json(BOOKS_FILE, [])
    readers = load_json(READERS_FILE, [])
    loans = load_json(LOANS_FILE, [])

    print("\n" + "📚" * 20)
    print("   БИБЛИОТЕКА «ЧИТАЙ-ГОРОД»")
    print("   Система учёта и выдачи книг")
    print("📚" * 20)

    while True:
        print("\n---- ГЛАВНОЕ МЕНЮ ----")
        print("  1. Каталог книг")
        print("  2. Список читателей")
        print("  3. Зарегистрировать читателя")
        print("  4. Выдать книгу")
        print("  5. Принять возврат")
        print("  6. Статистика")
        print("  0. Выход")

        choice = input("\nВаш выбор: ").strip()

        if choice == "1":
            print_books(books)
        elif choice == "2":
            print_readers(readers, loans)
        elif choice == "3":
            readers = add_reader(readers)
        elif choice == "4":
            books, readers, loans = issue_book(books, readers, loans)
        elif choice == "5":
            books, loans = return_book(books, loans)
        elif choice == "6":
            statistics(books, readers, loans)
        elif choice == "0":
            print("\n Спасибо за работу с библиотекой!")
            break
        else:
            print("Неверный ввод. Выберите 0–6.")


if __name__ == "__main__":
    main()
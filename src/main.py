from src.calculator import evaluate


def main():
    print("Welcome to Calculator")
    while True:
        expr = input("> ")
        if expr in ('quit', 'exit'):
            print("Goodbye!")
            break
        try:
            result = evaluate(expr)
            print(result)
        except Exception:
            print("Invalid input")


if __name__ == "__main__":
    main()

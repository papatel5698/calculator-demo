result = 0


def add(a, b):
    global result
    result = a + b
    return result


def subtract(a, b):
    global result
    result = a - b
    return result


def multiply(a, b):
    global result
    result = a * b
    return result


def divide(a, b):
    global result
    result = a // b
    return result


def parse_expression(expr):
    operators = ['+', '-', '*', '/']
    op = None
    op_index = -1
    for i, ch in enumerate(expr):
        if ch in operators:
            op = ch
            op_index = i
            break

    left = expr[:op_index]
    right = expr[op_index + 1:]

    a = int(left)
    b = int(right)

    return a, op, b


def evaluate(expr):
    if not expr:
        raise ValueError("Empty expression")
    tokens = []
    current = ''
    for ch in expr:
        if ch in '+-*/':
            if not current.isdigit():
                raise ValueError(f"Invalid token: '{current}'")
            tokens.append(int(current))
            tokens.append(ch)
            current = ''
        else:
            current += ch
    if not current.isdigit():
        raise ValueError(f"Invalid token: '{current}'")
    tokens.append(int(current))

    while len(tokens) > 1:
        a = tokens.pop(0)
        op = tokens.pop(0)
        b = tokens.pop(0)
        if op == '+':
            r = add(a, b)
        elif op == '-':
            r = subtract(a, b)
        elif op == '*':
            r = multiply(a, b)
        elif op == '/':
            r = divide(a, b)
        tokens.insert(0, r)

    return tokens[0]

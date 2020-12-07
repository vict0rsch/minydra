def split_line(line, length):
    items = [
        line[length * i : length * (i + 1)] for i in range(len(line) // length + 1)
    ]
    return [i for i in items if i.lstrip()]

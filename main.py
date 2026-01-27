<<<<<<< HEAD
=======
<<<<<<< HEAD
def multiply(a, b):   # Added comma between parameters
    return a * b

def main():
    x = 6
    y = 7
    print("Product =", multiply(x, y))  # Fixed function name typo

if __name__ == "__main__":
    main()
=======
>>>>>>> 26f1cae9aeab63e0166ec9cc08e139282db9c2b2
def read_file(path):
    with open(path, 'r') as f:
        return f.read()

def main():
<<<<<<< HEAD
    content = read_file("data.txt")  # Corrected function name
    print("File Content:", content)

if __name__ == "__main__":
    main()
=======
    content = read_file("data.txt")
    print("File Content:", content)

if __name__ == "__main__":
    main()
>>>>>>> 8e0ab90e846c09539f1aef17b22ddb08fab0d7c3
>>>>>>> 26f1cae9aeab63e0166ec9cc08e139282db9c2b2

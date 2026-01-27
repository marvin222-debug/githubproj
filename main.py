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
def read_file(path):
    with open(path, 'r') as f:
        return f.read()

def main():
    content = read_file("data.txt")
    print("File Content:", content)

if __name__ == "__main__":
    main()
>>>>>>> 8e0ab90e846c09539f1aef17b22ddb08fab0d7c3

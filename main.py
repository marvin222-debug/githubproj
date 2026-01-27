def read_file(path):
    with open(path, 'r') as f:
        return f.read()

def main():
    content = read_file("data.txt")  # Corrected function name
    print("File Content:", content)

if __name__ == "__main__":
    main()
from utils import calculate_average, load_numbers
from config import DATA_FILE

def main():
    numbers = load_numbers(DATA_FILE)
    avg = calculate_average(numbers)
    print(f"Average of numbers: {avg}")

if __name__ == "__main__":
    main()

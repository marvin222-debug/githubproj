from utils import calculate_average, load_numbers
from config import DATAFILE   # ❌ wrong variable name

def main():
    numbers = load_numbers(DATAFILE)
    avg = calculate_average(number_list)   # ❌ variable not defined
    print(f"Average of numbers: {avg}")

if __name__ == "__main__":
    main()

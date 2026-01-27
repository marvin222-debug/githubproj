# Fixed Program: Same code but with mistakes corrected

import math  # Added missing import for math module

def add_numbers(a, b):
    return a + b

def main():
    x = 10
    y = 20
    result = add_numbers(x, y)

    print("The sum is:", result)  # Fixed syntax error by adding comma

    print(math.sqrt(25))          # Now works because math is imported

    z = 30  # Defined variable z to avoid NameError
    print("Value of z:", z)       # Now works because z is defined

if __name__ == "__main__":
    main()
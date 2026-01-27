# Error Program: Same code but with mistakes

# Import the math module
import math

def add_numbers(a, b):
    return a + b

def main():
    x = 10
    y = 20
    result = add_numbers(x, y)

    # Fix the syntax error by adding a comma
    print("The sum is:", result)  

    # Use the math module to calculate the square root
    print(math.sqrt(25))         

    # Define z before using it
    z = 30
    print("Value of z:", z)       

if __name__ == "__main__":
    main()
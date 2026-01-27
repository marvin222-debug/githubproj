<<<<<<< HEAD
# Error Program: Same code but with mistakes

# Import the math module
import math
=======
# Fixed Program: Same code but with mistakes corrected

import math  # Added missing import for math module
>>>>>>> 3feec23028d038d38863c67159d05705a0c44a9e

def add_numbers(a, b):
    return a + b

def main():
    x = 10
    y = 20
    result = add_numbers(x, y)

<<<<<<< HEAD
    # Fix the syntax error by adding a comma
    print("The sum is:", result)  

    # Use the math module to calculate the square root
    print(math.sqrt(25))         

    # Define z before using it
    z = 30
    print("Value of z:", z)       
=======
    print("The sum is:", result)  # Fixed syntax error by adding comma

    print(math.sqrt(25))          # Now works because math is imported

    z = 30  # Defined variable z to avoid NameError
    print("Value of z:", z)       # Now works because z is defined
>>>>>>> 3feec23028d038d38863c67159d05705a0c44a9e

if __name__ == "__main__":
    main()
def load_numbers(path):
    with open(path, "r") as f:
        return [int(x.strip()) for x in f.readlines()]

def calculate_average(nums):
    if not nums:
        return 0
    return sum(nums) / len(nums)

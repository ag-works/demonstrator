"""
Program to demonstrate the binary search in Python
"""

import random


def binary_search(array, x, low, high):
    # Repeat loop until the pointers low and high meet
    while low <= high:
        # Calculate the mid point between low and high
        mid = low + (high - low) // 2
        if array[mid] == x:
            return mid
        elif array[mid] < x:
            low = mid + 1
        else:
            high = mid - 1

    return -1

if __name__ == '__main__':
    # Create a sorted array of integers using list comprehension
    array = [num for num in range(10)]
    item = random.randint(0, 10)
    result = binary_search(array, item, 0, len(array) - 1)

    if result != -1:
        print(f"Element {item} is present at index {result}.")
    else:
        print(f"Element {item} does not exist in the array.")

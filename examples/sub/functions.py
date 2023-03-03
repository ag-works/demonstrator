import math


def area(radius):
    """Returns the area of the circle for the given radius"""

    result = math.pi * math.pow(radius, 2)
    return result


def factorial(x):
    """Returns the factorial of the given number"""

    if x == 1:
        return 1
    else:
        return x * factorial(x - 1)

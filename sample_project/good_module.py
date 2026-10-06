"""A small, well-factored utility module used as a 'good' sample."""


def add(a, b):
    """Return the sum of two numbers."""
    return a + b


def average(values):
    """Return the arithmetic mean of a list of numbers."""
    if not values:
        return 0
    return sum(values) / len(values)


def clamp(value, low, high):
    """Clamp value into the inclusive [low, high] range."""
    if value < low:
        return low
    if value > high:
        return high
    return value


class Rectangle:
    """Simple rectangle with area and perimeter helpers."""

    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height

    def perimeter(self):
        return 2 * (self.width + self.height)

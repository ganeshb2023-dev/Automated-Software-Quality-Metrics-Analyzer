"""Demonstrates a small inheritance hierarchy for CBO / DIT / LCOM scoring."""


class Shape:
    def __init__(self, name):
        self.name = name

    def describe(self):
        return f"Shape: {self.name}"


class Polygon(Shape):
    def __init__(self, name, sides):
        super().__init__(name)
        self.sides = sides

    def side_count(self):
        return self.sides


class Square(Polygon):
    def __init__(self, length):
        super().__init__("Square", 4)
        self.length = length

    def area(self):
        return self.length * self.length


class ShapeRegistry:
    """Deliberately low-cohesion class mixing unrelated responsibilities."""

    def __init__(self):
        self.shapes = []
        self.log_lines = []
        self.counter = 0

    def register(self, shape: Shape):
        self.shapes.append(shape)
        self.counter += 1

    def log(self, message):
        self.log_lines.append(message)

    def export_csv(self):
        return "\n".join(s.name for s in self.shapes)

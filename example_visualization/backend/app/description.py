import random

def generate_description():
    # lightweight rotation of Iris-centric blurbs for the frontend
    samples = [
        "Setosa consistently shows the most compact measurements, while Virginica stretches the scale at the upper end.",
        "Versicolor tends to sit between the other two species, making it a useful reference point for mid-range values.",
        "Notice how the ratios tighten for Setosa—the smaller petals keep its shape closer to a perfect ellipse.",
        "Sepal measurements dominate the spread; petals only overtake when Virginica enters the comparison.",
    ]
    return random.choice(samples)

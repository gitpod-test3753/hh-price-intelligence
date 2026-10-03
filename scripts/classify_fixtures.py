from pathlib import Path

from hhpi.classification.price_list import StructuralPriceListClassifier


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    classifier = StructuralPriceListClassifier()
    for path in sorted((root / "benchmarks" / "fixtures" / "raw").glob("*.jpg")):
        result = classifier.classify(path)
        print(path.name, result.label, f"{result.confidence:.3f}", "; ".join(result.reasons))

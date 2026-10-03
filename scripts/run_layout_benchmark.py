from pathlib import Path

from hhpi.benchmark.layout_runner import run_layout_benchmark


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    rows = run_layout_benchmark(root / "benchmarks" / "fixtures" / "raw", root / "benchmarks")
    for row in rows:
        print(
            f"{row['file']}: likelihood={row['table_likelihood']:.3f} "
            f"h_lines={len(row['horizontal_lines'])} v_lines={len(row['vertical_lines'])} "
            f"regions={len(row['regions'])}"
        )

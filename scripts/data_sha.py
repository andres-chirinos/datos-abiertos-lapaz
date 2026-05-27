from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path


def compute_tree_sha(input_dir: Path) -> str:
    """Build a deterministic SHA-256 hash from file paths and file contents."""
    hasher = hashlib.sha256()

    files = sorted(p for p in input_dir.rglob("*") if p.is_file())
    for file_path in files:
        rel_path = file_path.relative_to(input_dir).as_posix()
        hasher.update(rel_path.encode("utf-8"))
        hasher.update(b"\0")
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                hasher.update(chunk)
        hasher.update(b"\0")

    return hasher.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calcula y guarda la SHA de un directorio para detectar cambios."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data"),
        help="Directorio a hashear. Default: data",
    )
    parser.add_argument(
        "--sha-file",
        type=Path,
        default=Path(".repo_state/data.sha256"),
        help="Archivo donde se guarda la SHA previa/actual.",
    )
    parser.add_argument(
        "--github-output",
        type=Path,
        default=None,
        help="Ruta de GITHUB_OUTPUT (opcional).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.input_dir.exists():
        raise SystemExit(f"Error: no existe el directorio {args.input_dir}")

    current_sha = compute_tree_sha(args.input_dir)
    previous_sha = ""

    if args.sha_file.exists():
        previous_sha = args.sha_file.read_text(encoding="utf-8").strip()

    changed = current_sha != previous_sha

    args.sha_file.parent.mkdir(parents=True, exist_ok=True)
    args.sha_file.write_text(f"{current_sha}\n", encoding="utf-8")

    print(f"SHA actual: {current_sha}")
    print(f"SHA previa: {previous_sha or '(sin valor previo)'}")
    print(f"Hubo cambios: {'true' if changed else 'false'}")

    github_output = args.github_output
    if github_output is None:
        output_env = os.getenv("GITHUB_OUTPUT", "").strip()
        if output_env:
            github_output = Path(output_env)

    if github_output is not None:
        with github_output.open("a", encoding="utf-8") as f:
            f.write(f"data_sha={current_sha}\n")
            f.write(f"previous_sha={previous_sha}\n")
            f.write(f"changed={'true' if changed else 'false'}\n")


if __name__ == "__main__":
    main()
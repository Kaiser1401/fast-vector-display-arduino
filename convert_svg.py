import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def extract_svg_points(filename):
    root = ET.parse(filename).getroot()

    # SVG path commands and floating-point numbers
    token_re = re.compile(
        r"[A-Za-z]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?"
    )

    points = []
    move_indices = []

    for elem in root.iter():
        if elem.tag.split("}")[-1] != "path":
            continue

        tokens = token_re.findall(elem.get("d", ""))
        i = 0
        cmd = None
        x = y = 0.0
        first_pair = False

        while i < len(tokens):
            if tokens[i].isalpha():
                cmd = tokens[i]
                i += 1

                if cmd in ("Z", "z"):
                    continue

                if cmd not in ("M", "m", "L", "l"):
                    raise ValueError(
                        f"Unsupported SVG command {cmd!r}. "
                        "Convert curves to lines first."
                    )

                first_pair = cmd in ("M", "m")

            if cmd is None or i + 1 >= len(tokens):
                raise ValueError("Incomplete SVG coordinate pair")

            if tokens[i].isalpha() or tokens[i + 1].isalpha():
                raise ValueError("Expected coordinate pair")

            a = float(tokens[i])
            b = float(tokens[i + 1])
            i += 2

            if cmd.islower():
                x += a
                y += b
            else:
                x, y = a, b

            if first_pair:
                move_indices.append(len(points) // 2)
                first_pair = False
                # Extra coordinate pairs after M/m are line commands.
                cmd = "l" if cmd == "m" else "L"

            points.extend([x, y])

    return points, move_indices


def main():
    if len(sys.argv) != 2:
        print(f"Usage: python {Path(sys.argv[0]).name} input.svg")
        sys.exit(1)

    svg_path = Path(sys.argv[1])
    points, moves = extract_svg_points(svg_path)

    coordinates = ", ".join(map(str, points))
    liftlist = ", ".join(map(str, moves))

    print(f"// {svg_path.name}")
    print(f"#define USER_PATTERN{{ {coordinates} }}")
    print(f"const fb_idx_t LIFTLIST[] = {{ {liftlist} }};")
    print(f"#define LIFTCOUNT {len(moves)}")


if __name__ == "__main__":
    main()

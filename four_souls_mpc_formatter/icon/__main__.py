from pathlib import Path
from PIL import Image


def main():
    create_icon()


def create_icon():
    script_dir = Path(__file__).parent
    input_filename = script_dir / "../../assets/images/LOGO.png"
    output_filename = script_dir / "../../logo.ico"

    icon_sizes = [
        (16, 16),
        (24, 24),
        (32, 32),
        (48, 48),
        (64, 64),
        (128, 128),
        (255, 255),
    ]

    img = Image.open(input_filename.resolve())
    img.save(output_filename.resolve(), sizes=icon_sizes)


if __name__ == "__main__":
    main()

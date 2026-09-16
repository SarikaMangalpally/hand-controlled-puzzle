"""Standalone native image chooser. Do not import Pygame into this process."""

import json
import tkinter
from tkinter.filedialog import askopenfilename


def main():
    root = tkinter.Tk()
    root.withdraw()
    try:
        selected = askopenfilename(parent=root, title="Choose a puzzle picture",
                                  filetypes=[("Pictures", "*.png *.jpg *.jpeg *.bmp *.webp")])
        print(json.dumps(selected or None))
    finally:
        root.destroy()


if __name__ == '__main__':
    main()

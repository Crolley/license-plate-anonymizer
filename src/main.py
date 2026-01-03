import tkinter as tk
from model import LicensePlateProcessor
from view import LicensePlateBlurView
from controller import LicensePlateBlurController


def main():
    root = tk.Tk()
    model = LicensePlateProcessor(model_path="../license_plate_detector.pt")
    view = LicensePlateBlurView(root)
    controller = LicensePlateBlurController(model, view)
    controller.run()


if __name__ == "__main__":
    main()

# Import the libraries we need
import numpy as np
import requests
import tkinter as tk

from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox

graph_canvas = None

# formatting/designing the colors on all the parts of the app
background_color = "#1f2a36"   # dark blue background
panel_color = "#2f3e4e"        # slightly lighter blue panels
text_color = "#e8f0f8"         # white/blue text
accent_color = "#4da3ff"       # blue accents (buttons/highlights)
button_color = "#dce6f2"       # light button

# GAS API INFO (where we get gas prices from)
EIA_API_KEY = "VPd9Slnh73WaHbzlvBPgq1o4J83Fy7sJfo062fnF"
EIA_SERIES = "EMM_EPM0_PTE_SCA_DPG"
EIA_URL = "https://api.eia.gov/v2/petroleum/pri/gnd/data/"



# FUNCTION: GET GAS PRICE FROM INTERNET
def get_california_gas_price():
    params = {
        "api_key": EIA_API_KEY,
        "frequency": "weekly",
        "data[0]": "value",
        "facets[series][]": EIA_SERIES,
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "offset": 0,
        "length": 1
    }

    response = requests.get(EIA_URL, params=params)
    response.raise_for_status()
    data = response.json()
    return float(data["response"]["data"][0]["value"])

# FUNCTION: CALCULATE DIFFERENT GAS GRADES
def calculate_grades(base_price):
    return {
        "87": base_price,
        "89": base_price + 0.20,
        "91": base_price + 0.40
    }

# FUNCTION: COMBINE ZIP + PRICE INFO
def estimate_prices(zip_code):
    base_price = get_california_gas_price()
    grades = calculate_grades(base_price)
    return zip_code, base_price, grades

# FUNCTION: sample gas station data
def get_gas_station_data():
    return [
        ("Gulf", "Marina", 5.95),
        ("7-Eleven", "Marina", 6.19),
        ("Chevron", "Marina", 6.59),
        ("Shell", "Marina", 6.59)
    ]

# update station section
def update_station_section():
    stations = get_gas_station_data()
    station_lines = []

    for i, (name, location, price) in enumerate(stations, start=1):
        station_lines.append(f"{i}. {name}")
        station_lines.append(f"   Location: {location}")
        station_lines.append(f"   Price: ${price:.2f} per gallon\n")

    stations_text.set("\n".join(station_lines))

# BIGGER, AUTO-ADVANCING INPUT POPUPS
def ask_value(title, prompt, callback):
    win = tk.Toplevel(root)
    win.title(title)
    win.geometry("400x200")
    win.grab_set()

    tk.Label(win, text=prompt, font=("Times New Roman", 14)).pack(pady=20)

    entry = tk.Entry(win, font=("Times New Roman", 14))
    entry.pack(pady=10)
    entry.focus_set()

    def submit():
        value = entry.get().strip()
        if value == "":
            messagebox.showwarning("Missing Input", "Please enter a value.")
            return
        win.destroy()
        callback(value)

    tk.Button(win, text="OK", font=("Times New Roman", 14), command=submit).pack(pady=10)
    win.bind("<Return>", lambda event: submit())

# CLEAR ALL FUNCTION
def clear_all():
    global graph_canvas

    entry_zip.delete(0, tk.END)
    selected_fraction.set("0")
    draw_segments()

    result_text.set("")
    stations_frame.pack_forget()
    stations_text.set("")

    if graph_canvas:
        graph_canvas.get_tk_widget().destroy()
        graph_canvas = None

# MAIN BUTTON FUNCTION
def on_submit():
    global graph_canvas

    zip_code = entry_zip.get().strip()

    if len(zip_code) != 5 or not zip_code.isdigit():
        messagebox.showerror("Invalid ZIP", "Enter a valid ZIP.")
        return

    if selected_fraction.get() == "0":
        messagebox.showerror("Missing Selection", "Select fuel level.")
        return

    try:
        zip_result, base_price, grades = estimate_prices(zip_code)

        gas_data = sorted(grades.items(), key=lambda item: item[1])
        labels = [i[0] for i in gas_data]
        prices = [i[1] for i in gas_data]

        fig, ax = plt.subplots(figsize=(3.8, 2.8))
        fig.patch.set_facecolor("white")
        ax.set_facecolor("#f7f9fb")

        bars = ax.barh(labels, prices, color=['#42f581', '#f5e642', '#f55a42'])
        ax.invert_yaxis()
        ax.set_xlabel("Price")
        ax.set_title("Gas Price Comparison")

        ax.bar_label(bars, fmt=" $%.02f")

        if graph_canvas:
            graph_canvas.get_tk_widget().destroy()

        graph_canvas = FigureCanvasTkAgg(fig, master=bottom_frame)
        graph_canvas.draw()
        graph_canvas.get_tk_widget().pack(side="right", padx=10, fill="both", expand=True)

        fraction_label = selected_fraction.get()
        fraction = fraction_values[fraction_label]

        def after_tank(value):
            try:
                tank_size = float(value)
            except ValueError:
                messagebox.showerror("Invalid Input", "Tank size must be a number.")
                ask_value("Tank", "Enter tank size in gallons:", after_tank)
                return

            def after_distance(dist):
                try:
                    distance = float(dist)
                except ValueError:
                    messagebox.showerror("Invalid Input", "Distance must be a number.")
                    ask_value("Distance you will travel", "Miles:", after_distance)
                    return

                def after_mpg(mpg_value):
                    try:
                        mpg = float(mpg_value)
                    except ValueError:
                        messagebox.showerror("Invalid Input", "MPG must be a number.")
                        ask_value("MPG", "Car MPG:", after_mpg)
                        return

                    estimated_cost = prices[0] * tank_size * fraction
                    premium_cost = prices[-1] * tank_size * fraction
                    savings = premium_cost - estimated_cost

                    trip_text = "Trip not calculated."
                    if mpg > 0:
                        trip_cost = (distance / mpg) * prices[0]
                        trip_text = f"Estimated Trip Cost: ${trip_cost:.2f}"

                    result_text.set(
                        f"ZIP: {zip_result}\n"
                        f"Gas Price: ${base_price:.3f}\n"
                        f"Fill Cost: ${estimated_cost:.2f}\n"
                        f"Savings: ${savings:.2f}\n\n"
                        f"{trip_text}\n\n"
                        f"Recommendation: Regular 87 is cheapest unless your car needs premium."
                    )

                    update_station_section()
                    stations_frame.pack(side="left", padx=10, pady=5, fill="both", expand=False)

                ask_value("MPG", "Car MPG:", after_mpg)

            ask_value("Distance you will travel", "Miles:", after_distance)

        ask_value("Tank", "Enter tank size in gallons:", after_tank)

    except Exception as e:
        messagebox.showerror("Error", str(e))

# GUI SETUP
if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg=background_color)
    root.title("Gas Estimator")
    root.geometry("1100x800")

    selected_fraction = tk.StringVar(value="0")

    fraction_values = {
        "1/4": 0.25,
        "1/2": 0.50,
        "3/4": 0.75,
        "Full": 1.00
    }

    fraction_colors = {
        "1/4": "#ff4d4d",
        "1/2": "#ffd633",
        "3/4": "#b3ff66",
        "Full": "#33cc33"
    }

    tk.Label(
        root,
        text="Enter ZIP Code:",
        font=("Times New Roman", 15, "bold"),
        bg=background_color,
        fg=text_color
    ).pack(pady=10)

    entry_zip = tk.Entry(
        root,
        font=("Times New Roman", 15),
        width=10,
        bg="#1f1f1f",
        fg="white",
        insertbackground="white"
    )
    entry_zip.pack()

    tk.Label(
        root,
        text="Select Fuel Level:",
        font=("Times New Roman", 14, "bold"),
        bg=background_color,
        fg=text_color
    ).pack(pady=10)

    fuel_canvas = tk.Canvas(root, width=300, height=50, bg=background_color, highlightthickness=0)
    fuel_canvas.pack()

    segment_width = 75
    segment_height = 40

    def draw_segments():
        fuel_canvas.delete("all")
        for i, label in enumerate(["1/4", "1/2", "3/4", "Full"]):
            x1 = i * segment_width
            x2 = x1 + segment_width
            color = fraction_colors[label] if selected_fraction.get() == label else "#d9d9d9"
            fuel_canvas.create_rectangle(x1, 5, x2, segment_height, fill=color, outline="black")
            fuel_canvas.create_text(
                (x1 + x2) / 2,
                segment_height / 2,
                text=label,
                fill="black",
                font=("Times New Roman", 14, "bold")
            )

    def click_event(event):
        index = event.x // segment_width
        labels = ["1/4", "1/2", "3/4", "Full"]
        if 0 <= index < 4:
            selected_fraction.set(labels[index])
            draw_segments()

    fuel_canvas.bind("<Button-1>", click_event)
    draw_segments()

    # BUTTON FRAME (Get Prices + Clear All)
    button_frame = tk.Frame(root, bg=background_color)
    button_frame.pack(pady=15)

    tk.Button(
        button_frame,
        text="Get Prices",
        font=("Times New Roman", 14, "bold"),
        bg="#7CFC98",
        fg="black",
        activebackground="#5fd67a",
        activeforeground="black",
        relief="raised",
        bd=3,
        padx=12,
        pady=5,
        command=on_submit
    ).pack(side="left", padx=10)

    tk.Button(
        button_frame,
        text="Clear All",
        font=("Times New Roman", 14, "bold"),
        bg="#ff6666",
        fg="black",
        activebackground="#cc5252",
        activeforeground="white",
        relief="raised",
        bd=3,
        padx=12,
        pady=5,
        command=clear_all
    ).pack(side="left", padx=10)

    result_text = tk.StringVar()
    tk.Label(
        root,
        textvariable=result_text,
        font=("Times New Roman", 15),
        bg=background_color,
        fg=text_color,
        justify="center"
    ).pack()

    bottom_frame = tk.Frame(root, bg=background_color)
    bottom_frame.pack(pady=10, padx=20, fill="both", expand=True)

    stations_frame = tk.LabelFrame(
        bottom_frame,
        text="Cheapest Nearby Gas Stations",
        font=("Times New Roman", 14, "bold"),
        bg=panel_color,
        fg=text_color,
        padx=10,
        pady=10
    )
    stations_frame.pack_forget()

    stations_text = tk.StringVar()

    tk.Label(
        stations_frame,
        textvariable=stations_text,
        font=("Times New Roman", 15),
        bg=panel_color,
        fg=text_color,
        justify="left",
        anchor="w"
    ).pack(fill="both", expand=True)

    root.mainloop()
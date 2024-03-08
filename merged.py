import tkinter as tk
from tkinter import ttk
import serial
import pynmea2
import cv2
from PIL import Image, ImageTk
import pyproj
from ultralytics import YOLO

# Initialize the YOLO model
model = YOLO("last.pt")

def object_detection(root, video_label):
    # Initialize the video capture device (webcam)
    cap = cv2.VideoCapture(0)
    # Set the frame dimensions
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1260)

    def detect_objects():
        ret, frame = cap.read()
        if not ret:
            return

        # Perform object detection
        results_list = model(frame)

        for results in results_list:
            # Access the original image from the Results object
            original_img = results.orig_img

            # Convert the original image to ImageTk format
            result_img = Image.fromarray(original_img)
            result_img = ImageTk.PhotoImage(image=result_img)

            # Update the label with the new image
            video_label.img = result_img
            video_label.config(image=result_img)

            # Update the GUI
            root.update()

        # Schedule the function to run again after 50 milliseconds
        root.after(50, detect_objects)

    # Start detecting objects
    detect_objects()

def get_grid_reference(latitude, longitude):
    # Define the coordinate systems
    wgs84 = pyproj.CRS("epsg:4326")  # WGS84 coordinate system for latitude and longitude
    osgb36 = pyproj.CRS("epsg:27700")  # Ordnance Survey GB coordinate system

    # Create transformer
    transformer = pyproj.Transformer.from_crs(wgs84, osgb36, always_xy=True)

    # Transform latitude and longitude to Ordnance Survey grid reference
    easting, northing = transformer.transform(longitude, latitude)

    # Format the easting and northing to have 5 digits each
    easting_int = int(easting)
    northing_int = int(northing)

    if easting_int < 0 or northing_int < 0:
        # No valid data available, set os_index_letter to "AA"
        os_index_letter = "AA"
    else:
        # Calculate os_index_letter
        os_letter = str(easting_int // 100000) + str(northing_int // 100000)
        os_index = {
            "00": "SV", "10": "SW", "20": "SX", "30": "SY", "40": "SZ", "50": "TV", "60": "TW",
            "01": "SQ", "11": "SR", "21": "SS", "31": "ST", "41": "SU", "51": "TQ", "61": "TR",
            "02": "SL", "12": "SM", "21": "SN", "32": "SO", "42": "SP", "52": "TL", "62": "TM",
            "03": "SF", "13": "SG", "22": "SH", "33": "SJ", "43": "SK", "53": "TF", "63": "TG",
            "04": "SA", "14": "SB", "24": "SC", "34": "SD", "44": "SE", "54": "TA", "64": "TB",
            "05": "NV", "15": "NW", "25": "NX", "35": "NY", "45": "NZ", "55": "OV", "65": "OW",
            "06": "NQ", "16": "NR", "26": "NS", "36": "NT", "46": "NU", "56": "OQ", "66": "OR",
            "07": "NL", "17": "NM", "27": "NN", "37": "NO", "47": "NP", "57": "OL", "67": "OM",
            "08": "NF", "18": "NG", "28": "NH", "38": "NJ", "48": "NK", "58": "OF", "68": "OG",
            "09": "NA", "19": "NB", "29": "NC", "39": "ND", "49": "NE", "59": "OA", "69": "OB",
            "010": "HV", "110": "HW", "210": "HX", "310": "HY", "410": "HZ", "510": "IV", "610": "IW",
            "011": "HQ", "111": "HR", "211": "HS", "311": "HT", "411": "HU", "511": "IQ", "611": "IR",
            "012": "HL", "112": "HM", "212": "HN", "312": "HO", "412": "HP", "512": "IL", "612": "IM",
        }
        os_index_letter = os_index[os_letter]

    easting_remain = str(easting_int % 100000)
    northing_remain = str(northing_int % 100000)

    # Combine easting and northing to form a full 8-figure OS grid reference
    full_grid_ref = os_index_letter, easting_remain[:4], northing_remain[:4]

    return full_grid_ref

def read_gps_data(root, tree, serial_port="/dev/cu.PL2303G-USBtoUART2240", baudrate=4800):
    def update_gps_data():
        with serial.Serial(serial_port, baudrate, timeout=1) as ser:
            line = ser.readline().decode('latin-1').strip()
            if line.startswith('$GNGGA'):
                try:
                    data = pynmea2.parse(line)
                    latitude = data.latitude
                    longitude = data.longitude
                    altitude = data.altitude
                    timestamp = data.timestamp
                    grid_ref = get_grid_reference(latitude, longitude)

                    tree.insert("", "end", text=timestamp, values=(latitude, longitude, altitude, grid_ref))
                  
                    # Remove oldest item if there are more than 1 items in the Treeview
                    if len(tree.get_children()) > 1:
                        tree.delete(tree.get_children()[0])

                except pynmea2.ParseError as e:
                    print(f"Error parsing NMEA sentence: {e}")

        root.after(500, update_gps_data)  # Update every 500 milliseconds

    update_gps_data()

def on_closing(cap, root):
    cap.release()
    root.destroy()

# Create the main application window
app = tk.Tk()
app.title("EAGLE EYE")
app.geometry("1200x1200")  # Set window width and height

# Create a frame for the main content
main_frame = tk.Frame(app)
main_frame.pack(fill="both", expand=True)

# Create a frame for the GPS data
gps_data_frame = tk.Frame(main_frame, width=40, height=10)  # Adjust width and height as needed
gps_data_frame.pack(side=tk.BOTTOM, pady=30)  # Position GPS data frame below the camera feed

# Create Treeview widget
tree = ttk.Treeview(gps_data_frame)
tree["columns"] = ("latitude", "longitude", "altitude", "grid_ref")
tree.heading("#0", text="Timestamp")
tree.heading("latitude", text="Latitude")
tree.heading("longitude", text="Longitude")
tree.heading("altitude", text="Altitude")
tree.heading("grid_ref", text="Grid Reference")
tree.pack(fill=tk.BOTH, expand=True)  # Fill the entire GPS frame

# Create a label to display the video feed
video_label = tk.Label(main_frame)
video_label.pack(expand=True)  # Expand to fill available space

# Run the GPS data reading function
read_gps_data(app, tree)

# Call the object detection function when the application starts
object_detection(app, video_label)


# Function to release the video capture device when window is closed
app.protocol("WM_DELETE_WINDOW", lambda: on_closing(cap, app))

def close_app(event):
    if event.char == 'q':
        on_closing(cap, app)

# Bind the key event to close the app
app.bind('<Key>', close_app)

# Run the application
app.mainloop()

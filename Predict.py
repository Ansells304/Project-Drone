
from ultralytics import YOLO

model = YOLO("last.pt")

#For image detection
#model.predict(source = 0, show=True, save=True, hide_labels=True, hide_conf=True, conf=0.5, save_txt=True, save_crop=True, line_thickness=2, show_labels = True)

#For video detection
#model.predict(source = "1.mp4", show=True, save=True, hide_labels=False, hide_conf=False, conf=0.5, save_txt=True, save_crop=False, line_thickness=2)

#For webcam detection
model.predict(source = 0, show=True, save=True, hide_labels=False, hide_conf=False, conf=0.5, save_txt=True, save_crop=False, line_thickness=2, show_labels = True)

#Export model
#model.export(format="onnx")

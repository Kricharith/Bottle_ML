import cv2
import numpy as np
from ultralytics import YOLO
import torch
import time
import serial

# ตรวจสอบว่ามี GPU หรือไม่
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Using device: {device}")

# โหลดโมเดล YOLO
model_path = "../../model/best50x.pt"
model = YOLO(model_path).to(device)
model.fuse()

categories = {0: 'Bottle-Ng Label', 1: 'Bottle-Ng Level', 2: 'Bottle-good Label', 3: 'Bottle-good Level'}

count_goodLevel = 0
count_not_goodLevel = 0
count_goodLabel = 0
count_not_goodLabel = 0

count_goodBottle = 0
count_not_goodBottle = 0

category_list = []

serial_port = None
# ------------------------------------------------------------------------------
try:
    serial_port = serial.Serial(port='COM3', baudrate=115200, timeout=.2)
except:
    print("Serial port not found")
# ------------------------------------------------------------------------------

# send data to mcu
def send_data_to_mcu(data):
    try:
        global serial_port
        serial_port.write(data.encode())
        print(f"Sent: {data}")
    except:
        print("Serial port not found")
def receive_data_from_mcu():
    global serial_port
    while True:
        if serial_port.in_waiting > 0:
            received_data = serial_port.readline().decode().strip()
            print(f"Received: {received_data}")
            break

# ฟังก์ชันสำหรับประมวลผลภาพและเพิ่มข้อมูลลงในภาพ
def process_image(image_path, model):
    global category_list # เรียกใช้ตัวแปร global

    # โหลดภาพ
    img = cv2.imread(image_path)
    
    # ส่งภาพเข้าโมเดล
    results = model(img)
    
    # วนลูปเพื่อแสดงผลลัพธ์ของแต่ละวัตถุ
    for detection in results:
        boxes = detection.boxes.cpu().numpy()
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            confidence = box.conf[0] #
            class_id = box.cls[0]
            category_name = categories.get(int(class_id), 'Unknown')
            if confidence > 0.9:
                category_list.append(category_name)  # เพิ่ม current_category เข้าไปใน List
                #----------------------------------------------------------
                if category_name in ['Bottle-Ng Label','Bottle-Ng Level']:
                    color = (0, 0, 255)  # Red for 'Not Good'
                else:
                    color = (0, 255, 0)  # Green for 'Good'
                #----------------------------------------------------------

                # Draw rectangle around detected object
                cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                
                # Put category name and confidence on frame
                cv2.putText(img, f"{category_name}: {confidence:.2f}", (int(x1), int(y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                
                # Put 'Good' or 'Not Good' label
                # cv2.putText(img, label_text, (int(x1), int(y2 + 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    checkAndSendMcu(category_list)
    category_list = []  

    # แสดงจำนวนของ Good และ Not Good ในมุมขวามือบนของเฟรม
    cv2.putText(img, f"GoodLevel: {count_goodLevel}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    cv2.putText(img, f"NotgoodLevel: {count_not_goodLevel}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    cv2.putText(img, f"GoodLabel: {count_goodLabel}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    cv2.putText(img, f"NotgoodLabel: {count_not_goodLabel}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    cv2.putText(img, f"goodBottle: {count_goodLevel}", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    cv2.putText(img, f"NotgoodBottle: {count_not_goodLevel}", (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    
    return img

def checkAndSendMcu(category_list):
    global count_goodLevel, count_not_goodLevel, count_goodLabel, count_not_goodLabel, count_goodBottle, count_not_goodBottle
    print("Showwwwwwwwwwwwwwwwwwww")
    if 'Bottle-Ng Level' in category_list and 'Bottle-Ng Label' in category_list:
        count_not_goodLevel += 1
        count_not_goodLabel += 1
        count_not_goodBottle +=1
        print("------------")
        print("---Kick1----")
        print("------------")
        send_data_to_mcu("NG")
    elif 'Bottle-Ng Level' in category_list and 'Bottle-good Label' in category_list:
        count_not_goodLevel += 1
        count_goodLabel += 1
        count_not_goodBottle +=1
        print("------------")
        print("---Kick2----")
        print("------------")
        send_data_to_mcu("NG")
    elif 'Bottle-good Level' in category_list and 'Bottle-Ng Label' in category_list:
        count_goodLevel += 1
        count_not_goodLabel += 1
        count_not_goodBottle +=1
        print("------------")
        print("----Kick2----")
        print("------------")
        send_data_to_mcu("NG")
    elif 'Bottle-good Level' in category_list and 'Bottle-good Label' in category_list:
        count_goodLevel += 1
        count_goodLabel += 1
        count_goodBottle += 1
        print("------------")
        print("--Not kick--")
        print("------------")
        send_data_to_mcu("G")
    elif 'Bottle-Ng Level' in category_list :
        count_not_goodBottle +=1
        print("------------")
        print("----Kick hard Best case----")
        print("------------")
        send_data_to_mcu("NG")
    elif 'Bottle-Ng Label' in category_list :
        count_not_goodBottle +=1
        print("------------")
        print("----Kick hard Best case----")
        print("------------")
        send_data_to_mcu("NG")
    elif 'Bottle-good Level' in category_list :
        count_not_goodBottle +=1
        print("------------")
        print("----Kick hard Best case----")
        print("------------")
        send_data_to_mcu("NG")
    elif 'Bottle-good Label' in category_list :
        count_not_goodBottle +=1
        print("------------")
        print("----Kick hard Best case----")
        print("------------")
        send_data_to_mcu("NG")
# เปิดการเชื่อมต่อกับกล้อง
cap = cv2.VideoCapture(0)  # เลข 0 หมายถึงกล้องตัวแรกที่เชื่อมต่ออยู่

if not cap.isOpened():
    print("ไม่สามารถเปิดกล้องได้")
    exit()

while True:
    # อ่านเฟรมจากกล้อง
    ret, frame = cap.read()
    if not ret:
        print("ไม่สามารถอ่านเฟรมจากกล้องได้")
        break

    # แสดงเฟรม
    cv2.imshow('Camera', frame)

    # รอรับคีย์บอร์ดอินพุต
    key = cv2.waitKey(1) & 0xFF

    # ถ้ากด 'C' ให้ถ่ายภาพและวิเคราะห์
    if key == ord('c') or key == ord('C'):
        image_path = 'captured_image.jpg'
        # บันทึกภาพเป็นไฟล์
        cv2.imwrite(image_path, frame)
        print("ถ่ายภาพสำเร็จและบันทึกเป็น 'captured_image.jpg'")

        # ประมวลผลภาพด้วยโมเดลและได้รับภาพที่มีข้อมูลเพิ่มลงไป
        processed_image = process_image(image_path, model)

        # แสดงภาพที่ผ่านการประมวลผล
        cv2.imshow('Camera', processed_image)

        # รอ 1 วินาที
        cv2.waitKey(2000)
    elif serial_port !=None and serial_port.in_waiting > 0 :
        received_data = serial_port.readline().decode().strip()
        print(f"Received: {received_data}")
        image_path = 'captured_image.jpg'
        # บันทึกภาพเป็นไฟล์
        cv2.imwrite(image_path, frame)
        print("ถ่ายภาพสำเร็จและบันทึกเป็น 'captured_image.jpg'")
        # ประมวลผลภาพด้วยโมเดลและได้รับภาพที่มีข้อมูลเพิ่มลงไป
        processed_image = process_image(image_path, model)
        # แสดงภาพที่ผ่านการประมวลผล
        cv2.imshow('Camera', processed_image)
        # รอ 1 วินาที
        cv2.waitKey(2000)
    # ถ้ากด 'Q' ให้ปิดโปรแกรม
    elif key == ord('q') or key == ord('Q'):
        print("ปิดโปรแกรม")
        break

# ปิดการเชื่อมต่อกับกล้องและปิดหน้าต่าง
cap.release()
cv2.destroyAllWindows()
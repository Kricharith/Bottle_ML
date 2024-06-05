import cv2
import numpy as np
from ultralytics import YOLO
import torch
import time
import serial
#pip install pyserial

# ตรวจสอบว่ามี GPU หรือไม่
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Using device: {device}")

# โหลดโมเดล YOLO
model_path = "best50x.pt"
model = YOLO(model_path).to(device)
model.fuse()

categories = {0: 'Bottle-Ng Label', 1: 'Bottle-Ng Level', 2: 'Bottle-good Label', 3: 'Bottle-good Level'}

count_goodLevel = 0
count_not_goodLevel = 0
count_goodLabel = 0
count_not_goodLabel = 0

count_goodBottle = 0
count_not_goodBottle = 0

category_list_frame1 = []
category_list_frame2 = []

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
def process_image(frame, image_path, model):
    global category_list_frame1 # เรียกใช้ตัวแปร global
    global category_list_frame2 # เรียกใช้ตัวแปร global
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
            if confidence > 0.7:
                if frame == "frame1":
                    category_list_frame1.append(category_name)  # เพิ่ม current_category เข้าไปใน List
                elif frame == "frame2":
                    category_list_frame2.append(category_name)  # เพิ่ม current_category เข้าไปใน List
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

    # checkAndSendMcu(category_list)
    # category_list_frame1 = []  
    # category_list_frame2 = []  
    # แสดงจำนวนของ Good และ Not Good ในมุมขวามือบนของเฟรม
    cv2.putText(img, f"GoodLevel: {count_goodLevel}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    cv2.putText(img, f"NotgoodLevel: {count_not_goodLevel}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    cv2.putText(img, f"GoodLabel: {count_goodLabel}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    cv2.putText(img, f"NotgoodLabel: {count_not_goodLabel}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    cv2.putText(img, f"goodBottle: {count_goodLevel}", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    cv2.putText(img, f"NotgoodBottle: {count_not_goodLevel}", (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    
    return img
def compare_category_lists(category_list_frame1,category_list_frame2):
    result = set()
    intersection = set()
    category_set_frame1 = set()
    category_set_frame2 = set()
    difference_frame1 = set()
    difference_frame2 = set()
    difference = set()
    print("-----------------------------------------")
    print("category_list_frame1",category_list_frame1)
    print("category_list_frame2",category_list_frame2)
    print("-----------------------------------------")
    category_set_frame1 = set(category_list_frame1)
    category_set_frame2 = set(category_list_frame2)
    if len(category_set_frame1) >= 3 or len(category_set_frame2) >= 3:
        result = {'Bottle-Ng Level', 'Bottle-good Label'}
    else:
        # เช็คว่ามีข้อมูลเพียงตัวเดียวใน set หนึ่งหรือไม่
        if len(category_set_frame1) == 1 or len(category_set_frame2) == 1:
            # ถ้ามีให้เก็บทั้ง intersection และ difference ในตัวแปรเดียวกัน
            intersection = category_set_frame1.intersection(category_set_frame2)
            difference_frame1 = category_set_frame1.difference(category_set_frame2)
            difference_frame2 = category_set_frame2.difference(category_set_frame1)
            difference = difference_frame1.union(difference_frame2)
            print("case 1 มีข้อมูลเพียงตัวเดียว")
            print("ข้อมูลที่ตรงกัน:", intersection)
            print("ข้อมูลที่ไม่ตรงกัน:", difference)
            intersection.update(difference)
            result = intersection
            print("result", result)
        else:
        # ถ้าไม่ใช่ให้ดำเนินการเช็คเหมือนเดิม
            if category_set_frame1 == category_set_frame2:
                print("case 2 ข้อมูลที่ตรงกันทั้งหมด")
                intersection = category_set_frame1.intersection(category_set_frame2)
                print("ข้อมูลที่ตรงกัน:", intersection)
            else:
                print("case 3 ข้อมูลที่ตรงกันไม่ทั้งหมด")
                difference_frame1 = category_set_frame1.difference(category_set_frame2)
                difference_frame2 = category_set_frame2.difference(category_set_frame1)
                difference = difference_frame1.union(difference_frame2)
                if "Bottle-Ng Label" in difference:
                    intersection = category_set_frame1.intersection(category_set_frame2)
                    print("ข้อมูลที่ตรงกัน:", intersection)
                    print("ข้อมูลที่ไม่ตรงกัน:", difference)
                    intersection.add("Bottle-Ng Label")
                    result = intersection  # เก็บค่า intersection ที่อัปเดตแล้วในตัวแปร result
                    print("result", result)
                elif "Bottle-Ng Level" in difference:
                    intersection = category_set_frame1.intersection(category_set_frame2)
                    print("ข้อมูลที่ตรงกัน:", intersection)
                    print("ข้อมูลที่ไม่ตรงกัน:", difference)
                    intersection.add("Bottle-Ng Level")
                    result = intersection  # เก็บค่า intersection ที่อัปเดตแล้วในตัวแปร result
                    print("result", result)
    checkAndSendMcu(result)
    result.clear()
    intersection.clear()
    category_set_frame1.clear()
    category_set_frame2.clear()
    difference_frame1.clear()
    difference_frame2.clear()
    difference.clear()
    

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

# สร้างสรรพสถานการเชื่อมต่อกับกล้องแรก
cap = cv2.VideoCapture(0)  # เลข 0 หมายถึงกล้องตัวแรกที่เชื่อมต่ออยู่
if not cap.isOpened():
    print("ไม่สามารถเปิดกล้องได้")
    exit()

# สร้างสรรพสถานการเชื่อมต่อกับกล้องที่สอง
cap2 = cv2.VideoCapture(1)  # เลข 1 หมายถึงกล้องที่สองที่เชื่อมต่ออยู่
if not cap2.isOpened():
    print("ไม่สามารถเปิดกล้องที่สองได้")
    exit()

while True:
    # อ่านเฟรมจากกล้องแรก
    ret, frame = cap.read()
    if not ret:
        print("ไม่สามารถอ่านเฟรมจากกล้องแรกได้")
        break

    # แสดงเฟรม
    cv2.imshow('Camera1', frame)

    # อ่านเฟรมจากกล้องที่สอง
    ret2, frame2 = cap2.read()
    if not ret2:
        print("ไม่สามารถอ่านเฟรมจากกล้องที่สองได้")
        break

    # แสดงเฟรม
    cv2.imshow('Camera2', frame2)

    # รอรับคีย์บอร์ดอินพุต
    key = cv2.waitKey(1) & 0xFF
    if key == ord('r') or key == ord('R'):
        count_goodLevel = 0 
        count_not_goodLevel = 0 
        count_goodLabel = 0
        count_not_goodLabel = 0 
        count_goodBottle = 0 
        count_not_goodBottle = 0
    # ถ้ากด 'C' ให้ถ่ายภาพและประมวลผล
    if key == ord('c') or key == ord('C') or (serial_port != None and serial_port.in_waiting > 0):
        image_path1 = 'captured_image1.jpg'
        image_path2 = 'captured_image2.jpg'
        
        # บันทึกภาพจากกล้องแรก
        cv2.imwrite(image_path1, frame)
        print("ถ่ายภาพและบันทึกเป็น 'captured_image1.jpg'")
        
        # บันทึกภาพจากกล้องที่สอง
        cv2.imwrite(image_path2, frame2)
        print("ถ่ายภาพและบันทึกเป็น 'captured_image2.jpg'")
        
        # ประมวลผลภาพจากกล้องแรก
        processed_image1 = process_image("frame1",image_path1, model)
        # แสดงภาพที่ผ่านการประมวลผล
        cv2.imshow('Camera1', processed_image1)

        # ประมวลผลภาพจากกล้องที่สอง
        processed_image2 = process_image("frame2",image_path2, model)
        # แสดงภาพที่ผ่านการประมวลผล
        cv2.imshow('Camera2', processed_image2)
        cv2.waitKey(2000)
        compare_category_lists(category_list_frame1, category_list_frame2)
        category_list_frame1 = []
        category_list_frame2 = []
    # ถ้ากด 'Q' ให้ปิดโปรแกรม
    elif key == ord('q') or key == ord('Q'):
        print("ปิดโปรแกรม")
        break

# ปิดการเชื่อมต่อกับกล้องและปิดหน้าต่าง
cap.release()
cap2.release()
cv2.destroyAllWindows()
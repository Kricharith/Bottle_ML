import cv2
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

    # ถ้ากด 'C' ให้ถ่ายภาพ
    if key == ord('c') or key == ord('C'):
        # บันทึกภาพเป็นไฟล์
        cv2.imwrite('captured_image.jpg', frame)
        print("ถ่ายภาพสำเร็จและบันทึกเป็น 'captured_image.jpg'")

    # ถ้ากด 'Q' ให้ปิดโปรแกรม
    elif key == ord('q') or key == ord('Q'):
        print("ปิดโปรแกรม")
        break

# ปิดการเชื่อมต่อกับกล้องและปิดหน้าต่าง
cap.release()
cv2.destroyAllWindows()
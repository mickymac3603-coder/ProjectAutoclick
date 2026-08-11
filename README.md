# 🖱️ AutoClicker

โปรแกรม Auto Clicker สำหรับ Windows รองรับทั้งการคลิกเมาส์, กดคีย์บอร์ด และคลิกหลายตำแหน่งพร้อมกัน

---

## ⬇️ ดาวน์โหลด (สำหรับผู้ใช้ทั่วไป)

ไปที่ [**Releases**](../../releases/latest) แล้วดาวน์โหลด `AutoClicker.exe`

> ✅ ไม่ต้องติดตั้ง Python หรือโปรแกรมใดๆ เพิ่มเติม — ดับเบิลคลิกแล้วใช้ได้เลย

---

## ✨ ฟีเจอร์

### 🔑 Hotkey
- กำหนดปุ่มคีย์บอร์ดเพื่อเปิด/ปิดการทำงานได้เอง (default: **F6**)
- ทำงานแม้หน้าต่างอื่นอยู่หน้า

### ⚡ ปรับความเร็ว
- ปรับได้ตั้งแต่ **1 – 100 ครั้ง/วินาที**

### 📦 3 โหมดการใช้งาน

| โหมด | การทำงาน |
|------|----------|
| **Mode 1: เมาส์** | คลิกซ้าย/ขวา/กลางที่ตำแหน่ง cursor ปัจจุบัน |
| **Mode 2: Keyboard** | กดปุ่มคีย์บอร์ดซ้ำๆ เป็น sequence วน loop |
| **Mode 3: หลายตำแหน่ง** | คลิกหลายจุดบนหน้าจอตามลำดับ พร้อม overlay ลากวางได้ |

---

## 🛠️ สำหรับ Developer (แก้ไขโค้ด)

### Requirements
- Python 3.8+
- pynput

### วิธีรัน
```bash
git clone https://github.com/YOUR_USERNAME/AutoClicker.git
cd AutoClicker
pip install pynput
python main.py
```

### วิธี Build เป็น .exe
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name AutoClicker main.py
```
ไฟล์จะอยู่ที่ `dist/AutoClicker.exe`

---

## 📁 โครงสร้างโปรเจกต์

```
AutoClicker/
├── main.py          # โค้ดหลัก
├── requirements.txt # dependencies
├── build.bat        # script สร้าง .exe (Windows)
└── README.md
```

---

## 📝 License

MIT License — ใช้งานและแก้ไขได้อย่างอิสระ

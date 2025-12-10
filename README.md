# AI Fabric Defect Detection System

This project implements a **real-time fabric defect detection system** using computer vision and AI.  
It integrates a live camera feed, an AI model (YOLOv8n), and a web interface to visualize and save predictions.

A video describing the use and performance of this project can be found at https://www.youtube.com/watch?v=wq12DnKXmt4

---

## ⭐ Features

- Real-time detection using **YOLOv8n**
- Detects:
  - Holes
  - Seams
  - Stains
  - Loose Threads
  - Warp/Weft Defects
  - No Defect
- Live camera preview with overlays
- Adjustable camera settings:
  - Resolution
  - Image format
  - Recording duration
  - Photos per second (FPS)
- Saves:
  - Raw images
  - YOLO bounding box labels
- Live monitoring:
  - FPS
  - Photo count
  - Total recording time
  - Folder size

---

## 🧰 Installation

### 1. Clone the repo

```bash
git clone <repo-url>
cd defect-detection
```

### 2. Install dependencies

```bash
pip install flask opencv-python ultralytics
```

---

## 🚀 Run

```bash
python app.py
```

Open browser:

```
http://127.0.0.1:5000/
```

---

## 📁 Output

Saved to timestamped folder:

```
photos20250130125959/
├── 20250130130000.jpeg
├── 20250130130000.txt
├── labels.txt
```

YOLO label format:
```
class x_center y_center width height
```

---

## 📊 Dataset Summary

| Defect Type       | Count |
|------------------|------:|
| Holes            |   238 |
| Seams            |   110 |
| Stains           |   337 |
| Loose Threads    |   135 |
| Warp/Weft Defect |   242 |
| No Defect        |   628 |
| **Total Images** | **1261** |


- Dataset hosted on RoboFlow: https://app.roboflow.com/yolo-defect-detection/fabric-defect-detection_2025-tw6ok/11
---

## 🧠 Model

- YOLOv8n
- ~400 epochs
- GPU accelerated

---

## 🧪 Prototype

- Autofocus camera
- Wooden frame
- Fabric samples
- Real-time detection visible in UI

---

## 🛠️ Hardware Requirements

Minimum:
- USB camera
- Laptop/PC with Python

Recommended:
- NVIDIA GPU (RTX 5070 Ti used)

---

## 🏭 Deployment Considerations

- Lighting control
- Industrial framing
- Remote access
- Database storage
- Line response logic (alerts, stop, etc.)

---

## 🔧 Future Work

- Edge device deployment
- Try anomaly detection (EfficientAD)
- Cloud monitoring
- Enhanced UI

---

## 🙌 Acknowledgements

- **Dr. Yalin Dong**
- **University of Akron**
- Industry photo providers
- **Nishi Pawar**

---

## 📚 References

- https://explodingtopics.com/blog/ai-statistics  
- https://joelnadarai.medium.com/the-art-of-choosing-the-right-number-of-images-for-your-computer-vision-project-6e45efd1efbf  
- YOLO docs: https://ultralytics.com

---

## 📝 License

This project is licensed under the MIT License — see the LICENSE file for details.

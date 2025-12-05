AI Fabric Defect Detection System

This project implements a real-time fabric defect detection system using computer vision and AI.
It integrates a live camera feed, an AI model (YOLOv8n), and a web interface to visualize and save predictions.

⭐ Features

Real-time detection using YOLOv8n

Detects:

Holes

Seams

Stains

Loose Threads

Warp/Weft Defects

No Defect

Live camera preview with overlays

Adjustable camera settings:

Resolution

Image format

Recording duration

Photos per second (FPS)

Saves:

Raw images

YOLO bounding box labels

Live monitoring:

FPS

Photo count

Total recording time

Folder size

🧰 Installation
1. Clone the repository
git clone <repo-url>
cd defect-detection

2. Install dependencies
pip install flask opencv-python ultralytics

🚀 Running the Application

Start the Flask server:

python app.py


Then open a browser and go to:

http://127.0.0.1:5000/

📷 Usage
Start Recording

Choose settings:

Resolution

Camera device

Photos per second

Duration (or Indefinite)

Press Start

Images will be saved with timestamps and YOLO labels.

Stop Recording

Click Stop at any time.

📁 Output Structure

Images and labels are stored in a timestamped folder:

photos20250130125959/
├── 20250130130000.jpeg
├── 20250130130000.txt
├── labels.txt


YOLO label format:

class x_center y_center width height

📊 Dataset Summary
Category	Instances
Holes	286
Seams	138
Stains	443
Loose Threads	182
Warp/Weft Defect	263
No Defect	677
Total Images	1415

Dataset managed with Roboflow.

🧠 Model Training

Model: YOLOv8n

Training:

~400 epochs

GPU accelerated

Speed improvement:

CPU: 17.82 hours

GPU: 15.84 minutes

Final model integrated into the live system with strong real-world results.

🧪 Prototype

A physical frame and cloth samples were created to test the system:

USB camera initially

Upgraded 4K autofocus camera for final prototype

Frame mounted above fabric surface

System detects defects in real-time

🛠️ Hardware Requirements

Minimum:

USB camera

Laptop/PC with Python

Optional GPU

Recommended for training:

NVIDIA GPU (example used: RTX 5070 Ti Laptop GPU)

🏭 Deployment Considerations

To deploy on a manufacturing line:

Add automated lighting

Industrial-grade frame

Remote access to interface

Database storage for images

Decision logic for:

Alerts

Line shutdown

Quality control

🔧 Future Improvements

Web-based remote control & monitoring

Edge computing device (Jetson, industrial PC)

Automated sorting/response logic

Expand to anomaly detection (EfficientAD)

Optimize dataset for single-fabric systems

🙌 Acknowledgements

Dr. Yalin Dong – Faculty Advisor

University of Akron

Industry photo providers

Nishi Pawar – teammate

📚 References

https://explodingtopics.com/blog/ai-statistics

https://joelnadarai.medium.com/the-art-of-choosing-the-right-number-of-images-for-your-computer-vision-project-6e45efd1efbf

YOLO design and docs: https://ultralytics.com

📝 License

This project is provided for educational and research purposes.
Deployment in industrial environments requires additional safety and validation.

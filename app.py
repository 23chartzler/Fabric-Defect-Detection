from flask import Flask, render_template, Response, jsonify, request
import cv2
import os
from datetime import datetime
import time
import threading
from queue import Queue
import json
import subprocess
import platform
import atexit
from ultralytics import YOLO

app = Flask("Fabric Defect Detection")

# Function to run on exit
def cleanup():
    print("Closing the application... Releasing resources.")
    cv2.VideoCapture(current_params['camera_device']).release()
    cv2.destroyAllWindows()

# Register cleanup function to be called on exit
atexit.register(cleanup)

# Global variables
camera = None
feed_frame = None
lock = threading.Lock()
recording = False
current_params = {
    'save_format': 'jpeg',
    'camera_device': 0,
    'max_time_interval_minutes': 0.5,
    'photos_per_second': 30,  # Default to 30 photos per second
    'resolution': '480,640'  # height,width format
}
photo_queue = Queue()
photo_queue_user_interface = Queue()
folder_size_queue = Queue()  # New queue for folder size updates
stop_recording = False
unannotated_save_frame = None

model = YOLO('C:\\Users\\AI_student\\Documents\\fabric_defect\\runs\\detect\\v11_yolo8n\\weights\\best.pt')

def initialize_camera():
    global camera
    try:
        #if camera is not None:
            #camera.release()
        if camera is None:
            camera = cv2.VideoCapture(current_params['camera_device'])
            height, width = map(int, current_params['resolution'].split(','))
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        if not camera.isOpened():
            print(f"Failed to open camera device {current_params['camera_device']}")
            camera = None
            return False
            
        # Verify resolution
        actual_width = camera.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
        if abs(actual_width - width) > 10 or abs(actual_height - height) > 10:
            print(f"Failed to set resolution to {width}x{height}")
            camera.release()
            camera = None
            return False
            
        return True
    except Exception as e:
        print(f"Error initializing camera: {str(e)}")
        if camera is not None:
            camera.release()
            camera = None
        return False

def generate_frames():
    global camera, stop_recording, feed_frame

    while True:
        try:
            if camera is None and not initialize_camera():
                time.sleep(0.1)
                continue

            if recording == True and feed_frame is not None:
                frame_display = feed_frame
            else:
                success, unannotated_frame = camera.read()
                if not success:
                    print("Failed to read frame from camera (feed)")
                    camera.release()
                    camera = None
                    time.sleep(0.1)
                    continue
                
                results = model.predict(unannotated_frame, verbose=False)
                # Draw the results on the frame
                frame_display = results[0].plot()
                
            ret, buffer = cv2.imencode('.jpg', frame_display)
            if not ret:
                print("Failed to encode frame")
                continue
                
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
            #time.sleep(0.01) 
                
        except Exception as e:
            print(f"Error in generate_frames: {str(e)}")
            if camera is not None:
                camera.release()
                camera = None
            time.sleep(0.1)
            continue

@app.route('/')
def index():
    return render_template('index.html', params=current_params)

@app.route('/user_interface')
def user_interface():
    return render_template('User Interface.html', params=current_params)


@app.route('/video_feed')
def video_feed():
    response = Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )
    # Add headers to prevent caching
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/start_recording', methods=['POST'])
def start_recording():
    global recording, current_params, stop_recording, camera
    
    # If already recording, don't start a new recording
    if recording:
        return jsonify({"status": "error", "message": "Already recording"})
    
    # Update parameters first
    data = request.get_json()
    current_params.update(data)
    
    # Reset all state
    recording = True
    stop_recording = False
    
    # Clear any existing stats
    while not photo_queue.empty():
        photo_queue.get()
    while not photo_queue_user_interface.empty():
        photo_queue_user_interface.get()
    
    # Create new folder for photos
    timestamp_initial = datetime.now().strftime("%Y%m%d%H%M%S")
    folder_name = f"photos{timestamp_initial}"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    # Start recording in a separate thread
    threading.Thread(target=record_photos, args=(folder_name,)).start()
    
    return jsonify({"status": "success", "message": "Recording started"})

@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    global recording, stop_recording, last_stats
    
    # Stop the recording first
    recording = False
    stop_recording = True

    #now = time.time()
    #while time.time() - now < .3:
        #time.sleep(0.05)
    #photo_queue.put(last_stats)
    # Clear the photo queue
    while not photo_queue.empty():
        photo_queue.get()
    #photo_queue.put(last_stats)

    while not photo_queue_user_interface.empty():
        photo_queue_user_interface.get()
    #photo_queue_user_interface.put(last_stats)

    return jsonify({"status": "success", "message": "Recording stopped"})

def get_folder_size(folder_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            total_size += os.path.getsize(file_path)
    
    # Convert to MB first
    size_mb = total_size / (1024 * 1024)
    
    # If size is >= 1GB, convert to GB
    if size_mb >= 1024:
        return {
            'size': round(size_mb / 1024, 3),
            'unit': 'GB'
        }
    else:
        return {
            'size': round(size_mb, 2),
            'unit': 'MB'
        }

def calculate_folder_size(folder_name):
    while recording:
        try:
            size = get_folder_size(folder_name)
            folder_size_queue.put(size)
            time.sleep(5)  # Calculate every 5 seconds
        except Exception as e:
            print(f"Error calculating folder size: {str(e)}")
            time.sleep(5)  # Wait before retrying

def record_photos(folder_name):
    global recording, current_params, camera, stop_recording, feed_frame, last_stats
    
    i = 0
    max_time_interval_sec = current_params['max_time_interval_minutes'] * 60
    target_fps = current_params['photos_per_second']
    delay = target_fps > 0
    delta_time = .4/target_fps if delay else 0
    last_feed_frame_time = 0
    
    # Variables for FPS control
    adjustment_factor = 0.1  # How quickly to adjust (0.1 = 10% adjustment per update)
    min_delta = 0 if delay else 0  # Allow going 50% faster to catch up 1/(target_fps * 1.5)
    max_delta = 1/(target_fps * 0.5) if delay else 0  # Don't go slower than half speed
    
    last_photo_time = time.time()
    last_data_sent_time = last_photo_time
    last_fps_check_time = last_photo_time
    fps_check_interval = 0.5  # Check FPS every half second
    photos_since_check = 0
    current_fps = 0
    current_folder_size = {'size': 0, 'unit': 'MB'}
    
    # Initialize camera if needed
    if camera is None and not initialize_camera():
        recording = False
        return

    # Start folder size calculation thread
    folder_size_thread = threading.Thread(target=calculate_folder_size, args=(folder_name,))
    folder_size_thread.daemon = True  # Thread will exit when main program exits
    folder_size_thread.start()
    #threading.Thread(target=get_stats, daemon=True).start()
    #threading.Thread(target=get_stats_user_interface, daemon=True).start()

    # Send camera initialization status
    photo_queue.put({
        "count": 0,
        "time": 0,
        "time_unit": "seconds",
        "rate": 0,
        "rate_unit": "photos/sec",
        "folder": os.path.abspath(folder_name),
        "recording": True,
        "camera_ready": True,
        "folder_size": current_folder_size
    })

    photo_queue_user_interface.put({
        "count": 0,
        "time": 0,
        "time_unit": "seconds",
        "rate": 0,
        "rate_unit": "photos/sec",
        "folder": os.path.abspath(folder_name),
        "recording": True,
        "camera_ready": True,
        "folder_size": current_folder_size
    })

    initial_time = time.time()
    while recording and (time.time() - initial_time < max_time_interval_sec or max_time_interval_sec == 0):
        if camera is None and not initialize_camera():
            time.sleep(0.1)
            continue
            
        ret, unannotated_frame = camera.read()
        results = model.predict(unannotated_frame, verbose=False)
        # Draw the results on the frame
        frame = results[0].plot()

        if not ret:
            print("Failed to read frame from camera (recording)")
            continue
              
        if time.time() - last_feed_frame_time >= 0.001:
            feed_frame = frame
            last_feed_frame_time = time.time()
        
        current_time = time.time()
        
        # Check for new folder size updates
        try:
            while not folder_size_queue.empty():
                current_folder_size = folder_size_queue.get_nowait()
        except:
            pass  # No new folder size updates available
        
        # Adjust delta_time based on actual frame rate
        if current_time - last_fps_check_time >= fps_check_interval and photos_since_check > 0:
            actual_fps = photos_since_check / (current_time - last_fps_check_time)
            current_fps = round(actual_fps, 1)  # Update the current FPS measurement
            
            if delay and abs(actual_fps - target_fps) > 0.1:  # If off by more than 0.1 FPS
                # If we're going too slow, decrease delta_time
                # If we're going too fast, increase delta_time
                fps_error = target_fps - actual_fps
                adjustment = delta_time * adjustment_factor * (fps_error / target_fps)
                delta_time = max(min_delta, min(max_delta, delta_time - adjustment))
           
            last_fps_check_time = current_time
            photos_since_check = 0

        current_time = time.time()
        if current_time >= last_data_sent_time + .01:
            real_time_interval = current_time - initial_time
            time_unit = "minutes" if real_time_interval > 50 else "seconds"
            real_time_interval = real_time_interval/60 if time_unit == "minutes" else real_time_interval
            last_data_sent_time = current_time

            # Clear the queue
            while not photo_queue.empty():
                photo_queue.get()
            while not photo_queue_user_interface.empty():
                photo_queue_user_interface.get()


            photo_queue.put({
                "count": i,
                "time": round(real_time_interval, 1),
                "time_unit": time_unit,
                "rate": current_fps,
                "rate_unit": "photos/sec",
                "folder": os.path.abspath(folder_name),
                "recording": True,
                "folder_size": current_folder_size
            })

            photo_queue_user_interface.put({
                "count": i,
                "time": round(real_time_interval, 1),
                "time_unit": time_unit,
                "rate": current_fps,
                "rate_unit": "photos/sec",
                "folder": os.path.abspath(folder_name),
                "recording": True,
                "folder_size": current_folder_size
            })

        if current_time >= last_photo_time + delta_time or not delay:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
            save_path= os.path.join(folder_name, f"{timestamp}.{current_params['save_format']}")
            save_path_txt = os.path.join(folder_name, f"{timestamp}.txt")
            cv2.imwrite(save_path, unannotated_frame)
            for r in results:
                h, w = r.orig_shape
                with open(save_path_txt, "w") as f:
                    for box in r.boxes:
                        cls = int(box.cls[0])                  # class id
                        x1, y1, x2, y2 = box.xyxy[0]           # box corners (absolute)
                        # convert to YOLO format
                        x_center = ((x1 + x2) / 2) / w
                        y_center = ((y1 + y2) / 2) / h
                        width = (x2 - x1) / w
                        height = (y2 - y1) / h
                        f.write(f"{cls} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
            if not os.path.exists(os.path.join(folder_name, "labels.txt")):
                with open(os.path.join(folder_name, "labels.txt"), "w") as f:
                    for class_id, class_name in model.names.items():
                        f.write(f"{class_id}: {class_name}\n")
            last_photo_time = current_time
            i += 1
            photos_since_check += 1

    # Calculate final FPS over the last interval
    final_time = time.time()
    if final_time - last_fps_check_time > 0 and photos_since_check > 0:
        current_fps = round(photos_since_check / (final_time - last_fps_check_time), 1)

    real_time_interval = final_time - initial_time
    time_unit = "minutes" if real_time_interval > 50 else "seconds"
    real_time_interval = real_time_interval/60 if time_unit == "minutes" else real_time_interval

    # Get final folder size
    try:
        while not folder_size_queue.empty():
            current_folder_size = folder_size_queue.get_nowait()
    except:
        pass


    last_stats = {
        "count": i,
        "time": round(real_time_interval, 1),
        "time_unit": time_unit,
        "rate": current_fps,
        "rate_unit": "photos/sec",
        "folder": os.path.abspath(folder_name),
        "recording": False,
        "folder_size": current_folder_size
    }
    photo_queue.put(last_stats)
    photo_queue_user_interface.put(last_stats)
    recording = False

@app.route('/get_stats')
def get_stats():
    if not photo_queue.empty():
        stats = photo_queue.get()
        return jsonify(stats)
    return jsonify({})


@app.route('/get_stats_user_interface')
def get_stats_user_interface():
    if not photo_queue_user_interface.empty():
        stats = photo_queue_user_interface.get()
        return jsonify(stats)
    return jsonify({})


@app.route('/open_folder', methods=['POST'])
def open_folder():
    data = request.get_json()
    folder_path = data.get('path')
    
    if not folder_path or not os.path.exists(folder_path):
        return jsonify({'error': 'Invalid path'}), 400
    
    try:
        if platform.system() == 'Windows':
            os.startfile(folder_path)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', folder_path])
        else:  # Linux
            subprocess.run(['xdg-open', folder_path])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update_resolution', methods=['POST'])
def update_resolution():
    global current_params, camera
    
    data = request.get_json()
    if 'resolution' in data:
        current_params['resolution'] = data['resolution']
        # Release the camera and force reinitialization
        if camera is not None:
            camera.release()
            camera = None
        # Try to initialize with new resolution
        if not initialize_camera():
            return jsonify({"status": "error", "message": "Failed to initialize camera with new resolution"})
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "No resolution provided"})

@app.route('/update_camera', methods=['POST'])
def update_camera():
    global current_params, camera
    
    data = request.get_json()
    if 'camera_device' in data:
        current_params['camera_device'] = data['camera_device']
        # Release the camera and force reinitialization
        if camera is not None:
            camera.release()
            camera = None
        # Try to initialize with new camera
        if not initialize_camera():
            return jsonify({"status": "error", "message": "Failed to initialize camera device"})
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "No camera device provided"})

if __name__ == '__main__':
    app.run(debug=True) 
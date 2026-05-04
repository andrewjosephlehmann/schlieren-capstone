'''
Author: Andrew Lehmann

Description: Example software to view the speed at which kelvin helmholtz instability patterns propagate upward.
'''

# %%
import numpy as np
import cv2
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

video_path = 'SCH/2026-03-09_11-46-44_796.wmv'


cap = cv2.VideoCapture(video_path)

ret, frame1 = cap.read()


prev_gray = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)

fps = cap.get(cv2.CAP_PROP_FPS)
meters_per_pixel = 0.000268056338 

fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16)

roi = cv2.selectROI("Select ROI", frame1, False)
cv2.destroyWindow("Select ROI")

x, y, w, h = roi
roi_mask = np.zeros_like(prev_gray)
roi_mask[y:y+h, x:x+w] = 255

speed_history = []

frame_idx = 1  
time_history = []

speed_log = []

smooth_buffer = []

while True:

    ret, frame2 = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

    # Dense optical flow
    flow = cv2.calcOpticalFlowFarneback(
        prev_gray, gray,
        None,
        pyr_scale=0.5,
        levels=3,
        winsize=21,
        iterations=5,
        poly_n=7,
        poly_sigma=1.5,
        flags=0
    )

    fx = flow[...,0]
    fy = flow[...,1]

    mag, ang = cv2.cartToPolar(fx, fy)

    # Background subtraction mask
    fgmask = fgbg.apply(frame2)
    fgmask = cv2.medianBlur(fgmask,5)

    # Motion threshold
    motion_mask = mag > 0.2

    # Combine masks
    combined_mask = (fgmask > 0) & motion_mask & (roi_mask > 0)

    plume_motion = mag[combined_mask]

    if plume_motion.size > 0:
        avg_disp = np.mean(plume_motion)
    else:
        avg_disp = 0

    # Convert to speed
    speed = avg_disp * fps * meters_per_pixel

    smooth_buffer.append(speed)
    if len(smooth_buffer) > 20:
        smooth_buffer.pop(0)

    smooth_speed = np.mean(smooth_buffer)
    
    frame_idx += 1
    timestamp = frame_idx / fps  # seconds

    time_history.append(timestamp)
    speed_log.append(smooth_speed)



    vis = frame2.copy()

    step = 20
    for yy in range(0, flow.shape[0], step):
        for xx in range(0, flow.shape[1], step):

            if combined_mask[yy,xx]:

                dx = fx[yy,xx]
                dy = fy[yy,xx]

                cv2.arrowedLine(
                    vis,
                    (xx,yy),
                    (int(xx+dx*5), int(yy+dy*5)),
                    (0,255,0),
                    1,
                    tipLength=0.3
                )

    # Draw ROI box
    cv2.rectangle(vis, (x,y), (x+w,y+h), (0,255,255), 2)

    # Display speed
    cv2.putText(
        vis,
        f"Plume speed: {smooth_speed:.5f} m/s",
        (20,40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0,255,0),
        2
    )

    cv2.imshow("Plume Flow", vis)

    if cv2.waitKey(1) & 0xFF == 27:
        break

    prev_gray = gray

cap.release()
cv2.destroyAllWindows()

# %%



# load csv data
df_temp = pd.read_csv('apl_data_run2.csv')
df_temp['timestamp'] = pd.to_datetime(df_temp['timestamp'])

# start time # Note that the computer was two hours behind for the example data provided
video_start = datetime(2026, 3, 9, 13, 46, 44)

#conversion 
df_temp['elapsed_s'] = (df_temp['timestamp'] - pd.Timestamp(video_start)).dt.total_seconds()

# compute the ambient temperature
df_temp['ambient'] = (df_temp['mon1'] + df_temp['mon2']) / 2

# filter for only the video duration
max_time = max(time_history)
df_temp = df_temp[(df_temp['elapsed_s'] >= 0) & (df_temp['elapsed_s'] <= max_time)]

# plot
fig, ax1 = plt.subplots(figsize=(10, 5))

# speed on left axis
ax1.plot(time_history, speed_log, color='royalblue', linewidth=1, label='Plume Speed (m/s)')
ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Plume Speed (m/s)', color='royalblue')
ax1.tick_params(axis='y', labelcolor='royalblue')

# temperature on right axis
ax2 = ax1.twinx()
ax2.plot(df_temp['elapsed_s'], df_temp['T3'],    color='tomato',      linewidth=1, label='T3')
ax2.plot(df_temp['elapsed_s'], df_temp['ambient'], color='darkorange', linewidth=1, linestyle='--', label='Ambient (avg mon1/mon2)')
ax2.set_ylabel('Temperature (C)', color='tomato')
ax2.tick_params(axis='y', labelcolor='tomato')

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

plt.title('Plume Speed and Temperature over Time')
plt.tight_layout()
plt.savefig('speed_temperature_plot.png', dpi=150)
plt.show()
# %%

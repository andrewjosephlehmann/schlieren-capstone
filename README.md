# schlieren-capstone






opticalflow.py:

The Python program opticalflow.py allows one to measure the velocity of turbulent patterns from .wmv files already provided in the repository. 
For new data, make sure to retrieve the meters-per-pixel ratio, which allows us to extrapolate the velocity of the propagating patterns in the water. I initially did this 
by taking a measurement from the bottom of the heater to the waterline in the video, and then using cropping software, I obtained the number of pixels corresponding to that measured length (L/px). 


When running the Python cell, a pop-up window titled 'select ROI' will appear. This allows you to specify which part of the video to run the optical flow algorithm on. To specify the region, left-click and drag your cursor to form the bounding box, and press 'return/enter' to confirm the selection. 
<img width="653" height="520" alt="image" src="https://github.com/user-attachments/assets/8e3c3394-2b2c-4a33-ba3d-e5e0b7380419" />

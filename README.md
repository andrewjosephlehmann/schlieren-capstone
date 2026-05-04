# schlieren-capstone

Warning:

This experiment involves a high power draw (up to 320 watts total); the initial apparatus can only handle 40 watts due to inadequate bus wiring and a power supply. (Do not run the apparatus continuously, as it would be prone to an electrical fire if a hardware malfunction were to occur (such as sending too much current into the heaters)). To reduce the risk of electric shock when inserting the array of heaters into the aquarium, do not touch the water in the fish tank while the apparatus is powered on. 

Experimental Setup:

BOM: 

1 x 8 relay module https://a.co/d/0czdi1bT 

8 x 40W 12V heater cartridges https://a.co/d/03P65jwe

8 x NTC 3950 thermistors https://a.co/d/0iHnboFi

1 x Arduino Leonardo

1 x Sparkfun PID 13906 https://a.co/d/0bEcR1Cd


Follow the same procedure for the heat gun test as outlined in the Scheliren capstone manual to ensure the camera can detect optical inhomogeneities emanating from the heat gun. 

Ensure the heater array is inserted into the water upright, as shown in the image below:

<img width="768" height="1024" alt="14EA9531-E6D1-43EA-80B7-8CA05D96342D_1_105_c" src="https://github.com/user-attachments/assets/be76d72d-65fd-4cef-b846-e2dbc1347003" />

The apparatus was initially held upright with a clamp, as shown in this image:

<img width="1024" height="768" alt="E06C874C-9FB6-4DA0-A63A-565C320C115C_1_105_c" src="https://github.com/user-attachments/assets/7a1a4160-63c3-43bd-bbf5-43c8b474d3f7" />

If the heater array is not redesigned to ensure that the wires from the heaters and temperature sensors do not compromise the array's stability when sitting upright. Please use a clamp made of a non-corrosive material, such as plastic, as the water quality will degrade rapidly, obstructing the optical setup's ability to observe inhomogeneities in the water.

If this is replicated in the future, I would strongly recommend organizing the cables to prevent tangling, which could tug on the heater or temperature sensor wires. 


Software:

The array of heaters was controlled with the control.py program listed in the repository. The firmware for the Arduino Leonardo uses a PID script adapted to work with relays located in the 'thermal_pid' folder.


opticalflow.py:

The Python program opticalflow.py allows one to measure the velocity of turbulent patterns from .wmv files already provided in the repository. For new data, make sure to retrieve the meters-per-pixel ratio, which allows us to extrapolate the velocity of the propagating patterns in the water. I initially did this by measuring the distance from the bottom of the heater to the waterline in the video, and then, using cropping software, I obtained the number of pixels corresponding to that measured length (L/px). 


When running the Python cell, a pop-up window titled 'select ROI' will appear. This allows you to specify which part of the video to run the optical flow algorithm on. To specify the region, left-click and drag your cursor to form the bounding box, and press 'return/enter' to confirm the selection. 
<img width="653" height="520" alt="image" src="https://github.com/user-attachments/assets/8e3c3394-2b2c-4a33-ba3d-e5e0b7380419" />

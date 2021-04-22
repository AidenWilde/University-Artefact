# Artefact
University final year project artefact

For this project to run on your local machine you must first install Python and the required dependencies:

1. https://pypi.org/project/face-recognition/
2. https://pypi.org/project/opencv-python/


**How to use**

1. Launch the python program 'artefact.py' and it will generate the required folders and settings file

2. The folders will be created in the same directory as artefact.py, and you will need to add your own data to them 

2.1. The 'known_people' folder should contain images of faces of people you want to be able to identify 

2.2. The 'videos' folder should contain videos that you want to be processed, for identification of individuals or faces within those videos 

2.3. The 'output_videos' folder will automatically contain all processed videos when the user presses the 'pre-recorded' button and once the program suggests it has finished.

3. If you select real-time, only the 'known_people' folder is needed, as it will use the images located within to identify people using the hardware selected.

import tkinter as tk
import cv2 # available at : https://pypi.org/project/opencv-python/
import face_recognition # available at : https://pypi.org/project/face-recognition/
import threading
import os
import numpy
import time
from enum import Enum
# custom libraries made by me
from TkinterWrapper import TkinterWrapper 
from FileHandler import FileHandler
from Settings import Settings
from Error import Error
from ArtefactGUI import ArtefactGUI

"""
Todo list:

1. Paralelism/Multiprocessing so that videos can be processed faster 
2. Show each frame being written to output video (can use canvas : https://solarianprogrammer.com/2018/04/21/python-opencv-show-video-tkinter-window/)

!!! handy for face_locations  (faces that aren't detected using face_encodings)
https://github.com/ageitgey/face_recognition/issues/670
"""

class InputType(Enum):
    PreRecorded = 0
    Realtime = 1

class Application:
    def __init__(self):
        self.fileHandler = FileHandler()
        self.directorySettings = self.ReadSettings()
        # Supported formats listed here: https://docs.opencv.org/master/d4/da8/group__imgcodecs.html
        self.supportedFileFormats = ["jpg", "jpeg", "mp4", "mov"]
        self.knownPeople = {}
        self.videosToAnalyse = []
        self.LoadKnownFaceEncodings()
        self.resourcesLoadedAtleastOnce = False

        mainWindow = tk.Tk()
        self.gui = ArtefactGUI(master=mainWindow)
        self.runStatusLabel = self.gui.AddWidget("label", "Status: Awaiting input", None, 1, 1)
        self.reloadResourcesButton = self.gui.AddWidget("button", "Load/Reload resources", lambda: self.LoadImagesAndVideos(), 1, 2)
        self.preRecordedButton = self.gui.AddWidget("button", "Pre-recorded analysis", lambda: self.Run(InputType.PreRecorded), 1, 3) 
        self.realTimeButton = self.gui.AddWidget("button", "Real-time analysis", lambda: self.Run(InputType.Realtime), 1, 4)
        self.quitButton = self.gui.AddWidget("button", "Quit", lambda : mainWindow.destroy(), 1, 5)
        
        self.gui.DisableButton(self.preRecordedButton)
        self.gui.mainloop()

    def ReadSettings(self):
        settingsFile = "settings.txt"
        settings = self.fileHandler.ReadLine("", settingsFile)
        if(len(settings) == 0 or len(settings.split(',')) != 4):
            print("Overwriting invalid settings file")
            self.fileHandler.WriteFileContents(settingsFile, "inputDirectory=videos, outputDirectory=output_videos, knownPeople=known_people, faceEncodings=face_encodings")
            return self.ReadSettings()
        else:
            separateSettings = settings.split(',')
            settings = Settings(separateSettings[0].split('=')[1], separateSettings[1].split('=')[1], separateSettings[2].split('=')[1], separateSettings[3].split('=')[1])                
            return settings

    def IdentifyIndividualsInFrame(self, frame):
        faceNames = []

        faceLocations = face_recognition.face_locations(frame)
        faceEncodings = face_recognition.face_encodings(frame, faceLocations)
        for faceEncoding in faceEncodings:
            name = ""
            for knownPerson in self.knownPeople:
                knownFaceEncoding = self.knownPeople[knownPerson]
                match = face_recognition.compare_faces([knownFaceEncoding], faceEncoding, tolerance=0.5)
                
                if(match):
                    if(match[0]):
                        print(f"match found for {knownPerson}")
                        name = knownPerson
            faceNames.append(name)

        return (faceNames, faceLocations) 

    def DrawResultsToFrame(self, originalFrame, faceNames, faceLocations):
        for (top, right, bottom, left), name in zip(faceLocations, faceNames):
            # Draw a box around the face
            mainColour = (0,255,0)
            cv2.rectangle(originalFrame, (left, top), (right, bottom), mainColour, 2)

            # Draw a label with a name below the face
            if(name != ""):
                idBoxStart = (left, bottom)
                idBoxEnd = (right, bottom + 20)
                cv2.rectangle(originalFrame, idBoxStart, idBoxEnd, (25, 25, 25), cv2.FILLED) # for text visibility
                cv2.rectangle(originalFrame, idBoxStart, idBoxEnd, mainColour, thickness=2)
                #fontScale = (((right-left)/100)/(bottom-top))*10
                cv2.putText(originalFrame, name, (left + 10 , bottom + 15), cv2.FONT_HERSHEY_DUPLEX, 0.45, (255, 255, 255), 1)
        
        return originalFrame

    def ApplyAIAlgorithm(self, videoName):
        try:
            #startTime = time.time()
            # Open input video file into memory 
            inputVideo = cv2.VideoCapture(f"{self.directorySettings.inputDirectory}/{videoName}")
            length = int(inputVideo.get(cv2.CAP_PROP_FRAME_COUNT))
        
            # Create an output video file
            outputVideo = self.CreateOutputVideo(inputVideo, videoName)

            frameNumber = 0

            while True:
                readingVideo, frame = inputVideo.read()
                frameNumber += 1

                if not readingVideo:
                    break

                # cv uses BGR instead of RGB so converting it to the same as face_recognition uses
                rgbFrame = frame[:, :, ::-1]
                
                identifyIndividualsInFrameResult = self.IdentifyIndividualsInFrame(rgbFrame)
                faceNames = identifyIndividualsInFrameResult[0]
                faceLocations = identifyIndividualsInFrameResult[1]
                updatedFrame = self.DrawResultsToFrame(frame, faceNames, faceLocations)

                # Write the resulting image to the output video file
                self.gui.UpdateLabelWidget(self.runStatusLabel, f"Status: Writing frame {frameNumber}/{length}")
                outputVideo.write(updatedFrame)

            inputVideo.release()
            cv2.destroyAllWindows()

            #endTime = time.time()
            #timeTaken = endTime - startTime
            #newContent = f"start:{str(startTime)}\nend:{str(endTime)}\ntimeTaken:{str(timeTaken)}\ntotalFrames:{str(length)}\ntimePerFrame:{str(timeTaken/length)}"
            #self.fileHandler.WriteFileContents(f"timings-{videoName}.txt", newContent)
            
            return
        except Error as e:
            raise e    
    
    def CreateOutputVideo(self, inputVideo, videoName):
        if(not self.fileHandler.DirectoryExists(self.directorySettings.outputDirectory)):
            if(not self.fileHandler.CreateDirectory(self.directorySettings.outputDirectory)):
                raise Error(f"An error has occured when creating the output video for {videoName}")

        # Read information from the video so that resolution and frame rate matches input video
        videoCodec = int(inputVideo.get(cv2.CAP_PROP_FOURCC))
        framesPerSecond = int(inputVideo.get(cv2.CAP_PROP_FPS))
        frameWidth = int(inputVideo.get(cv2.CAP_PROP_FRAME_WIDTH))
        frameHeight = int(inputVideo.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Return the object reference to the newly created output video
        video = cv2.VideoWriter(f"{self.directorySettings.outputDirectory}/{videoName}", videoCodec, framesPerSecond, (frameWidth, frameHeight))        
        print(f"Created new output video to {self.directorySettings.outputDirectory}/{videoName}")
        return video

    def Run(self, inputType):
        self.gui.StartAutoRefresh()

        try:
            if(inputType == InputType.PreRecorded):
                threading.Thread(target=self.AnalyseVideos).start()
                
            elif(inputType == InputType.Realtime):
                pass
            # rest of functionality here...
        except Error as e:
            self.gui.UpdateLabelWidget(self.runStatusLabel, f"Status: An error has occured: {e.GetErrorMessage()}")
            print(e.GetErrorMessage())

    def AnalyseVideos(self):
        self.gui.DisableButton(self.preRecordedButton)
        for video in self.videosToAnalyse:
            try:
                self.gui.UpdateLabelWidget(self.runStatusLabel, f"Status: Starting video {video}")
                self.ApplyAIAlgorithm(video)
                self.gui.UpdateLabelWidget(self.runStatusLabel, f"Status: Finished video {video}")
            except Error as e:
                self.gui.UpdateLabelWidget(self.runStatusLabel, f"Status: An error has occured: {e.GetErrorMessage()}")
                print(e.GetErrorMessage())
                continue
        self.gui.EnableButton(self.preRecordedButton)

    def LoadImagesAndVideos(self):
        self.LoadInputImages()
        self.LoadInputVideos()
        self.gui.UpdateLabelWidget(self.runStatusLabel, "Finished loading images and videos. Awaiting input.")
        if(self.resourcesLoadedAtleastOnce == False):
            self.gui.EnableButton(self.preRecordedButton)
            self.resourcesLoadedAtleastOnce = True
        return

    def LoadInputImages(self):
        self.gui.UpdateLabelWidget(self.runStatusLabel, "Status: Loading known faces...")
        imageFiles = self.fileHandler.ListDirectory(self.directorySettings.knownPeopleDirectory)
        for imageFile in imageFiles:
            fileInformation = imageFile.split(".")
            if(fileInformation[1].lower() in self.supportedFileFormats):
                if(any(fileInformation[0] in identifier for identifier in list(self.knownPeople.keys()))):
                    print(f"Skipped loading file {fileInformation[0]} because an encoding is already known of this individual")
                    continue

                print(f"New image found, analysing image {fileInformation[0]} and saving to face encoding database")
                loadedImage = face_recognition.load_image_file(self.directorySettings.knownPeopleDirectory + "/"+ imageFile)
                faceLocations = face_recognition.face_locations(loadedImage, model="cnn", number_of_times_to_upsample=0)
                faceEncodings = face_recognition.face_encodings(loadedImage, known_face_locations=faceLocations)
                # for each face in the image, give the person the name of the image + n, e.g. ABC-1, ABC-2 and save to file as (name:encoding)
                number = 1 # used to determine how many unique individuals are found within a given image
                for face in faceEncodings:
                    name = f"{fileInformation[0]}-{number}"
                    self.knownPeople[name] = face
                    number += 1

                self.SaveKnownPeople(self.knownPeople)
            else:
                continue  

        self.knownPeopleLoaded = True

    def LoadKnownFaceEncodings(self):
        if(not self.fileHandler.DirectoryExists(f"{self.directorySettings.faceEncodingsDirectory}.txt")):
            print("No known face encodings file... skipping pre-load.")
            return 

        print("Reading known face encodings")

        self.knownPeople.clear()
        faceEncodingsFileData = self.fileHandler.PickleReadFile(f"{self.directorySettings.faceEncodingsDirectory}.txt")
        if(not len(faceEncodingsFileData) > 0):
            return

        # need to alter how it reads known encodings
        for knownEncoding in faceEncodingsFileData:
            self.knownPeople[knownEncoding] = faceEncodingsFileData[knownEncoding]

        print(f"Finished pre-loading {len(self.knownPeople.keys())} people")
        print(list(self.knownPeople.keys()))

    def SaveKnownPeople(self, knownPeople):
        self.fileHandler.PickleWriteFile("face_encodings.txt", knownPeople)

    def LoadInputVideos(self):
        self.gui.UpdateLabelWidget(self.runStatusLabel, "Status: Loading input videos...")
        self.videosToAnalyse.clear()

        # Go through all videos in the videos directory and create a new ArtefactVideo object
        videoFiles = self.fileHandler.ListDirectory(self.directorySettings.inputDirectory)
        for video in videoFiles:
            fileFormat = video.split(".")[1].lower()
            if(fileFormat in self.supportedFileFormats):
                self.videosToAnalyse.append(video)
            else:
                continue

        self.gui.EnableButton(self.preRecordedButton)

application = Application()
print("Artefact application closed.")
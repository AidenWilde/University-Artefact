import tkinter as tk
import cv2
import face_recognition
import threading
import multiprocessing
import signal
import os
import numpy
import time
from enum import Enum

from TkinterWrapper import TkinterWrapper 
from FileHandler import FileHandler
from Settings import Settings
from Error import Error
from ArtefactGUI import ArtefactGUI

class InputType(Enum):
    PreRecorded = 0
    Realtime = 1

class Application:
    def __init__(self):
        self.fileHandler = FileHandler()
        self.directorySettings = self.ReadSettings()
        self.supportedFileFormats = ["jpg", "jpeg", "mp4", "mov"]
        self.knownPeople = {}
        self.videosToAnalyse = []
        self.LoadKnownFaceEncodings()
        self.resultingFrames = []
        self.threads = []
        self.exitEvent = threading.Event()

        self.mainWindow = tk.Tk()
        self.gui = ArtefactGUI(master=self.mainWindow)
        self.runStatusLabel = self.gui.AddWidget("label", "Status: Awaiting input", None, 1, 1)
        self.reloadResourcesButton = self.gui.AddWidget("button", "Load/Reload resources", lambda: self.LoadImagesAndVideos(), 1, 2)
        self.preRecordedButton = self.gui.AddWidget("button", "Pre-recorded analysis", lambda: self.Run(InputType.PreRecorded), 1, 3, tk.DISABLED) 
        self.realTimeButton = self.gui.AddWidget("button", "Real-time analysis", lambda: self.Run(InputType.Realtime), 1, 4,  tk.DISABLED)
        self.quitButton = self.gui.AddWidget("button", "Quit", lambda : self.mainWindow.destroy(), 1, 5)
        
        self.gui.mainloop()

    def SignalHandler(self, signum, frame):
        self.exitEvent.set()

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

    def DrawResultsToFrame(self, originalFrame, faceNames, faceLocations, faceLocationScale):
        for (top, right, bottom, left), name in zip(faceLocations, faceNames):
            top *= faceLocationScale
            right *= faceLocationScale
            bottom *= faceLocationScale
            left *= faceLocationScale

            mainColour = (0,255,0)
            cv2.rectangle(originalFrame, (left, top), (right, bottom), mainColour, 2)

            if(name != ""):
                idBoxStart = (left, bottom)
                idBoxEnd = (right, bottom + 20)
                cv2.rectangle(originalFrame, idBoxStart, idBoxEnd, (25, 25, 25), cv2.FILLED)
                cv2.rectangle(originalFrame, idBoxStart, idBoxEnd, mainColour, thickness=2)
                cv2.putText(originalFrame, name, (left + 10 , bottom + 15), cv2.FONT_HERSHEY_DUPLEX, 0.45, (255, 255, 255), 1)
        
        return originalFrame

    def ProcessChunk(self, chunk):
        print("Processing next chunk.")
        for frameTupil in chunk:
            if(self.exitEvent.is_set()):
                print("Finished chunk early because program received exit command.")
                break    
            (faceNames, faceLocations) = self.IdentifyIndividualsInFrame(frameTupil[2])
            updatedFrame = self.DrawResultsToFrame(frameTupil[1], faceNames, faceLocations, 1)
            self.resultingFrames.append((frameTupil[0], updatedFrame))
        print("Finished chunk.")

    def ChunkFrames(self, uneditedFrames):
        print("Generating chunks.")
        chunks = []
        chunk = []
        maxNumberOfChunks = 4
        chunkSize = int(len(uneditedFrames)/maxNumberOfChunks)
        remainingFrames = len(uneditedFrames)-(chunkSize*maxNumberOfChunks)
        
        iterator = 0
        for uneditedFrameTuple in uneditedFrames:
            chunk.append(uneditedFrameTuple)
            iterator += 1
            if(iterator % int(chunkSize) == 0):
                chunks.append(chunk)
                chunk = []

        if(remainingFrames > 0):
            for i in range(chunks[3][-1][0], (chunks[3][-1][0] + remainingFrames)):
                chunks[3].append(uneditedFrames[i])

        return chunks

    def ApplyAIAlgorithm(self, videoName, inputType):
        try:
            print(f"Processing video {videoName}")
            self.gui.UpdateLabelWidget(self.runStatusLabel, f"Processing video {videoName}")
            uneditedFrames = []

            if(inputType == InputType.PreRecorded):
                print(f"Applying AI Algorithm to {videoName}")
                inputVideo = cv2.VideoCapture(f"{self.directorySettings.inputDirectory}/{videoName}")
                if(not inputVideo.isOpened()):
                    raise Error(f"Unable to open video {videoName}")

                frameNumber = 0

                while True:
                    if(self.exitEvent.is_set()):
                        raise Error(f"Finished processing {videoName} early because program received exit command")

                    readingVideo, cvFrame = inputVideo.read()
                    frameNumber += 1

                    if not readingVideo:
                        break

                    rgbFrame = cvFrame[:, :, ::-1]
                    uneditedFrames.append((frameNumber, cvFrame, rgbFrame))
                    
                chunks = self.ChunkFrames(uneditedFrames) 
                for chunk in chunks:
                    process = threading.Thread(target=self.ProcessChunk, args=[chunk])
                    process.start()
                    self.threads.append(process)

                for process in self.threads:
                    process.join()

                outputVideo = self.CreateOutputVideo(inputVideo, videoName)

                count = 0
                sortedResultingFrames = sorted(self.resultingFrames, key=lambda x : x[0])
                for frame in sortedResultingFrames:
                    outputVideo.write(frame[1])
                    count += 1

                inputVideo.release()
                cv2.destroyAllWindows()
                self.resultingFrames.clear()

                print(f"Finished processing video {videoName}")

            elif(inputType == InputType.Realtime):
                self.gui.DisableButton(self.realTimeButton)
                videoCapture = cv2.VideoCapture(0)
                if(not videoCapture.isOpened()):
                    raise Error(f"Unable to open video {videoName}")

                processNewFrame = True
                cv2NamedWindowString = "Real-time video processing"
                cv2.namedWindow(cv2NamedWindowString)
                cv2.moveWindow(cv2NamedWindowString, 0, 0)

                while True:
                    ret, frame = videoCapture.read()
                    smallFrame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                    rgbSmallFrame = smallFrame[:, :, ::-1]
                    if processNewFrame:
                        (faceNames, faceLocations) = self.IdentifyIndividualsInFrame(rgbSmallFrame)
                    
                    processNewFrame = not processNewFrame
                    analysedFrame = self.DrawResultsToFrame(frame, faceNames, faceLocations, 4)
                    cv2.imshow(cv2NamedWindowString, analysedFrame)

                    if(cv2.waitKey(1) & 0xFF == ord('q')):
                        cv2.destroyAllWindows()
                        self.gui.UpdateLabelWidget(self.runStatusLabel, f"Status: Closed real-time video window")
                        self.gui.EnableButton(self.realTimeButton)
                        break
            return
        except Error as e:
            raise e    
    
    def CreateOutputVideo(self, inputVideo, videoName):
        if(not self.fileHandler.DirectoryExists(self.directorySettings.outputDirectory)):
            if(not self.fileHandler.CreateDirectory(self.directorySettings.outputDirectory)):
                raise Error(f"An error has occured when creating the output video for {videoName}")

        videoCodec = int(inputVideo.get(cv2.CAP_PROP_FOURCC))
        framesPerSecond = int(inputVideo.get(cv2.CAP_PROP_FPS))
        frameWidth = int(inputVideo.get(cv2.CAP_PROP_FRAME_WIDTH))
        frameHeight = int(inputVideo.get(cv2.CAP_PROP_FRAME_HEIGHT))

        video = cv2.VideoWriter(f"{self.directorySettings.outputDirectory}/{videoName}", videoCodec, framesPerSecond, (frameWidth, frameHeight))        
        print(f"Created new output video to {self.directorySettings.outputDirectory}/{videoName}")
        return video

    def Run(self, inputType):
        self.gui.StartAutoRefresh()

        try:
            if(inputType == InputType.PreRecorded):
                signal.signal(signal.SIGINT, self.SignalHandler)
                analyseVideosThread = threading.Thread(target=self.AnalyseVideos)
                analyseVideosThread.start()
            elif(inputType == InputType.Realtime):
                self.AnalyseHardwareVideoStream()
                # threading.Thread(target=self.AnalyseHardwareVideoStream).start()

        except Error as e:
            self.gui.UpdateLabelWidget(self.runStatusLabel, f"Status: An error has occured: {e.GetErrorMessage()}")
            print(e.GetErrorMessage())

    def AnalyseHardwareVideoStream(self):
        try:
            self.gui.UpdateLabelWidget(self.runStatusLabel, f"Status: Reading from hardware video stream...")
            self.ApplyAIAlgorithm(None, InputType.Realtime)
        except Error as e:
            self.gui.UpdateLabelWidget(self.runStatusLabel, f"Status: An error has occured: {e.GetErrorMessage()}")
            print(e.GetErrorMessage())

    def AnalyseVideos(self):
        self.gui.DisableButton(self.preRecordedButton)
        self.gui.DisableButton(self.reloadResourcesButton)
        for video in self.videosToAnalyse:
            if(self.exitEvent.is_set()):
                print("Finished processing early because program received exit command.")
                self.exitEvent.clear()
                break
            else:
                try:
                    self.gui.UpdateLabelWidget(self.runStatusLabel, f"Status: Starting video {video}")
                    self.ApplyAIAlgorithm(video, InputType.PreRecorded)
                    self.gui.UpdateLabelWidget(self.runStatusLabel, f"Status: Finished video {video}")
                except Error as e:
                    self.gui.UpdateLabelWidget(self.runStatusLabel, f"Status: An error has occured: {e.GetErrorMessage()}")
                    print(e.GetErrorMessage())
                    continue
        self.gui.EnableButton(self.preRecordedButton)
        self.gui.EnableButton(self.reloadResourcesButton)

    def LoadImagesAndVideos(self):
        self.LoadInputImages()
        self.LoadInputVideos()
        self.gui.UpdateLabelWidget(self.runStatusLabel, "Finished loading images and videos. Awaiting input.")
        return

    def LoadInputImages(self):
        self.gui.UpdateLabelWidget(self.runStatusLabel, "Status: Loading known faces...")
        imageFiles = self.fileHandler.ListDirectory(self.directorySettings.knownPeopleDirectory)
        if(len(imageFiles) <= 0):
            raise Error(f"No input images found, no new individuals will be able to be identified other than already-known encodings.")

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

                number = 1 
                for face in faceEncodings:
                    name = f"{fileInformation[0]}-{number}"
                    self.knownPeople[name] = face
                    number += 1

                self.SaveKnownPeople(self.knownPeople)
            else:
                continue  

        self.gui.EnableButton(self.realTimeButton)

    def LoadKnownFaceEncodings(self):
        if(not self.fileHandler.DirectoryExists(f"{self.directorySettings.faceEncodingsDirectory}.txt")):
            print("No known face encodings file... skipping pre-load.")
            return 

        print("Reading known face encodings")

        self.knownPeople.clear()
        faceEncodingsFileData = self.fileHandler.PickleReadFile(f"{self.directorySettings.faceEncodingsDirectory}.txt")
        if(not len(faceEncodingsFileData) > 0):
            return

        for knownEncoding in faceEncodingsFileData:
            self.knownPeople[knownEncoding] = faceEncodingsFileData[knownEncoding]

        print(f"Finished pre-loading {len(self.knownPeople.keys())} people")
        print(list(self.knownPeople.keys()))

    def SaveKnownPeople(self, knownPeople):
        self.fileHandler.PickleWriteFile("face_encodings.txt", knownPeople)

    def LoadInputVideos(self):
        self.gui.UpdateLabelWidget(self.runStatusLabel, "Status: Loading input videos...")
        self.videosToAnalyse.clear()

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
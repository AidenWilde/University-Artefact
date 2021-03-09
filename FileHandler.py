import os
import pickle

class FileHandler:
    def __init__(self):
        pass

    def PickleWriteFile(self, fileLocation, content):
        with open(fileLocation, 'wb') as file:
            pickle.dump(content, file)

    def PickleReadFile(self, fileLocation):
        with open(fileLocation, 'rb') as file:
	        all_face_encodings = pickle.load(file)

        return all_face_encodings

    def ReadLine(self, path, fileName):
        if(os.path.exists(fileName)):
            file = open(fileName, 'r')
            contents = file.readline()
            file.close()
            return contents
        else:
            return []      
    
    def WriteFileContents(self, fileName, content):
        file = open(fileName, 'w')
        file.writelines(content)
        file.close()

    def DirectoryExists(self, path):
        return os.path.exists(path)

    def CreateDirectory(self, path):
        if(os.path.exists(path) == False):
            os.mkdir(path)

        return os.path.exists(path)
        
    def ListDirectory(self, path):
        if(os.path.exists(path) == False):
            return []
        else:
            return os.listdir(path)
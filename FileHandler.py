import os
import pickle

class FileHandler:
    def __init__(self):
        pass

    def PickleWriteLine(self, path, filename, content):
        file = open(f'{path}/{filename}', 'wb')
        pickle.dump(content, file)
        file.close()

    def PickleReadFile(self, path, filename, content):
        file = open(f'{path}/{filename}', 'rb')
        fileContent = pickle.load(file)
        file.close()
        return fileContent

    def ReadLine(self, path, fileName):
        if(os.path.exists(fileName)):
            file = open(fileName, 'r')
            contents = file.readline()
            file.close()
            return contents
        else:
            return []      

    def ReadLines(self, path, fileName):
        if(os.path.exists(fileName)):
            file = open(fileName, 'r')
            contents = file.readlines()
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
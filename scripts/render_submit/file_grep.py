'''
Module to grep and sort files.
'''

import glob
import os 
# import time

def get_files(directory, file_types = ('*.ma', '*.mb')):
    directory = os.path.abspath(directory)
    if not os.path.isdir(directory):
        return []
   
    files = []
    for file_type in file_types:
        file_paths = glob.glob(os.path.join(directory, "**", file_type), recursive = True)

        for file_path in file_paths:
            file_path = os.path.normpath(file_path).replace('\\', '/')
            file_time = os.path.getmtime(file_path)
            files.append((file_path, file_time))
    if files:
        sort_tuple(files)
        files = [f[0] for f in files]
        files.reverse()

    return files

def sort_tuple(tup):
    '''Function to sort the list by second item of tuple'''
 
    # reverse = None (Sorts in Ascending order)
    # key is set to sort using second element of
    # sublist lambda has been used
    tup.sort(key = lambda x: x[1])
    return tup

if __name__ == '__main__': 
    directory = 'Z:'
    print(get_files(directory))
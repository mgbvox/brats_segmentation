import os
import pandas as pd


'''
An easily manipulable OS-like wrapper for PyDrive.
Takes inspiration from FastAI's pathlib.Path().
Originally built to facilitate transfer of data from Google Drive to SageMaker.

Built by Matthew Billman
Apteryx Labs
mgbvox@gmail.com
www.matthewbillman.com

If this code made your life easier, consider sending a tip my way:
paypal.me/matthewbillman

'''

#Recursive download function tailored to File() object type.
def download_directory(root, ignore=[]):
    for f in root.ls():
        print(f.path)
        if not any(item in f.path for item in ignore):
            if f.is_dir:
                if not os.path.isdir(f.path):
                    print(f'Making {f.path}')
                    os.mkdir(f.path)
                download_directory(f)
            elif f.is_file:
                if not os.path.exists(f.path):
                    f.download(dest=f.path)
        clear_output()
    print('Done!')

    
class File:
    def __init__(self, f_obj, drive=None):
        self.obj = f_obj
        self.drive = drive
        self.name = self.obj['title']
        self.id = self.obj['id']
        
        #File Structure Properties
        self.parent = None
        self.children = None
        self.path = None
        self.is_root = not bool(self.parent)
        self.is_dir = self.obj['mimeType']=='application/vnd.google-apps.folder'
        self.is_file = not self.is_dir
        
        if not self.parent:
            self.path = f'./{self.name}'
        
    def __repr__(self):
        base = f'{self.name} | {self.id}'
        if not self.drive:
            base = 'NO ATTACHED DRIVE.'
        return  base
    
    def set_parent(self, parent):
        self.parent = parent
        self.path = os.path.join(str(parent.path),str(self.name))
        self.is_root = not bool(self.parent)    
            
    def set_to_root(self):
        self.parent = None
        self.path = f'./{self.name}'
        self.is_root = True
    
    def ls(self, r=False):
        if not 'Series' in str(type(self.children)):
            filelist=[]
            file_list = self.drive.ListFile({'q': "'%s' in parents and trashed=false" % self.id}).GetList()

            for f in file_list:
                f_class = File(f, drive=self.drive)
                f_class.set_parent(self)
                filelist.append(f_class)

            self.children = pd.Series(filelist)
        
        return self.children
    
    def download(self, dest='./'):
        if self.is_file:
            try:
                print(f'Downloading {self.name} to {dest}')
                self.obj.GetContentFile(dest)
                #Avoid too many open files.
                for c in self.obj.http.connections.values():
                    c.close()
            except:
                print('Error. Likely, either downloading this file is impossible (e.g., there is no download link), or destination path does not exist.')
        else:
            print('File is a directory - cannot download.')
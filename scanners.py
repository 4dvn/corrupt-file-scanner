from xlrd import open_workbook, XLRDError

import os

def dir_walker(directory):
    filecount = 0
    for root, dirs, files in os.walk(directory, topdown=False):
        for name in files:
            #print(os.path.join(root, name))
            filecount += 1
            if filecount % 100 == 0:
                print(filecount)
            yield os.path.join(root, name)
        # for name in dirs:
        #     print(os.path.join(root, name))


def check_excel(filename):
    '''
    example
    for f in dir_walker("/Users/vincentdavis/Downloads"):
    check_excel(f)
    '''
    if os.path.splitext(filename)[-1].lower()== ".xlsx":
        try:
            open_workbook(filename)
        except XLRDError:
            print("Exception: " + filename)
            return False
        else:
            #print("True: " + filename)
            return True
    # else:
    #     print(os.path.splitext(filename))

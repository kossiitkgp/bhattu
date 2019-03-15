"""
This script generates .txt from the secrets/Contacts repo.
The name of the .txt file will be the same as that of the .csv file used.
Please provide the path to the Contacts folder while running the script.
e.g:    python autogen.py ../secrets/Contacts
Note: Latest year = freshers, latest - 1 = executives, <latest - 2 = seniors, hyphen joined filename = Alumni
"""

import os, os.path, sys, glob

pathname = sys.argv[1]
filelist = glob.glob(pathname + "*.csv")

namemap = dict()
yearlist = list()

for csv in filelist:
    f = os.path.basename(csv)[:-4]
    if '-' in f:
        #Many old year members punched into one file. Must be our respected alumni.
        namemap[f] = "alumni"
    else:
        yearlist.append(int(f))

yearlist.sort()
namemap[str(yearlist[-1])] = "freshers"
namemap[str(yearlist[-2])] = "executives"
for i in yearlist[:-2]:
    namemap[str(i)] = "seniors"


for csv in filelist:
    f = open(csv, "r")
    w = open(namemap[os.path.basename(csv)[:-4]] + ".txt", "w")

    f.readline()
    for line in f.readlines():
        handle = line.split(",")[5]
        handle = handle.strip()
        handle = handle.split("/")[0]
        w.write(handle+'\n')

print ".txt files generated!. Do you want to run json_maker.py and main.py?"
choice = str(raw_input(" [y/n] "))

if choice == "y":
    os.system("python json_maker.py")
    os.system("python main.py")
elif choice == "n":
    print "Bye!"
else:
    print "Unknown choice entered! Aborting"

print "\n"











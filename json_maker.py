import json
data={}
while (True):
    name=raw_input("Enter name of file without .txt (enter 0 to quit): ")
    if name[0]=='0': break
    myfile = open(str(name)+".txt", "r")
    while (True):
        line=myfile.readline()
        if not line: break
        line=line[:-1]
        try:
            data[name].append(line)
        except:
            data[name]=[]
            data[name].append(line)
    myfile.close()
print data
myfile = open("data.json", "w")
myfile.write(json.dumps(data, indent=4))
myfile.close()

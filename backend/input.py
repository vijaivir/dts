import requests
import sys

apiUrl = "http://134.87.32.119:5001";


def createCommand(line):
    c = line.split(',')
    cmd = c[0].split(" ")[1]
    
    if(cmd == "QUOTE"):
        requests.get(apiUrl + "/quote")

    elif(cmd == "ADD"):
        requests.post()

    elif(cmd == "DISPLAY_SUMMARY"):
        print(cmd)

    elif(cmd == "BUY"):
        print(cmd)

    elif(cmd == "COMMIT_BUY"):
        print(cmd)

    elif(cmd == "SET_BUY_TRIGGER"):
        print(cmd)

    elif(cmd == "CANCEL_BUY"):
        print(cmd)

    elif(cmd == "CANCEL_SET_BUY"):
        print(cmd)
    
    elif(cmd == "SELL"):
        print(cmd)

    elif(cmd == "COMMIT_SELL"):
        print(cmd)

    elif(cmd == "SET_SELL_TRIGGER"):
        print(cmd)

    elif(cmd == "CANCEL_SELL"):
        print(cmd)

    elif(cmd == "CANCEL_SET_SELL"):
        print(cmd)

    elif(cmd == "DUMPLOG"):
        print(cmd)


def readInputFile(fileName):
    with open(fileName, "r") as f:
        for line in f:
            createCommand(line)

if __name__ =="__main__":
    fileName = sys.argv[1]
    readInputFile(fileName)
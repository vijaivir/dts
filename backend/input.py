import requests
import sys
import time

apiUrl = "http://localhost"


def createCommand(line, count):
    c = line.split(',')
    trxNum = count
    cmd = c[0].split(" ")[1]

    print(cmd, trxNum)
    
    if(cmd == "QUOTE"):
        requests.post(apiUrl + "/quote", json={'cmd':cmd, 'username':c[1], 'sym':c[2]})

    elif(cmd == "ADD"):
        requests.post(apiUrl + "/add", json={'cmd':cmd, 'username':c[1], 'amount':c[2], 'trxNum':trxNum})

    elif(cmd == "BUY"):
        requests.post(apiUrl + "/buy", json={'cmd':cmd, 'username':c[1], 'sym':c[2] , 'amount':c[3], 'trxNum':trxNum})
        
    elif(cmd == "COMMIT_BUY"):
        requests.post(apiUrl + "/commit_buy", json={'cmd':cmd, 'username':c[1], 'trxNum':trxNum})

    elif(cmd == "SET_BUY_TRIGGER"):
        requests.post(apiUrl + "/set_buy_trigger", json={'cmd':cmd, 'username':c[1], 'sym':c[2], 'amount':c[3], 'trxNum':trxNum})

    elif(cmd == "SET_BUY_AMOUNT"):
        requests.post(apiUrl + "/set_buy_amount", json={'cmd':cmd, 'username':c[1], 'sym':c[2], 'amount':c[3], 'trxNum':trxNum})

    elif(cmd == "CANCEL_BUY"):
        requests.post(apiUrl + "/cancel_buy", json={'cmd':cmd, 'username':c[1], 'trxNum':trxNum})

    elif(cmd == "CANCEL_SET_BUY"):
        requests.post(apiUrl + "/cancel_set_buy", json={'cmd':cmd, 'username':c[1], 'sym':c[2], 'trxNum':trxNum})
    
    elif(cmd == "SELL"):
        requests.post(apiUrl + "/sell", json={'cmd':cmd, 'username':c[1], 'sym':c[2], 'amount':c[3], 'trxNum':trxNum})

    elif(cmd == "COMMIT_SELL"):
        requests.post(apiUrl + "/commit_sell", json={'cmd':cmd, 'username':c[1], 'trxNum':trxNum})

    elif(cmd == "SET_SELL_TRIGGER"):
        requests.post(apiUrl + "/set_sell_trigger", json={'cmd':cmd, 'username':c[1], 'sym':c[2], 'amount':c[3], 'trxNum':trxNum})

    elif(cmd == "SET_SELL_AMOUNT"):
        requests.post(apiUrl + "/set_sell_amount", json={'cmd':cmd, 'username':c[1], 'sym':c[2], 'amount':c[3], 'trxNum':trxNum})

    elif(cmd == "CANCEL_SELL"):
        requests.post(apiUrl + "/cancel_sell", json={'cmd':cmd, 'username':c[1], 'trxNum':trxNum})

    elif(cmd == "CANCEL_SET_SELL"):
        requests.post(apiUrl + "/cancel_set_sell", json={'cmd':cmd, 'username':c[1], 'sym':c[2], 'trxNum':trxNum})

    elif(cmd == "DUMPLOG"):
        if len(c) == 2:
            requests.post(apiUrl + "/dumplog", json={'filename':c[1]})
        else:
            requests.post(apiUrl + "/dumplog", json={'username':c[1], 'filename':c[2]})

    elif(cmd == "DISPLAY_SUMMARY"):
        requests.post(apiUrl + "/display_summary", json={'username':c[1], 'trxNum':trxNum})


def readInputFile(fileName):
    with open(fileName, "r") as f:
        count = 1
        for line in f:
            line = line.strip().rstrip()
            createCommand(line, count)
            count = count + 1

if __name__ =="__main__":
    fileName = sys.argv[1]
    start = time.perf_counter()
    readInputFile(fileName)
    stop = time.perf_counter()
    print("time taken:", stop - start)
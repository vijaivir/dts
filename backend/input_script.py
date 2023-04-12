import requests
import sys
import time

apiUrl = "http://127.0.0.1"
sell = '/sell'
buy = '/buy'
user = '/user_utils'

all_requests = []

print_flag = 1

def createCommand(line, count):
    c = line.split(',')
    trxNum = count
    cmd = c[0].split(" ")[1]

    # if print_flag:
    #     print(cmd, trxNum)
    
    c[1] = c[1].strip()
    # TODO need a separate quote server count
    if(cmd == "QUOTE"):
        requests.post(apiUrl + user + "/quote", json={'cmd':cmd, 'username':c[1], 'sym':c[2]})

    elif(cmd == "ADD"):
        requests.post(apiUrl + user + "/add", json={'cmd':cmd, 'username':c[1], 'amount':float(c[2]), 'trxNum':trxNum})

    elif(cmd == "BUY"):
        requests.post(apiUrl + buy + "/buy", json={'cmd':cmd, 'username':c[1], 'sym':c[2] , 'amount':float(c[3]), 'trxNum':trxNum})
        
    elif(cmd == "COMMIT_BUY"):
        requests.post(apiUrl + buy + "/commit_buy", json={'cmd':cmd, 'username':c[1], 'trxNum':trxNum})

    elif(cmd == "SET_BUY_TRIGGER"):
        requests.post(apiUrl + buy + "/set_buy_trigger", json={'cmd':cmd, 'username':c[1], 'sym':c[2], 'amount':float(c[3]), 'trxNum':trxNum})

    elif(cmd == "SET_BUY_AMOUNT"):
        requests.post(apiUrl + buy + "/set_buy_amount", json={'cmd':cmd, 'username':c[1], 'sym':c[2], 'amount':float(c[3]), 'trxNum':trxNum})

    elif(cmd == "CANCEL_BUY"):
        requests.post(apiUrl + buy + "/cancel_buy", json={'cmd':cmd, 'username':c[1], 'trxNum':trxNum})

    elif(cmd == "CANCEL_SET_BUY"):
        requests.post(apiUrl + buy + "/cancel_set_buy", json={'cmd':cmd, 'username':c[1], 'sym':c[2], 'trxNum':trxNum})
    
    elif(cmd == "SELL"):
        requests.post(apiUrl + sell + "/sell", json={'cmd':cmd, 'username':c[1], 'sym':c[2], 'amount':float(c[3]), 'trxNum':trxNum})

    elif(cmd == "COMMIT_SELL"):
        requests.post(apiUrl + sell + "/commit_sell", json={'cmd':cmd, 'username':c[1], 'trxNum':trxNum})

    elif(cmd == "SET_SELL_TRIGGER"):
        requests.post(apiUrl + sell + "/set_sell_trigger", json={'cmd':cmd, 'username':c[1], 'sym':c[2], 'amount':float(c[3]), 'trxNum':trxNum})

    elif(cmd == "SET_SELL_AMOUNT"):
        requests.post(apiUrl + sell + "/set_sell_amount", json={'cmd':cmd, 'username':c[1], 'sym':c[2], 'amount':float(c[3]), 'trxNum':trxNum})

    elif(cmd == "CANCEL_SELL"):
        requests.post(apiUrl + sell + "/cancel_sell", json={'cmd':cmd, 'username':c[1], 'trxNum':trxNum})

    elif(cmd == "CANCEL_SET_SELL"):
        requests.post(apiUrl + sell + "/cancel_set_sell", json={'cmd':cmd, 'username':c[1], 'sym':c[2], 'trxNum':trxNum})

    elif(cmd == "DUMPLOG"):
        if len(c) == 2:
            requests.post(apiUrl + user + "/dumplog", json={'filename':c[1]})
        else:
            requests.post(apiUrl + user + "/dumplog", json={'username':c[1], 'filename':c[2]})

    elif(cmd == "DISPLAY_SUMMARY"):
        requests.post(apiUrl + user + "/display_summary", json={'username':c[1],'trxNum':trxNum})


def sendrequests():
    # print(all_requests)
    start = time.perf_counter()
    results = requests.map(all_requests)
    stop = time.perf_counter()
    print(f"finished in {stop-start} seconds")

def readInputFile(fileName):
    with open(fileName, "r") as f:
        count = 0
        for line in f:
            createCommand(line, count)
            count = count + 1

if __name__ =="__main__":
    fileName = sys.argv[1]
    if len(sys.argv) > 2:
        print_flag = int(sys.argv[2])

    start = time.perf_counter()
    readInputFile(fileName)
    stop = time.perf_counter()
    print(f"finished in {stop-start} seconds")
    # all_requests = set(all_requests)
    # sendrequests()

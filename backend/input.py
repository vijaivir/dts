import requests
import sys

apiUrl = "http://localhost"
apuUrlBuy = "http://localhost/buy"
apuUrlSell = "http://localhost/sell"



def createCommand(line, count):
    c = line.split(',')
    trxNum = count
    cmd = c[0].split(" ")[1]

    print(cmd, trxNum)
    
    # TODO need a separate quote server count
    if(cmd == "QUOTE"):
        requests.post(apuUrlBuy + "/quote",
                      json={'cmd': cmd, 'username': c[1], 'sym': c[2]})

    elif(cmd == "ADD"):
        requests.post(apuUrlBuy + "/add",
                      json={'cmd': cmd, 'username': c[1], 'amount': c[2], 'trxNum': trxNum})

    elif(cmd == "BUY"):
        requests.post(apuUrlBuy + "/buy", json={
                      'cmd': cmd, 'username': c[1], 'sym': c[2], 'amount': c[3], 'trxNum': trxNum})
        
    elif(cmd == "COMMIT_BUY"):
        requests.post(apuUrlBuy + "/commit_buy",
                      json={'cmd': cmd, 'username': c[1], 'trxNum': trxNum})

    elif(cmd == "SET_BUY_TRIGGER"):
        requests.post(apuUrlBuy + "/set_buy_trigger", json={
                      'cmd': cmd, 'username': c[1], 'sym': c[2], 'amount': c[3], 'trxNum': trxNum})

    elif(cmd == "SET_BUY_AMOUNT"):
        requests.post(apuUrlBuy + "/set_buy_amount", json={
                      'cmd': cmd, 'username': c[1], 'sym': c[2], 'amount': c[3], 'trxNum': trxNum})

    elif(cmd == "CANCEL_BUY"):
        requests.post(apuUrlBuy + "/cancel_buy",
                      json={'cmd': cmd, 'username': c[1], 'trxNum': trxNum})

    elif(cmd == "CANCEL_SET_BUY"):
        requests.post(apuUrlBuy + "/cancel_set_buy",
                      json={'cmd': cmd, 'username': c[1], 'sym': c[2], 'trxNum': trxNum})
    
    elif(cmd == "SELL"):
        requests.post(apuUrlSell + "/sell", json={
                      'cmd': cmd, 'username': c[1], 'sym': c[2], 'amount': c[3], 'trxNum': trxNum})

    elif(cmd == "COMMIT_SELL"):
        requests.post(apuUrlSell + "/commit_sell",
                      json={'cmd': cmd, 'username': c[1], 'trxNum': trxNum})

    elif(cmd == "SET_SELL_TRIGGER"):
        requests.post(apuUrlSell + "/set_sell_trigger", json={
                      'cmd': cmd, 'username': c[1], 'sym': c[2], 'amount': c[3], 'trxNum': trxNum})

    elif(cmd == "SET_SELL_AMOUNT"):
        requests.post(apuUrlSell + "/set_sell_amount", json={
                      'cmd': cmd, 'username': c[1], 'sym': c[2], 'amount': c[3], 'trxNum': trxNum})

    elif(cmd == "CANCEL_SELL"):
        requests.post(apuUrlSell + "/cancel_sell",
                      json={'cmd': cmd, 'username': c[1], 'trxNum': trxNum})

    elif(cmd == "CANCEL_SET_SELL"):
        requests.post(apuUrlSell + "/cancel_set_sell",
                      json={'cmd': cmd, 'username': c[1], 'sym': c[2], 'trxNum': trxNum})

    elif(cmd == "DUMPLOG"):
        if len(c) == 2:
            requests.post(apuUrlBuy + "/dumplog", json={'filename': c[1]})
        else:
            requests.post(apuUrlBuy + "/dumplog",
                          json={'username': c[1], 'filename': c[2]})

    elif(cmd == "DISPLAY_SUMMARY"):
        requests.post(apuUrlBuy + "/display_summary",
                      json={'username': c[1], 'trxNum': trxNum})


def readInputFile(fileName):
    with open(fileName, "r") as f:
        count = 0
        for line in f:
            line = line.strip().rstrip()
            createCommand(line, count)
            count = count + 1

if __name__ =="__main__":
    fileName = sys.argv[1]
    readInputFile(fileName)
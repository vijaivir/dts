import requests
import sys
import asyncio
import time

apiUrl = "http://localhost"


async def createCommand(line, count):
    c = line.split(',')
    trxNum = count
    cmd = c[0].split(" ")[1]

    #print(cmd, trxNum)
    
    if(cmd == "QUOTE"):
        return requests.post(apiUrl + "/quote", json={'cmd':cmd, 'username':c[1], 'sym':c[2]})

    elif(cmd == "ADD"):
        return requests.post(apiUrl + "/add", json={'cmd':cmd, 'username':c[1], 'amount':c[2], 'trxNum':trxNum})

    elif(cmd == "BUY"):
        return requests.post(apiUrl + "/buy", json={'cmd':cmd, 'username':c[1], 'sym':c[2] , 'amount':c[3], 'trxNum':trxNum})
        
    elif(cmd == "COMMIT_BUY"):
        return requests.post(apiUrl + "/commit_buy", json={'cmd':cmd, 'username':c[1], 'trxNum':trxNum})

    elif(cmd == "SET_BUY_TRIGGER"):
        return requests.post(apiUrl + "/set_buy_trigger", json={'cmd':cmd, 'username':c[1], 'sym':c[2], 'amount':c[3], 'trxNum':trxNum})

    elif(cmd == "SET_BUY_AMOUNT"):
        return requests.post(apiUrl + "/set_buy_amount", json={'cmd':cmd, 'username':c[1], 'sym':c[2], 'amount':c[3], 'trxNum':trxNum})

    elif(cmd == "CANCEL_BUY"):
        return requests.post(apiUrl + "/cancel_buy", json={'cmd':cmd, 'username':c[1], 'trxNum':trxNum})

    elif(cmd == "CANCEL_SET_BUY"):
        return requests.post(apiUrl + "/cancel_set_buy", json={'cmd':cmd, 'username':c[1], 'sym':c[2], 'trxNum':trxNum})
    
    elif(cmd == "SELL"):
        return requests.post(apiUrl + "/sell", json={'cmd':cmd, 'username':c[1], 'sym':c[2], 'amount':c[3], 'trxNum':trxNum})

    elif(cmd == "COMMIT_SELL"):
        return requests.post(apiUrl + "/commit_sell", json={'cmd':cmd, 'username':c[1], 'trxNum':trxNum})

    elif(cmd == "SET_SELL_TRIGGER"):
        return requests.post(apiUrl + "/set_sell_trigger", json={'cmd':cmd, 'username':c[1], 'sym':c[2], 'amount':c[3], 'trxNum':trxNum})

    elif(cmd == "SET_SELL_AMOUNT"):
        return requests.post(apiUrl + "/set_sell_amount", json={'cmd':cmd, 'username':c[1], 'sym':c[2], 'amount':c[3], 'trxNum':trxNum})

    elif(cmd == "CANCEL_SELL"):
        return requests.post(apiUrl + "/cancel_sell", json={'cmd':cmd, 'username':c[1], 'trxNum':trxNum})

    elif(cmd == "CANCEL_SET_SELL"):
        return requests.post(apiUrl + "/cancel_set_sell", json={'cmd':cmd, 'username':c[1], 'sym':c[2], 'trxNum':trxNum})

    elif(cmd == "DUMPLOG"):
        if len(c) == 2:
            return requests.post(apiUrl + "/dumplog", json={'filename':c[1]})
        else:
            return requests.post(apiUrl + "/dumplog", json={'username':c[1], 'filename':c[2]})

    elif(cmd == "DISPLAY_SUMMARY"):
        return requests.post(apiUrl + "/display_summary", json={'username':c[1], 'trxNum':trxNum})


async def readInputFile(fileName):
    with open(fileName, "r") as f:
        count = 1
        tasks = []
        for line in f:
            line = line.strip().rstrip()
            task = asyncio.create_task(createCommand(line, count))
            tasks.append(task)
            count = count + 1
        res = await asyncio.gather(*tasks)
        return res
    
async def main(fileName):
    res = await readInputFile(fileName)

if __name__ =="__main__":
    fileName = sys.argv[1]
    start = time.perf_counter()
    asyncio.run(main(fileName))
    stop = time.perf_counter()
    print("time taken:", stop - start)
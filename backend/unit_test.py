import unittest
from api import app, client
import time

class UnitTest(unittest.TestCase):

    def setUp(self):
        app.testing = True
        # create a test database and collection
        test_db = client.user_database
        # Create two collections (user_table, transaction_table)
        self.user_table = test_db.user_table
        self.transaction_table = test_db.transaction_table
        self.client = app.test_client()

    def tearDown(self):
        self.user_table.drop()
        self.transaction_table.drop()

    def test_quote(self):
        data = {'cmd':'QUOTE', 'username':'testuser', 'sym':'S', 'trxNum':1 }
        self.client.post('/quote', json=data)

    def test_add(self):
        # valid request - new user
        data = {'cmd':'ADD', 'username':'testuser', 'amount':200, 'trxNum':1 }
        response = self.client.post('/add', json=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'created account')
        self.assertEqual(self.transaction_table.count_documents({}), 1)
        self.assertEqual(self.user_table.find_one({'username':'testuser'})['funds'], 200)
        self.user_table.drop()

        # valid request - existing user
        user = {
            'username':"testuser",
            'funds':500,
            'stocks':[{'sym':'A', 'amount':500}],
            'transactions':[]
        }
        self.user_table.insert_one(user)
        data = {'cmd':'ADD', 'username':'testuser', 'amount':200, 'trxNum':1 }
        response = self.client.post('/add', json=data)
        self.assertEqual(self.transaction_table.count_documents({}), 2)
        self.assertEqual(self.user_table.find_one({'username':'testuser'})['funds'], 700)

    def test_buy(self):
        user = {
            'username':"testuser",
            'funds':500,
            'stocks':[],
            'transactions':[]
        }
        self.user_table.insert_one(user)

        # valid request
        data = {'cmd':'BUY', 'username':'testuser', 'sym':'A', 'amount':200, 'trxNum':1 }
        self.client.post('/buy', json=data)
        self.assertEqual(self.user_table.count_documents({}), 1)
        tx_filter = {"username": data['username'], "transactions.command": "BUY"}
        self.assertEqual(self.user_table.find_one(tx_filter, {"transactions.$": 1})['transactions'][0]['flag'], 'pending')
        
        # invalid request (wrong username)
        data = {'cmd':'BUY', 'username':'testuser1', 'sym':'A', 'amount':200, 'trxNum':1 }
        self.client.post('/buy', json=data)
        self.assertEqual(self.transaction_table.find_one({'username':'testuser1'})['error'], 'The specified user does not exist.')

        # invalid request (insufficient funds)
        self.transaction_table.drop()
        data = {'cmd':'BUY', 'username':'testuser', 'sym':'A', 'amount':600, 'trxNum':1 }
        self.client.post('/buy', json=data)
        self.assertEqual(self.transaction_table.find_one({'username':'testuser', 'type':'errorEvent'})['error'], 'Insufficient funds.')

    def test_commit_buy(self):
        user = {
            'username':"testuser",
            'funds':500,
            'stocks':[{'sym':'A', 'amount':500, 'share':1}],
            'transactions':[{'timestamp':time.time(), 'transactionNum':1, 'command': 'SELL', 'username':'testuser', 'amount':500, 'sym':'A', 'flag':'purchased', 'share':1}]
        }
        self.user_table.insert_one(user)

        # invalid request - no recent BUY transactions
        data = {'cmd':'COMMIT_BUY', 'username':'testuser', 'trxNum':1 }
        self.client.post('/commit_buy', json=data)
        self.assertEqual(self.transaction_table.find_one({'username':'testuser'})['error'], 'No recent BUY transactions.')
        

        # invlaid request - recent BUY but not pending
        self.user_table.update_one({'username':'testuser'}, {'$push': {'transactions': [
            {'timestamp':time.time(), 'transactionNum':2, 'command': 'BUY', 'username':'testuser', 'amount':500, 'sym':'A', 'flag':'complete', 'share':1}
        ]}})
        self.client.post('/commit_buy', json=data)
        self.assertEqual(self.transaction_table.find_one({'username':'testuser'})['error'], 'No recent BUY transactions.')


        # valid request - most recent BUY that is pending (existing stock)
        self.user_table.update_one({'username':'testuser'}, {'$push': {'transactions': 
            {'timestamp':time.time(), 'transactionNum':3, 'command': 'BUY', 'username':'testuser', 'amount':500, 'sym':'A', 'flag':'pending', "share":1}
        }})
        self.user_table.update_one({'username':'testuser'}, {'$push': {'transactions': 
            {'timestamp':time.time(), 'transactionNum':4, 'command': 'BUY', 'username':'testuser', 'amount':200, 'sym':'A', 'flag':'pending', "share":1}
        }})
        # for x in self.user_table.find():
        #     print(x)
        self.client.post('/commit_buy', json=data)
        self.assertEqual(self.transaction_table.count_documents({'command':'COMMIT_BUY', 'type':'accountTransaction'}), 1) #added to transaction_table
        self.assertEqual(self.user_table.find_one({'username':'testuser'})['funds'], 300) # updated user funds
        self.assertEqual(self.user_table.find_one({'username':'testuser'})['stocks'][0]['amount'], 700) # updated stock price
        tx_filter = {"username": data['username'], "transactions.transactionNum": 4}
        self.assertEqual(self.user_table.find_one(tx_filter, {"transactions.$": 1})['transactions'][0]['flag'], 'complete') # check flag set to complete

        # valid request - most recent BUY that is pending (new stock)
        self.user_table.update_one({'username':'testuser'}, {'$push': {'transactions': 
            {'timestamp':time.time(), 'transactionNum':5, 'command': 'BUY', 'username':'testuser', 'amount':50, 'sym':'B', 'flag':'pending', "share":1}
        }})
        self.client.post('/commit_buy', json=data)
        self.assertEqual(self.transaction_table.count_documents({'command':'COMMIT_BUY', 'type':'accountTransaction'}), 2) #added to transaction_table
        self.assertEqual(self.user_table.find_one({'username':'testuser'})['funds'], 250) # updated user funds
        stock_filter = {"username": data['username'], "stocks.sym": 'B'}
        self.assertEqual(self.user_table.find_one(stock_filter, {"stocks.$": 1})['stocks'][0]['amount'], 50)
        self.assertEqual(self.user_table.find_one(stock_filter, {"stocks.$": 1})['stocks'][0]['sym'], "B")
        tx_filter = {"username": data['username'], "transactions.transactionNum": 5}
        self.assertEqual(self.user_table.find_one(tx_filter, {"transactions.$": 1})['transactions'][0]['flag'], 'complete') # check flag set to complete

    def test_cancel_buy(self):
        user = {
            'username':"testuser",
            'funds':500,
            'stocks':[{'sym':'A', 'amount':500}],
            'transactions':[{'timestamp':time.time(), 'transactionNum':1, 'command': 'SELL', 'username':'testuser', 'amount':500, 'sym':'A', 'flag':'purchased'}]
        }
        self.user_table.insert_one(user)

        # invalid request - no recent BUY transactions
        data = {'cmd':'CANCEL_BUY', 'username':'testuser', 'trxNum':1 }
        self.client.post('/cancel_buy', json=data)
        self.assertEqual(self.transaction_table.find_one({'username':'testuser'})['error'], 'No recent BUY transactions.')
        

        # invlaid request - recent BUY but not pending
        self.user_table.update_one({'username':'testuser'}, {'$push': {'transactions': [
            {'timestamp':time.time(), 'transactionNum':2, 'command': 'BUY', 'username':'testuser', 'amount':500, 'sym':'A', 'flag':'complete'}
        ]}})
        self.client.post('/cancel_buy', json=data)
        self.assertEqual(self.transaction_table.find_one({'username':'testuser'})['error'], 'No recent BUY transactions.')


        # valid request - most recent BUY that is pending
        self.user_table.update_one({'username':'testuser'}, {'$push': {'transactions': 
            {'timestamp':time.time(), 'transactionNum':3, 'command': 'BUY', 'username':'testuser', 'amount':500, 'sym':'A', 'flag':'pending'}
        }})
        self.user_table.update_one({'username':'testuser'}, {'$push': {'transactions': 
            {'timestamp':time.time(), 'transactionNum':4, 'command': 'BUY', 'username':'testuser', 'amount':200, 'sym':'A', 'flag':'pending'}
        }})
        self.client.post('/cancel_buy', json=data)
        self.assertEqual(self.transaction_table.count_documents({'command':'CANCEL_BUY', 'type':'accountTransaction'}), 1) #added to transaction_table
        tx_filter = {"username": data['username'], "transactions.transactionNum": 4}
        self.assertEqual(self.user_table.find_one(tx_filter, {"transactions.$": 1})['transactions'][0]['flag'], 'cancelled') # check flag set to complete

    def test_set_buy_amount(self):
        user = {
            'username':"testuser",
            'funds':500,
            'stocks':[{'sym':'A', 'amount':500}],
            'reserved_buy':[],
            'transactions':[]
        }
        self.user_table.insert_one(user)
        
        # invalid request - insufficient funds
        data = {'cmd':"SET_BUY_AMOUNT", 'username':'testuser', 'sym':'A', 'amount':1000, 'trxNum':1}
        self.client.post('/set_buy_amount', json=data)
        self.assertEqual(self.transaction_table.find_one({'username':'testuser'})['error'], 'Insufficient Funds.')

        # valid request 
        data = {'cmd':"SET_BUY_AMOUNT", 'username':'testuser', 'sym':'A', 'amount':200, 'trxNum':1}
        self.client.post('/set_buy_amount', json=data)
        filter = {'username': data['username']}
        self.assertEqual(self.user_table.find_one(filter)['reserved_buy'][0]['sym'], 'A')
        self.assertEqual(self.user_table.find_one(filter)['reserved_buy'][0]['amount'], 200)

    def test_set_buy_trigger(self):
        user = {
            'username':"testuser",
            'funds':500,
            'stocks':[{'sym':'A', 'amount':500}],
            'reserved_buy':[],
            'transactions':[]
        }
        self.user_table.insert_one(user)
        
        # invalid request - no set buy amount
        data = {'cmd':"SET_BUY_TRIGGER", 'username':'testuser', 'sym':'A', 'amount':50, 'trxNum':1}
        self.client.post('/set_buy_trigger', json=data)
        self.assertEqual(self.transaction_table.find_one({'username':'testuser'})['error'], "No prereq SET_BUY_AMOUNT")

        # valid request 
        filter = {'username': data['username']}
        self.user_table.update_one(filter, {"$push": { "reserved_buy": {"sym":"A", "amount":200}}})
        data = {'cmd':"SET_BUY_TRIGGER", 'username':'testuser', 'sym':'A', 'amount':50, 'trxNum':1}
        self.client.post('/set_buy_trigger', json=data)
        # for x in self.user_table.find():
        #     print(x)
        self.assertEqual(self.user_table.find_one(filter)['reserved_buy'][0]['trigger_price'], 50)

    def test_cancel_set_buy(self):
        user = {
            'username':"testuser",
            'funds':500,
            'stocks':[],
            'reserved_buy':[{'sym':'A', 'amount':200}],
            'transactions':[]
        }
        self.user_table.insert_one(user)

        # invalid request
        data = {'cmd':"CANCEL_SET_BUY", 'username':'testuser', 'sym':'B', 'trxNum':1}
        self.client.post('/cancel_set_buy', json=data)
        self.assertEqual(self.transaction_table.find_one({'username':'testuser'})['error'], 'No prereq SET_BUY_AMOUNT')

        # valid request
        data = {'cmd':"CANCEL_SET_BUY", 'username':'testuser', 'sym':'A', 'trxNum':1}
        self.client.post('/cancel_set_buy', json=data)
        self.assertEqual(self.user_table.find_one({'username':'testuser'})['funds'], 700)


    def test_sell(self):
        user = {
            'username':"testuser",
            'stocks':[{'sym':'A', 'amount':500}],
            'transactions':[]
        }
        self.user_table.insert_one(user)

        # valid request
        data = {'cmd':'SELL', 'username':'testuser', 'sym':'A', 'amount':200, 'trxNum':1 }
        self.client.post('/sell', json=data)
        self.assertEqual(self.user_table.count_documents({}), 1)
        tx_filter = {"username": data['username'], "transactions.command": "SELL"}
        self.assertEqual(self.user_table.find_one(tx_filter, {"transactions.$": 1})['transactions'][0]['flag'], 'pending')

        # invalid request (wrong username)
        data = {'cmd':'SELL', 'username':'testuser1', 'sym':'A', 'amount':200, 'trxNum':1 }
        self.client.post('/sell', json=data)
        self.assertEqual(self.transaction_table.find_one({'username':'testuser1'})['error'], 'The specified user does not exist.')

        # invalid request (insufficient stock)
        self.transaction_table.drop()
        data = {'cmd':'SELL', 'username':'testuser', 'sym':'A', 'amount':600, 'trxNum':1 }
        self.client.post('/sell', json=data)
        self.assertEqual(self.transaction_table.find_one({'username':'testuser', 'type':'errorEvent'})['error'], 'Insufficient stock amount.')

    # def test_commit_sell(self):
    #     user = {
    #         'username':"testuser",
    #         'funds':500,
    #         'stocks':[{'sym':'A', 'amount':500}],
    #         'transactions':[{'timestamp':time.time(), 'transactionNum':1, 'command': 'BUY', 'username':'testuser', 'amount':500, 'sym':'A', 'flag':'purchased'}]
    #     }
    #     self.user_table.insert_one(user)

    #     # invalid request - no recent SELL transactions
    #     data = {'cmd':'COMMIT_SELL', 'username':'testuser', 'trxNum':1 }
    #     self.client.post('/commit_sell', json=data)
    #     self.assertEqual(self.transaction_table.find_one({'username':'testuser'})['error'], 'No recent SELL transactions.')
        

    #     # invlaid request - recent SELL but not pending
    #     self.user_table.update_one({'username':'testuser'}, {'$push': {'transactions': [
    #         {'timestamp':time.time(), 'transactionNum':2, 'command': 'SELL', 'username':'testuser', 'amount':500, 'sym':'A', 'flag':'complete'}
    #     ]}})
    #     self.client.post('/commit_sell', json=data)
    #     self.assertEqual(self.transaction_table.find_one({'username':'testuser'})['error'], 'No recent SELL transactions.')


    #     # valid request - most recent SELL that is pending
    #     self.user_table.update_one({'username':'testuser'}, {'$push': {'transactions': 
    #         {'timestamp':time.time(), 'transactionNum':3, 'command': 'SELL', 'username':'testuser', 'amount':500, 'sym':'A', 'flag':'pending'}
    #     }})
    #     self.user_table.update_one({'username':'testuser'}, {'$push': {'transactions': 
    #         {'timestamp':time.time(), 'transactionNum':4, 'command': 'SELL', 'username':'testuser', 'amount':200, 'sym':'A', 'flag':'pending'}
    #     }})
    #     self.client.post('/commit_sell', json=data)
    #     self.assertEqual(self.transaction_table.count_documents({'command':'COMMIT_SELL', 'type':'accountTransaction'}), 1) #added to transaction_table
    #     self.assertEqual(self.user_table.find_one({'username':'testuser'})['funds'], 700) # updated user funds
    #     self.assertEqual(self.user_table.find_one({'username':'testuser'})['stocks'][0]['amount'], 300) # updated stock price
    #     tx_filter = {"username": data['username'], "transactions.transactionNum": 4}
    #     self.assertEqual(self.user_table.find_one(tx_filter, {"transactions.$": 1})['transactions'][0]['flag'], 'complete') # check flag set to complete

    # def test_cancel_sell(self):
    #     user = {
    #         'username':"testuser",
    #         'funds':500,
    #         'stocks':[{'sym':'A', 'amount':500}],
    #         'transactions':[{'timestamp':time.time(), 'transactionNum':1, 'command': 'BUY', 'username':'testuser', 'amount':500, 'sym':'A', 'flag':'purchased'}]
    #     }
    #     self.user_table.insert_one(user)

    #     # invalid request - no recent SELL transactions
    #     data = {'cmd':'CANCEL_SELL', 'username':'testuser', 'trxNum':1 }
    #     self.client.post('/cancel_sell', json=data)
    #     self.assertEqual(self.transaction_table.find_one({'username':'testuser'})['error'], 'No recent SELL transactions.')
        

    #     # invlaid request - recent SELL but not pending
    #     self.user_table.update_one({'username':'testuser'}, {'$push': {'transactions': [
    #         {'timestamp':time.time(), 'transactionNum':2, 'command': 'SELL', 'username':'testuser', 'amount':500, 'sym':'A', 'flag':'complete'}
    #     ]}})
    #     self.client.post('/cancel_sell', json=data)
    #     self.assertEqual(self.transaction_table.find_one({'username':'testuser'})['error'], 'No recent SELL transactions.')


    #     # valid request - most recent SELL that is pending
    #     self.user_table.update_one({'username':'testuser'}, {'$push': {'transactions': 
    #         {'timestamp':time.time(), 'transactionNum':3, 'command': 'SELL', 'username':'testuser', 'amount':500, 'sym':'A', 'flag':'pending'}
    #     }})
    #     self.user_table.update_one({'username':'testuser'}, {'$push': {'transactions': 
    #         {'timestamp':time.time(), 'transactionNum':4, 'command': 'SELL', 'username':'testuser', 'amount':200, 'sym':'A', 'flag':'pending'}
    #     }})
    #     self.client.post('/cancel_sell', json=data)
    #     self.assertEqual(self.transaction_table.count_documents({'command':'CANCEL_SELL', 'type':'accountTransaction'}), 1) #added to transaction_table
    #     tx_filter = {"username": data['username'], "transactions.transactionNum": 4}
    #     self.assertEqual(self.user_table.find_one(tx_filter, {"transactions.$": 1})['transactions'][0]['flag'], 'cancelled') # check flag set to complete

    # def test_set_sell_amount(self):
    #     user = {
    #         'username':"testuser",
    #         'funds':500,
    #         'reserved':[],
    #         'stocks':[{'sym':'A', 'amount':500}],
    #         'transactions':[]
    #     }
    #     self.user_table.insert_one(user)

    #     # invalid request - not enough stock
    #     data = {'cmd':'SET_SELL_AMOUNT', 'username':'testuser', 'sym':'A', 'amount':600, 'trxNum':1 }
    #     self.client.post('/set_sell_amount', json=data)
    #     self.assertEqual(self.transaction_table.find_one({'username':'testuser'})['error'], 'Not enough stock.')

    #     # valid request - enough stock
    #     data = {'cmd':'SET_SELL_AMOUNT', 'username':'testuser', 'sym':'A', 'amount':400, 'trxNum':1 }
    #     response = self.client.post('/set_sell_amount', json=data)
    #     self.assertEqual(response.data, b'successfully set sell amount')
    #     self.assertEqual(self.user_table.find_one({'username':'testuser'})['reserved_sell'][0]['amount'], 400)
        

    # def test_set_sell_trigger(self):
    #     user = {
    #         'username':"testuser",
    #         'funds':500,
    #         'reserved_sell':[{'sym':'A', 'amount':500}],
    #         'stocks':[{'sym':'A', 'amount':500}],
    #         'transactions':[]
    #     }
    #     self.user_table.insert_one(user)

    #     # invalid request - no sell amount
    #     data = {'cmd':'SET_SELL_TRIGGER', 'username':'testuser', 'sym':'B', 'amount':600, 'trxNum':1 }
    #     self.client.post('/set_sell_trigger', json=data)
    #     self.assertEqual(self.transaction_table.find_one({'username':'testuser'})['error'], 'Set sell amount first.')

    #     # # valid request - sell amount set
    #     data = {'cmd':'SET_SELL_TRIGGER', 'username':'testuser', 'sym':'A', 'amount':50, 'trxNum':1 }
    #     response = self.client.post('/set_sell_trigger', json=data)
    #     self.assertEqual(response.data, b'successfully set sell trigger')
    #     self.assertEqual(self.user_table.find_one({'username':'testuser'})['reserved_sell'][0]['trigger'], 50)

    # def test_dumplog(self):
    #     user = {
    #         'username':"testuser",
    #         'funds':500,
    #         'reserved_sell':[{'sym':'A', 'amount':500}],
    #         'stocks':[{'sym':'A', 'amount':500}],
    #         'transactions':[
    #         {'timestamp':time.time(), 'transactionNum':3, 'command': 'BUY', 'username':'testuser', 'amount':500, 'sym':'A', 'flag':'pending', 'type':'accountTransaction', 'server':"TS1"},
    #         {'timestamp':time.time(), 'transactionNum':3, 'command': 'SELL', 'username':'testuser', 'amount':500, 'sym':'A', 'flag':'pending', 'type':'accountTransaction', 'server':"TS1"},
    #         {'timestamp':time.time(), 'transactionNum':3, 'command': 'BUY', 'username':'testuser', 'amount':500, 'sym':'A', 'flag':'pending', 'type':'accountTransaction', 'server':"TS1"},
    #         {'timestamp':time.time(), 'transactionNum':3, 'command': 'SELL', 'username':'testuser', 'amount':500, 'sym':'A', 'error':'this is an error', 'type':'errorEvent', 'server':"TS1"}
    #         ]
    #     }
    #     self.user_table.insert_one(user)
    #     data = {'cmd':'DUMPLOG', 'filename':'file', 'username':'testuser', 'trxNum':1 }
    #     self.client.post('/dumplog', json=data)

if __name__ == '__main__':
    unittest.main()

# Day Trading System (DTS) - Documentation

The DTS application allows users to perform various trading transactions such as adding funds, buying stocks, selling stocks, setting automated buy and sell points, and viewing a summary of their transactions. 

To start the application run:

```
docker compose up
```

To test the functionality using user scripts, open another terminal and run:

```
cd backend
python3 input.py ./commands/user1.txt
```

Additional user scripts have been included that simulates the application beign run by 1-10,000 users. 

To navigate the application using the frontend, open another terminal and run:

```
cd frontend
npm install
npm start
```

## Components

### Frontend
The UI is designed using React for simple state management. The UI is updated whenever an event of interest occurs that triggers a state change, such as an API call or selecting an action such as buying or selling stocks, resulting in a responsive and interactive UI. All the components within the UI are created usign HTML and CSS and interactions with the backend are handled through the Axios library via HTTP requests.

![Login](https://user-images.githubusercontent.com/91633223/231275899-7283a789-b38b-49a7-bb5b-af36381ed417.png)

*Login Page*

![Buy](https://user-images.githubusercontent.com/91633223/231276924-f3ce7d1a-1dbc-4fe1-8cfb-c68e9177151a.png)

*Buy View*

![Sell](https://user-images.githubusercontent.com/91633223/231277029-34ee94a2-c043-4aaf-9244-358b6b5b7cf8.png)

*Sell View*

### Database

All the information about the system is stored using MongoDB hosted in a docker container. There are two collections, a `user_table` and a `transaction_table` with the following schema respectively:

```
{
	username: string,
	funds: float,
	stocks: [],
	reserved_buy: [],
	reserved_sell: [],
	transactions: []
}
```

```
{
	timestamp: seconds,
	command: string,
	username: string,
	transactionNum: int,
	type: string,
	server: string,
	amount: float (optional),
	sym: string (optional),
	share: int (optional),
	flag: string (optional),
        cryptokey: string(optional),
        quoteServerTime: seconds, 
}
```

### Cache

A Redis cache is used to improve response times by caching frequently accessed stock prices. When a microservice requests a quote price it first checks the Redis cache for the stock symbol, if it exists in the cache it is immediately returned to the microservice. If a stock symbol does not exist in the Redis cache, a quote request is sent to the Flask quote server and that symbol is cached with an expiry time of 120 seconds.

### NGINX Load Balancer

The DTS utilizes an NGINX load balancer that listens on port 80 and redirects requests as appropriate based on the url being accessed. NGINX is configured to use an IP Hash distribution algorithm so that the load is distributed evenly based on the IP address. 

### Microservices

The application is divided into three Python Flask microservices: buy, sell, and user utilities.

The buy microservice handles all buy related functionalities and supports the following commands:
- BUY
- COMMIT BUY
- CANCEL BUY
- SET BUY AMOUNT
- SET BUY TRIGGER
- CANCEL SET BUY

The sell microservice handles all sell related functionalities and supports the following commands:
- SELL
- COMMIT SELL
- CANCEL SELL
- SET SELL AMOUNT
- SET SELL TRIGGER
- CANCEL SET SELL

The user utilities microservice handles all functions related to a user’s account and some helper functions:
- QUOTE
- RECENT TRANSACTIONS
- DUMPLOG
- DISPLAY SUMMARY

### Quote Server

The DTS implements a custom quote server that accepts a stock symbol and returns a randomly generated stock price and a cryptokey. The quote server is hosted in a docker container and created using the Python Flask web framework similar to the microservices. 

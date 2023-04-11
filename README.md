# Day Trading System (DTS) - Documentation

The DTS application allows users to perform various trading transactions such as adding funds, buying stocks, selling stocks, setting automated buy and sell points, and viewing a summary of their transactions. 

To test the application using demo scripts, run:

```
docker compose up
```

Open another terminal and run:

```
cd backend
python3 input.py ./commands/user1.txt
```

Additional user scripts have been included that simulates the application beign run by 1-10,000 users. 

To navigate the application using the frontend, run:

```
docker compose up
```

Open another terminal and run:

```
cd frontend
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



### NGINX Load Balancer

### Microservices

### Quote Server

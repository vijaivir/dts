import React, { useState, useEffect } from "react";
// import { getQuoteService } from "../service";
import axios from "axios";
const apiUserUtilsUrl = "http://127.0.0.1/user_utils/";
const apiBuyUrl = "http://127.0.0.1/buy/";
const apiSellUrl = "http://127.0.0.1/sell/";

const TradingPanel = (props) => {
  const [operation, setOperation] = useState("Buy");
  const [symbol, setSymbol] = useState("");
  const [amount, setAmount] = useState(0);
  const [point, setPoint] = useState(0);
  const [stockPrice, setStockPrice] = useState(0);
  const [submitted, setSubmitted] = useState(false);
  const [commited, setCommited] = useState(false);

  useEffect(() => {
    //get a qoute for the price
    getQuote(symbol);
    //   getQuoteService(props.username, symbol);
    //   setStockPrice(price);
    //   setPoint(price);
  }, [symbol]);

  const getQuote = async (symbol) => {
    const payload = {
      username: props.username,
      sym: symbol,
    };
    console.log(symbol);
    const quote = await axios.post(apiUserUtilsUrl + "quote", payload);
    console.log(quote)
    setStockPrice(quote.data.price);
  };

  const submitOperation = async () => {

    console.log(operation, symbol, amount, point, stockPrice);

    if(operation == "Buy"){
      if(props.funds >= amount){
        //check if there is enough funds
        if(point == stockPrice){
          //buy current price
          const payload = {
            cmd: operation,
            username: props.username,
            sym: symbol,
            amount: amount,
            trxNum: 1,
          }
          const response = await axios.post(apiBuyUrl + "buy", payload);
          console.log(response)
          setSubmitted(true);
        }else{
          //this is a setBuy operation
          // const payloadAmount = {
          //   cmd: operation,
          //   username: props.username,
          //   sym: symbol,
          //   amount: amount,
          //   trxNum: 1,
          // }
          // const payloadTrigger = {
          //   cmd: operation,
          //   username: props.username,
          //   sym: symbol,
          //   amount: stockPrice,
          //   trxNum: 1,
          // }
          // const setBuyAmountResponse = await axios.post(apiBuyUrl + "set_buy_amount", payloadAmount);
          // const setBuyTriggerResponse = await axios.post(apiBuyUrl + "set_buy_trigger", payloadTrigger);
        }
      }else{
        //not enough funds to buy this amount!
        console.log("too broke to complete transaction")
      }
      
        
    }

    if(operation == "Sell"){
      //check their holdings
      if(point == stockPrice){
        //sell current price
        const payload = {
          cmd: operation,
          username: props.username,
          sym: symbol,
          amount: amount,
          trxNum: 1,
        }
        const response = await axios.post(apiSellUrl + "sell", payload);
        console.log(response)
      }
        
    }
      
  };

  const commitOperation = () => {
    //form commited
    setCommited(true);

    //decipher what service to call from state
    console.log("the operation was committed");
  };

  const renderSubmitButtons = () => {
    return (
      <div>
        {point === stockPrice ? (
          <button onClick={() => submitOperation()}>{operation}</button>
        ) : (
          <button>Set {operation}</button>
        )}
      </div>
    );
  };

  const renderCommitButtons = () => {
    return (
      <div>
        <button onClick={() => setSubmitted(false)}>Cancel</button>
        <button onClick={() => commitOperation()}>Commit {operation}</button>
      </div>
    );
  };

  return (
    <>
      <div>
        <div>
          <span>Operation: </span>
          <select
            value={operation}
            onChange={(e) => setOperation(e.target.value)}
          >
            <option value="Buy">Buy</option>
            <option value="Sell">Sell</option>
          </select>
        </div>
        <div>
          <span>Stock Symbol: </span>
          <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
            <option value="App">App</option>
            <option value="Amz">Amz</option>
            <option value="Bel">Bel</option>
            <option value="Btc">Btc</option>
            <option value="Eth">Eth</option>
            <option value="Ggl">Ggl</option>
          </select>
        </div>
        <div>
          <span>Stock Price: </span>${stockPrice}
        </div>
        <div>
          <span>Amount: $</span>
          <input
            type="number"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
        </div>
        <div>
          <span>{operation} Point: $</span>
          <input
            type="number"
            value={point}
            onChange={(e) => setPoint(e.target.value)}
          />
          <button onClick={() => setPoint(stockPrice)}>set to current</button>
        </div>
        <div>{submitted ? renderCommitButtons() : renderSubmitButtons()}</div>
      </div>
    </>
  );
};

export default TradingPanel;

import React, { useState, useEffect } from "react";
// import { getQuoteService } from "../service";
import axios from "axios";
const apiUrl = "http://127.0.0.1/user_utils/";
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
    const quote = await axios.post(apiUrl + "/quote", payload);
    setStockPrice(quote.data.price);
  };

  const submitOperation = () => {
    //form submitted
    setSubmitted(true);

    //decipher what service to call from state
    //TODO make sure this state cannot be changed from form after submit
    console.log(operation, symbol, amount, point, stockPrice);
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

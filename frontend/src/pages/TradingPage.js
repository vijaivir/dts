import CollapsibleList from "../components/CollapsibleList";
import styles from "../styles.module.css";
import NavBar from "../components/NavBar";
import TradingPanel from "../components/TradingPanel";
import axios from "axios";
import { useEffect, useState } from "react";

const apiUserUtilsUrl = "http://127.0.0.1/user_utils/";



function TradingPage(props) {

  const [funds, setFunds] = useState(0);
  const [stockList, setStockList] = useState([]);
  const [reservedBuy, setReservedBuy] = useState([]);
  const [reservedSell, setReservedSell] = useState([]);
  const [transactions, setTransactions] = useState([]);

  useEffect(() => {
    getUserInfo()
  }, []);

  const parseUserData = async (data) => {

    console.log("yayay")
    setFunds(data.funds)
    setStockList(data.stocks)
    setReservedBuy(data.reserved_buy)
    setReservedSell(data.reserved_sell)
    setTransactions(data.transactions)

    console.log(transactions)

  }

  const getUserInfo = async () => {

    const payload = {
      username: props.username,
      trxNum: 1,
    }

    try {
      const userInfo = await axios.post(apiUserUtilsUrl + "display_summary", payload);
      console.log(userInfo.data)
      //problem with format of data, str using '' instead of "", change backend to send jsonify(obj) not a str(obj)
      parseUserData(JSON.parse(userInfo.data));
      console.log(userInfo);
    } catch (error) {
      console.error("Error fetching user info:", error);
    }

  }

  const pendingTransactions = [
    { operation: "BUY", amount: "75", sym: "App" },
    { operation: "SELL", amount: "40", sym: "Gg" },
    { operation: "BUY", amount: "65", sym: "Amz" },
  ];

  const currentHoldings = [
    { amount: "75", sym: "App" },
    { amount: "40", sym: "Gg" },
    { amount: "65", sym: "Amz" },
  ];

  const transactionHistory = [
    { operation: "BUY", amount: "75", sym: "App", date: "2022-03-08" },
    { operation: "SELL", amount: "40", sym: "Gg", date: "2022-03-08" },
    { operation: "BUY", amount: "65", sym: "Amz", date: "2022-03-08" },
  ];

  return (
    <div>
      <NavBar username={props.username} isLoggedIn={props.isLoggedIn}></NavBar>
      <div className={styles.container}>
        <div className={styles.panel}>
          <TradingPanel username={props.username} funds={funds}></TradingPanel>
        </div>
        <div className={styles.panel}>
          <CollapsibleList
            type={"Pending Transactions"}
            list={reservedBuy}
          ></CollapsibleList>
          <CollapsibleList
            type={"Current Holdings"}
            list={stockList}
          ></CollapsibleList>
          <CollapsibleList
            type={"Transaction History"}
            list={transactions}
          ></CollapsibleList>
        </div>
      </div>
    </div>
  );
}

export default TradingPage;

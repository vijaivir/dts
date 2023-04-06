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

  const refreshUserInfo = () => {
    console.log("rerendering")
    getUserInfo();
  };

  const parseUserData = async (data) => {

    setFunds(data.funds)
    setStockList(data.stocks)
    setReservedBuy(data.reserved_buy)
    setReservedSell(data.reserved_sell)
    setTransactions(data.transactions)

  }

  const getUserInfo = async () => {

    const payload = {
      username: props.username,
      trxNum: 1,
    }

    try {
      const userInfo = await axios.post(apiUserUtilsUrl + "display_summary", payload);
      console.log(userInfo)
      parseUserData(userInfo.data)
      console.log(funds)
      
    } catch (error) {
      console.error("Error fetching user info:", error);
    }

  }

  return (
    <div>
      <NavBar username={props.username} isLoggedIn={props.isLoggedIn} funds={funds}></NavBar>
      <div className={styles.container}>
        <div className={styles.panel}>
          <TradingPanel username={props.username} funds={funds} refreshUserInfo={refreshUserInfo}></TradingPanel>
        </div>
        <div className={styles.panel}>
          <CollapsibleList
            type={"Pending Transactions"}
            list={reservedBuy}
            refreshUserInfo={refreshUserInfo}
          ></CollapsibleList>
          <CollapsibleList
            type={"Current Holdings"}
            list={stockList}
            refreshUserInfo={refreshUserInfo}
          ></CollapsibleList>
          <CollapsibleList
            type={"Transaction History"}
            list={transactions}
            refreshUserInfo={refreshUserInfo}
          ></CollapsibleList>
        </div>
      </div>
    </div>
  );
}

export default TradingPage;

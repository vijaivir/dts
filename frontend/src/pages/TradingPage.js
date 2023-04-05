import CollapsibleList from "../components/CollapsibleList";
import styles from "../styles.module.css";
import NavBar from "../components/NavBar";
import TradingPanel from "../components/TradingPanel";

function TradingPage(props) {
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
          <TradingPanel username={props.username}></TradingPanel>
        </div>
        <div className={styles.panel}>
          <CollapsibleList
            type={"Pending Transactions"}
            list={pendingTransactions}
          ></CollapsibleList>
          <CollapsibleList
            type={"Current Holdings"}
            list={currentHoldings}
          ></CollapsibleList>
          <CollapsibleList
            type={"Transaction History"}
            list={transactionHistory}
          ></CollapsibleList>
        </div>
      </div>
    </div>
  );
}

export default TradingPage;

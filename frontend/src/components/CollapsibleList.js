import React, { useState, useEffect } from "react";
import axios from "axios";
const CollapsibleList = (props) => {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    props.refreshUserInfo()
  }, [isOpen]);

  const toggleList = () => {
    setIsOpen(!isOpen);
  };

  console.log(props.list);

  const cancelSetBuy = async (item) => {
    const payload = {
      username: props.username,
      sym: item.sym,
      cmd: "CANCEL_SET_BUY",
      trxNum: 1,
    };
    const res = await axios.post(
      "http://localhost/buy/cancel_set_buy",
      payload
    );
  };

  return (
    <>
      <div>
        <button onClick={toggleList}>
          {isOpen ? "-" : "+"} {props.type}
        </button>
        {isOpen && props.type === "Pending Transactions" ? (
          <ul>
            {props.list.map((item, index) => (
              <li key={index}>
                {item.command} {item.sym} {item.amount} {item.timestamp}{" "}
                <button onClick={() => cancelSetBuy(item)}>Cancel</button>
              </li>
            ))}
          </ul>
        ) : (
          <ul>
            {props.list.map((item, index) => (
              <li key={index}>
                {item.command} {item.sym} {item.amount} {item.timestamp}
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  );
};

export default CollapsibleList;

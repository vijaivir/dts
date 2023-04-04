import React, { useState } from 'react';
import { Button } from 'react-bootstrap';
import styles from "../styles.module.css"
import {addFundsService} from "../service.js"

const UserNavBarMenu = (props) => {

  const [addAmount, setAddAmount] = useState(0);

  const handleAddFunds = () => {
    addFundsService(props.username, addAmount)
  }

  return (
    <div className='userNav'>
        <>{props.username}</>
        <>{props.amount}</>
        <input type="number" value={addAmount} onChange={(e) => setAddAmount(e.target.value)} />
        <button onClick={() => handleAddFunds()}>+</button>
    </div>
  );
};

export default UserNavBarMenu;
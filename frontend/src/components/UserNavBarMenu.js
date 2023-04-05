import React, { useEffect, useState } from 'react';
import axios from 'axios';

const apiUserUtilsUrl = "http://127.0.0.1/user_utils/";

const UserNavBarMenu = (props) => {

  const [addAmount, setAddAmount] = useState(0);
  const [currentFunds, setCurrentFunds] = useState(props.funds)

  useEffect(() => {
    setCurrentFunds(props.funds);
  }, [props.funds]);

  const handleAddFunds = async () => {
    const payload = {
      username: props.username,
      amount: addAmount,
      trxNum: 1,
      cmd:'ADD',
    }

    const response = await axios.post(apiUserUtilsUrl + "add", payload);
    console.log(response)
    setCurrentFunds(parseFloat(currentFunds)+parseFloat(addAmount));
  }

  return (
    <div className='userNav'>
        <>{props.username} </>
        <>-- {currentFunds} -- </>
        <input type="number" value={addAmount} onChange={(e) => setAddAmount(e.target.value)} />
        <button onClick={() => handleAddFunds()}>+</button>
    </div>
  );
};

export default UserNavBarMenu;
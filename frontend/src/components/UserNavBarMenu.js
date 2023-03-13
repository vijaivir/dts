import React, { useState } from 'react';
import { Button } from 'react-bootstrap';
import styles from "../styles.module.css"

const UserNavBarMenu = (props) => {

    const handleAddFunds = () => {
        console.log("add funds logic")
    }

  return (
    <div className='userNav'>
        <>{props.username}</>
        <>{props.amount}</>
        <button onClick={() => handleAddFunds()}>+</button>
    </div>
  );
};

export default UserNavBarMenu;
import navBar from "./components/NavBar";
import React, {useState} from "react";
import Login from "./components/Login";
import TradingPage from './TradingPage'

function HomePage() {

    const [username, setUsername] = useState('');
    const [isLoggedIn, setIsLoggedIn] = useState(false);

    return(
        <div>
            {navBar()}
            {isLoggedIn ? <><TradingPage username={username}></TradingPage></> : <Login setIsLoggedIn={setIsLoggedIn} setUsername={setUsername}></Login>}
        </div>
    );

}

export default HomePage;
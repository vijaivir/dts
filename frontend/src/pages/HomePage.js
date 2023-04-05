import navBar from "../components/NavBar";
import React, { useState, useEffect } from "react";
import Login from "./LoginPage";
import TradingPage from "./TradingPage";

function HomePage() {
  const [username, setUsername] = useState("");
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    console.log(username);
  }, [username]);
  return (
    <div>
      {isLoggedIn ? (
        <>
          <TradingPage
            username={username}
            isLoggedIn={isLoggedIn}
          ></TradingPage>
        </>
      ) : (
        <Login setIsLoggedIn={setIsLoggedIn} setUsername={setUsername}></Login>
      )}
    </div>
  );
}

export default HomePage;

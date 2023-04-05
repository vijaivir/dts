import "bootstrap/dist/css/bootstrap.min.css";
import { Form } from "react-bootstrap";
import { Container } from "react-bootstrap";
import { Button } from "react-bootstrap";
import React, { useState } from "react";
import NavBar from "../components/NavBar";
import axios from "axios";

function LoginPage(props) {
  const [username, setUsername] = useState("");

  const handleSubmit = async () => {
    // Perform login logic here
    console.log(username);
    props.setIsLoggedIn(true);
    props.setUsername(username);
    // const payload = {
    //   "username": username,
    //   ""
    // }
  };

  return (
    <div>
      <NavBar setIsLoggedIn={false}></NavBar>
      <div>
        <Container>
          <Form>
            <Form.Group className="mt-5" controlId="loginPage.username">
              <Form.Label className="mr-3">Username</Form.Label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
              <Button onClick={() => handleSubmit()}> Login </Button>
            </Form.Group>
          </Form>
        </Container>
      </div>
    </div>
  );
}

export default LoginPage;

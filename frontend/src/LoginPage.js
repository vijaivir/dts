import 'bootstrap/dist/css/bootstrap.min.css';
import { Form } from 'react-bootstrap';
import { Container } from 'react-bootstrap';
import { Button } from 'react-bootstrap';
import Navbar from 'react-bootstrap/Navbar';
import { useState } from 'react'
function LoginPage() {

  const [username, setUsername] = useState('') 

  const requestOptions = {
    method: "POST",
    headers: { 'Content-Type': 'application/json' },
    mode: 'no-cors',
    body: JSON.stringify({username: username})
  }

  function sendUser() {
    console.log(username)
    fetch("http://localhost:8080/books", requestOptions)
      .then(res => res.json())
      .then((data) => {
        console.log(data)
      })
  }


  return (
    <div>
      <div>
        <Navbar bg="primary" expand="lg">
          <Container>
            <Navbar.Brand href="#home" style={{color:"white"}}>Day Trading System</Navbar.Brand>
          </Container>
        </Navbar>
      </div>
      <div>
        <Container>
          <Form>
            <Form.Group className="mt-5" controlId="loginPage.username">
              <Form.Label className='mr-3'>Username</Form.Label>
              <Form.Control className='mb-2 mt-2' type="email" name='userinfobox' placeholder='username' onChange={e => setUsername(e.target.value)}/>
              <Button  onClick={() => sendUser()}> Login </Button>
            </Form.Group>
          </Form>
        </Container>
      </div>
    </div>
  );
}

export default LoginPage;
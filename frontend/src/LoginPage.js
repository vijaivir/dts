import 'bootstrap/dist/css/bootstrap.min.css';
import { Form } from 'react-bootstrap';
import { Container } from 'react-bootstrap';
import { Button } from 'react-bootstrap';
import Navbar from 'react-bootstrap/Navbar';

function LoginPage() {
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
              <Form.Control className='mb-2 mt-2' type="email"/>
              <Button> Login </Button>
            </Form.Group>
          </Form>
        </Container>
      </div>
    </div>
  );
}

export default LoginPage;
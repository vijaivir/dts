import Navbar from "react-bootstrap/Navbar";
import Container from "react-bootstrap/Container";

function NavBar() {
    return(
        <div>
            <div>
                <Navbar bg="primary" expand="lg">
                <Container>
                    <Navbar.Brand href="#home" style={{color:"white"}} fixed='right'>Day Trading System</Navbar.Brand>
                </Container>
                </Navbar>
            </div>
        </div>
    );

}

export default NavBar;
import Navbar from "react-bootstrap/Navbar";
import Container from "react-bootstrap/Container";
import UserNavBarMenu from "./UserNavBarMenu";

function NavBar(props) {

    const renderUserNav = () =>{
        return (
            <Navbar.Collapse className="justify-content-end" style={{color:"white"}}>
                <UserNavBarMenu username={props.username}></UserNavBarMenu>
            </Navbar.Collapse>
        )
    }

    return(
        <div>
            <div>
                <Navbar bg="primary" expand="lg">
                <Container>
                    <Navbar.Brand style={{color:"white"}} fixed='right'>Day Trading System</Navbar.Brand>
                </Container>
                <Container>
                {props.isLoggedIn ? renderUserNav() : <></>}
                </Container>
                </Navbar>
            </div>
        </div>
    );

}

export default NavBar;
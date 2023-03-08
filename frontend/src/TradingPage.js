import CollapsibleList from "./components/CollapsibleList";
import styles from "./styles.module.css"
import NavBar from "./components/NavBar";

function TradingPage(props) {

    const demoList = ['auya', 'asdasd', 'listyyy']

    return(
        <div>
            <NavBar username={props.username} isLoggedIn={props.isLoggedIn} amount={'1000$'}></NavBar>
            <div className={styles.container}>
                <div className={styles.panel}>
                    yayay
                </div>   
                <div className={styles.panel}>
                    yayay
                </div>   
            </div> 
        </div>
    );

}

export default TradingPage;
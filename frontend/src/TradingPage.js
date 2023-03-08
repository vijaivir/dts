import CollapsibleList from "./components/CollapsibleList";

function TradingPage(props) {

    const demoList = ['auya', 'asdasd', 'listyyy']

    return(
        <div>
            <div>
                {props.username}
                <CollapsibleList items={demoList}></CollapsibleList>
            </div>
        </div>
    );

}

export default TradingPage;
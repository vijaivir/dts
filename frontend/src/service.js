const apiUrl = "http://localhost:5001"

//this is just an idea, I imagine this will need to be different for when nginx is introduced
const addFundsService = (username, amount) => {
    const requestOptions = {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({'cmd':'ADD', 'username':username, 'amount':amount, 'trxNum':1})
    }

    return fetch(apiUrl + '/add', requestOptions).then(response => response.json())
        
}
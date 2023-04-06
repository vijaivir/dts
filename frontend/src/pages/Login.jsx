import * as React from 'react';
import {useState} from 'react'
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardActions from '@mui/material/CardActions';
import CardContent from '@mui/material/CardContent';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import axios from 'axios'
import trxNum from '../utils/trxNum'
import {Link} from "react-router-dom";
import NavigationBar from '../components/NavigationBar'

export default function Login(props) {

    const [username, setUsername] = useState('')

    const handleLogin = async() => {
        const payload = {
            username: username,
            cmd: "ADD",
            funds: 0,
            trxNum: trxNum()
        }

        const res = await axios.post("http://127.0.0.1/user_utils/add", payload)
    }


    return (
    <div>
        <NavigationBar></NavigationBar>
        <div style={{height: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center', backgroundColor: '#696764'}}>
        
        <Card sx={{ minWidth: 275 }}>
            <CardContent sx={{display:'flex', flexDirection: 'column', alignItems: 'center'}}>
                <div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', marginBottom: 50}}>
                    <h3>Login</h3>
                </div>
                <div style={{display:'flex', justifyContent: 'center'}}>
                    <TextField id="outlined-basic" label="Username" variant="outlined" value={username} onChange={(e) => setUsername(e.target.value)}/>
                </div>
            </CardContent>
            <CardActions sx={{display:'flex', flexDirection: 'column', alignItems: 'center'}}>
                <Link to="/home" username={username}>
                    <Button disabled={username.length <= 0 }variant="contained" onClick={props.setSubmittedUsername(username)}>Login</Button>
                </Link>
            </CardActions>
        </Card>
        </div>
    </div>
    );
  }
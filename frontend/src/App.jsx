import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import {useState, useEffect} from "react"
import Login from './pages/Login'
import Home from './pages/Home'

function App() {

    const [submittedUsername, setSubmittedUsername] = useState('')
    return (
      <Router>
        <Routes>
            <Route path="/" element={<Login setSubmittedUsername={setSubmittedUsername}/>} username={submittedUsername}/>
            <Route path="/home" element={<Home username={submittedUsername}/>}/>
        </Routes>
      </Router>
    );
  }
  
export default App;
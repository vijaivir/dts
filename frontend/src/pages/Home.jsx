import {useState, useEffect} from 'react'
import NavigationBar from '../components/NavigationBar'
export default function Home ({username}) {


    return (
        <div>
            <NavigationBar username={username}></NavigationBar>
        </div>
    )
}
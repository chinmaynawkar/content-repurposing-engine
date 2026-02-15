import { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [message, setMessage] = useState<string>('Loading...')

  useEffect(() => {
    axios
      .get('http://127.0.0.1:8000/api/health')
      .then((response) => {
        setMessage(`✅ ${response.data.message}`)
      })
      .catch((error) => {
        setMessage(`❌ Backend connection failed: ${error.message}`)
      })
  }, [])

  return (
    <div className="App">
      <h1>Content Repurposing Engine</h1>
      <p>{message}</p>
    </div>
  )
}

export default App

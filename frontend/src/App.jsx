import { BrowserRouter, Routes, Route } from 'react-router-dom'

import Dashboard from './pages/Dashboard'
import BorrowerPage from './pages/BorrowerPage'

import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />

        <Route path="/borrower/:id" element={<BorrowerPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
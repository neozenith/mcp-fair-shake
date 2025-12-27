import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { GraphView } from './components/GraphView'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-background">
        <Routes>
          <Route path="/" element={<GraphView />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App

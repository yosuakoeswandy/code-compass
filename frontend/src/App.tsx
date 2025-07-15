import './App.css'
import { BrowserRouter, Route, Routes } from 'react-router';
import Search from './pages/Search/Search';

function App() {

  return (
    <BrowserRouter>
      <div>
        <Routes>
          <Route path="/" element={<Search />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App

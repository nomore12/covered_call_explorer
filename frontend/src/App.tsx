import './App.css';
import AppRoutes from './routes/Routes';
import { BrowserRouter } from 'react-router-dom';
import { SWRProvider } from './lib/swr-config';

function App() {
  return (
    <SWRProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </SWRProvider>
  );
}

export default App;

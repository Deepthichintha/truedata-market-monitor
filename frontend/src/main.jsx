import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import ProviderSelection from './ProviderSelection.jsx'
import KiteTestPage from './KiteTestPage.jsx'

function Root() {
  const provider = new URLSearchParams(window.location.search).get('provider')

  if (provider === 'kite') {
    return <KiteTestPage />
  }

  if (provider === 'truedata') {
    return <App />
  }

  return <ProviderSelection />
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Root />
  </StrictMode>,
)

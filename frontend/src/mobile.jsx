import React from 'react'
import ReactDOM from 'react-dom/client'
import MobileApp from './MobileApp.jsx'
import './index.css'
import { registerSW } from 'virtual:pwa-register'

// Register PWA service worker strictly in mobile entry
if ('serviceWorker' in navigator) {
  registerSW({
    immediate: true,
    onNeedRefresh() {
      // Automatic update without disrupting active scan
      console.log('Tracora Mobile PWA update available')
    },
    onOfflineReady() {
      console.log('Tracora Mobile PWA shell cached and ready offline')
    },
  })
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <MobileApp />
  </React.StrictMode>,
)

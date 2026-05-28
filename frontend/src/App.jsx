import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { AppConfigProvider } from './context/AppConfigContext'
import { ThemeProvider } from './context/ThemeContext'
import { ToastProvider } from './context/ToastContext'
import SystemRecoveryGate from './components/SystemRecoveryGate'

export default function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <ToastProvider>
          <AppConfigProvider>
            <BrowserRouter>
              <SystemRecoveryGate />
            </BrowserRouter>
          </AppConfigProvider>
        </ToastProvider>
      </ThemeProvider>
    </AuthProvider>
  )
}

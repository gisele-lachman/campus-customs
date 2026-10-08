import { useEffect } from 'react'
import { Route, Routes, useLocation } from 'react-router-dom'
import NavBar from './components/NavBar'
import ChatWidget from './components/ChatWidget'
import { Monogram } from './components/Graphics'
import Home from './pages/Home'
import About from './pages/About'
import Products from './pages/Products'
import ProductDetail from './pages/ProductDetail'
import Login from './pages/Login'
import Signup from './pages/Signup'
import NotFound from './pages/NotFound'

export default function App() {
  const location = useLocation()

  // Start each new page at the top.
  useEffect(() => {
    window.scrollTo({ top: 0 })
  }, [location.pathname])

  return (
    <>
      <NavBar />
      {/* Keyed on the path so each page fades in: a gentle page transition. */}
      <main className="page page-enter" key={location.pathname}>
        <Routes location={location}>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/:productId" element={<ProductDetail />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <footer className="footer">
        <div className="footer-stripes" />
        <div className="footer-inner">
          <div className="brand">
            <Monogram size={38} />
            <span className="brand-name">Campus Customs</span>
          </div>
          <p>
            <span className="accent">For Bulldogs, by Bulldogs.</span> A fictional Yale merch shop built for a class
            project.
          </p>
        </div>
      </footer>
      {/* Rendered outside <Routes> so the chat button appears on every page. */}
      <ChatWidget />
    </>
  )
}

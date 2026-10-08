import { Link } from 'react-router-dom'
import { EmptyPennant } from '../components/Graphics'

export default function NotFound() {
  return (
    <div className="no-results">
      <EmptyPennant />
      <h1>Out of bounds!</h1>
      <p className="muted">That page isn’t on our field.</p>
      <Link to="/" className="button">Back to the home page</Link>
    </div>
  )
}

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Cpu, Loader2 } from 'lucide-react';
import axios from 'axios';

export default function Signup() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await axios.post('/api/auth/signup', { name, email, password });
      login(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative bg-base">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-indigo-900/20 via-base to-base z-0" />
      
      <div className="w-full max-w-md relative z-10">
        <div className="bg-surface/80 backdrop-blur-xl p-8 rounded-2xl border border-subtle shadow-2xl">
          <div className="flex flex-col items-center mb-8">
            <div className="w-12 h-12 rounded-xl bg-primary flex items-center justify-center mb-4 shadow-lg shadow-primary/30">
              <Cpu size={24} className="text-white" />
            </div>
            <h2 className="text-2xl font-bold">Create Account</h2>
            <p className="text-txt-sec text-sm mt-1">Get started with CRAG Pipeline</p>
          </div>

          {error && <div className="bg-error/10 border border-error/20 text-error text-sm p-3 rounded-lg mb-4">{error}</div>}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-txt-sec mb-1">Name</label>
              <input type="text" required
                className="w-full bg-card border border-subtle rounded-xl px-4 py-2.5 text-sm outline-none focus:border-primary transition-colors"
                value={name} onChange={e => setName(e.target.value)} />
            </div>
            <div>
              <label className="block text-xs font-medium text-txt-sec mb-1">Email</label>
              <input type="email" required
                className="w-full bg-card border border-subtle rounded-xl px-4 py-2.5 text-sm outline-none focus:border-primary transition-colors"
                value={email} onChange={e => setEmail(e.target.value)} />
            </div>
            <div>
              <label className="block text-xs font-medium text-txt-sec mb-1">Password</label>
              <input type="password" required
                className="w-full bg-card border border-subtle rounded-xl px-4 py-2.5 text-sm outline-none focus:border-primary transition-colors"
                value={password} onChange={e => setPassword(e.target.value)} />
            </div>
            <button disabled={loading} type="submit" 
              className="w-full bg-primary hover:bg-primary-hover text-white font-medium py-2.5 rounded-xl transition-all shadow-lg shadow-primary/20 flex items-center justify-center">
              {loading ? <Loader2 size={18} className="animate-spin" /> : 'Sign up'}
            </button>
          </form>

          <p className="text-center text-xs text-txt-muted mt-6">
            Already have an account? <Link to="/signin" className="text-primary hover:text-primary-hover font-medium">Log in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

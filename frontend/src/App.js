import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate, Link, useNavigate } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('session_token');
    const userData = localStorage.getItem('user_data');
    
    if (token && userData) {
      setUser(JSON.parse(userData));
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
    setLoading(false);
  }, []);

  const login = (userData, token) => {
    setUser(userData);
    localStorage.setItem('session_token', token);
    localStorage.setItem('user_data', JSON.stringify(userData));
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('session_token');
    localStorage.removeItem('user_data');
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Components
const Header = () => {
  const { user, logout } = useAuth();
  
  return (
    <header className="header">
      <div className="container">
        <Link to="/" className="logo">
          <h2>LendStronger</h2>
        </Link>
        <nav className="nav">
          {!user ? (
            <>
              <Link to="/" className="nav-link">Home</Link>
              <Link to="/about" className="nav-link">About</Link>
              <Link to="/services" className="nav-link">Services</Link>
              <Link to="/login" className="nav-link login-btn">Login</Link>
            </>
          ) : (
            <>
              <Link to="/dashboard" className="nav-link">Dashboard</Link>
              <span className="user-info">Welcome, {user.name}</span>
              <button onClick={logout} className="logout-btn">Logout</button>
            </>
          )}
        </nav>
      </div>
    </header>
  );
};

const Home = () => {
  return (
    <div className="home">
      <section className="hero">
        <div className="hero-content">
          <h1>Connect Brokers & Lenders Seamlessly</h1>
          <p>The premier platform for mortgage brokers and lenders to collaborate, streamline deals, and grow their business together.</p>
          <div className="cta-buttons">
            <Link to="/login" className="cta-btn primary">Get Started</Link>
            <Link to="/about" className="cta-btn secondary">Learn More</Link>
          </div>
        </div>
        <div className="hero-image">
          <img src="https://images.unsplash.com/photo-1521790797524-b2497295b8a0?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzh8MHwxfHNlYXJjaHwxfHxmaW5hbmNpYWwlMjBjb2xsYWJvcmF0aW9ufGVufDB8fHx8MTc1MzU5MzEyOXww&ixlib=rb-4.1.0&q=85" alt="Professional Collaboration" />
        </div>
      </section>

      <section className="features">
        <div className="container">
          <h2>Why Choose LendStronger?</h2>
          <div className="features-grid">
            <div className="feature-card">
              <h3>For Brokers</h3>
              <ul>
                <li>Upload deals easily</li>
                <li>Get matched with qualified lenders</li>
                <li>Secure document sharing</li>
                <li>Track deal progress</li>
              </ul>
            </div>
            <div className="feature-card">
              <h3>For Lenders</h3>
              <ul>
                <li>Set your lending criteria</li>
                <li>Get notified of matching deals</li>
                <li>Secure communication</li>
                <li>Efficient deal management</li>
              </ul>
            </div>
            <div className="feature-card">
              <h3>Secure & Encrypted</h3>
              <ul>
                <li>End-to-end encryption</li>
                <li>Role-based access control</li>
                <li>Secure document storage</li>
                <li>Privacy protection</li>
              </ul>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

const About = () => {
  return (
    <div className="page-content">
      <div className="container">
        <h1>About LendStronger</h1>
        <div className="about-content">
          <div className="about-text">
            <p>LendStronger is the premier platform connecting mortgage brokers and lenders in a secure, efficient environment. We understand the challenges of the lending industry and have built a solution that streamlines the entire process.</p>
            
            <h3>Our Mission</h3>
            <p>To revolutionize how brokers and lenders collaborate by providing a secure, efficient platform that reduces time-to-close and increases successful loan completions.</p>
            
            <h3>Key Benefits</h3>
            <ul>
              <li>Automated matching based on lender criteria</li>
              <li>Secure, encrypted document sharing</li>
              <li>Real-time communication tools</li>
              <li>Comprehensive deal tracking</li>
              <li>Professional compliance standards</li>
            </ul>
          </div>
          <div className="about-image">
            <img src="https://images.unsplash.com/39/lIZrwvbeRuuzqOoWJUEn_Photoaday_CSD%20%281%20of%201%29-5.jpg?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDN8MHwxfHNlYXJjaHwxfHxidXNpbmVzcyUyMHBhcnRuZXJzaGlwfGVufDB8fHx8MTc1MzU5MzEzOHww&ixlib=rb-4.1.0&q=85" alt="Professional Office" />
          </div>
        </div>
      </div>
    </div>
  );
};

const Services = () => {
  return (
    <div className="page-content">
      <div className="container">
        <h1>Our Services</h1>
        <div className="services-grid">
          <div className="service-card">
            <img src="https://images.unsplash.com/photo-1559067096-d109b66fd5af?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2Mzl8MHwxfHNlYXJjaHwxfHxtb3J0Z2FnZSUyMGxlbmRpbmd8ZW58MHx8fHwxNzUzNTkzMTM0fDA&ixlib=rb-4.1.0&q=85" alt="Mortgage Services" />
            <h3>Deal Matching</h3>
            <p>Our intelligent matching system connects brokers with the right lenders based on specific criteria and deal parameters.</p>
          </div>
          <div className="service-card">
            <img src="https://images.pexels.com/photos/4161619/pexels-photo-4161619.jpeg" alt="Consultation" />
            <h3>Secure Communication</h3>
            <p>Built-in messaging system with role-based access ensures secure communication throughout the deal process.</p>
          </div>
          <div className="service-card">
            <img src="https://images.unsplash.com/photo-1521790797524-b2497295b8a0?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzh8MHwxfHNlYXJjaHwxfHxmaW5hbmNpYWwlMjBjb2xsYWJvcmF0aW9ufGVufDB8fHx8MTc1MzU5MzEyOXww&ixlib=rb-4.1.0&q=85" alt="Document Management" />
            <h3>Document Management</h3>
            <p>Encrypted document storage and sharing with comprehensive access controls for sensitive financial information.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

const Login = () => {
  const [userType, setUserType] = useState('broker');
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const payload = {
        ...formData,
        user_type: userType
      };

      const response = await axios.post(`${API}${endpoint}`, payload);
      
      if (isLogin) {
        login(response.data.user, response.data.session_token);
        navigate('/dashboard');
      } else {
        alert('Registration successful! Please login.');
        setIsLogin(true);
        setFormData({ email: '', password: '', name: '' });
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-form">
          <h2>{isLogin ? 'Login' : 'Register'} as {userType === 'broker' ? 'Broker' : 'Lender'}</h2>
          
          <div className="user-type-selector">
            <button 
              type="button"
              className={userType === 'broker' ? 'active' : ''}
              onClick={() => setUserType('broker')}
            >
              Broker
            </button>
            <button 
              type="button"
              className={userType === 'lender' ? 'active' : ''}
              onClick={() => setUserType('lender')}
            >
              Lender
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            {!isLogin && (
              <input
                type="text"
                placeholder="Full Name"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                required
              />
            )}
            <input
              type="email"
              placeholder="Email"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              required
            />
            <input
              type="password"
              placeholder="Password"
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              required
            />
            
            {error && <div className="error-message">{error}</div>}
            
            <button type="submit" disabled={loading}>
              {loading ? 'Processing...' : (isLogin ? 'Login' : 'Register')}
            </button>
          </form>

          <p>
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <button 
              type="button" 
              className="link-btn"
              onClick={() => setIsLogin(!isLogin)}
            >
              {isLogin ? 'Register' : 'Login'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const { user } = useAuth();
  
  if (!user) {
    return <Navigate to="/login" />;
  }

  return user.user_type === 'broker' ? <BrokerDashboard /> : <LenderDashboard />;
};

const BrokerDashboard = () => {
  const [deals, setDeals] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newDeal, setNewDeal] = useState({
    title: '',
    loan_type: 'residential',
    amount: '',
    region: '',
    borrower_credit_score: '',
    ltv_ratio: '',
    property_type: '',
    description: ''
  });

  useEffect(() => {
    fetchDeals();
  }, []);

  const fetchDeals = async () => {
    try {
      const response = await axios.get(`${API}/broker/deals`);
      setDeals(response.data);
    } catch (error) {
      console.error('Error fetching deals:', error);
    }
  };

  const handleCreateDeal = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/broker/deals`, {
        ...newDeal,
        amount: parseFloat(newDeal.amount),
        borrower_credit_score: parseInt(newDeal.borrower_credit_score),
        ltv_ratio: parseFloat(newDeal.ltv_ratio)
      });
      setShowCreateForm(false);
      setNewDeal({
        title: '',
        loan_type: 'residential',
        amount: '',
        region: '',
        borrower_credit_score: '',
        ltv_ratio: '',
        property_type: '',
        description: ''
      });
      fetchDeals();
      alert('Deal created successfully!');
    } catch (error) {
      alert('Error creating deal');
      console.error(error);
    }
  };

  return (
    <div className="dashboard">
      <div className="container">
        <div className="dashboard-header">
          <h1>Broker Dashboard</h1>
          <button 
            className="create-btn"
            onClick={() => setShowCreateForm(true)}
          >
            Create New Deal
          </button>
        </div>

        {showCreateForm && (
          <div className="modal-overlay">
            <div className="modal">
              <h3>Create New Deal</h3>
              <form onSubmit={handleCreateDeal}>
                <input
                  type="text"
                  placeholder="Deal Title"
                  value={newDeal.title}
                  onChange={(e) => setNewDeal({...newDeal, title: e.target.value})}
                  required
                />
                <select
                  value={newDeal.loan_type}
                  onChange={(e) => setNewDeal({...newDeal, loan_type: e.target.value})}
                >
                  <option value="residential">Residential</option>
                  <option value="commercial">Commercial</option>
                  <option value="construction">Construction</option>
                  <option value="refinance">Refinance</option>
                </select>
                <input
                  type="number"
                  placeholder="Loan Amount"
                  value={newDeal.amount}
                  onChange={(e) => setNewDeal({...newDeal, amount: e.target.value})}
                  required
                />
                <input
                  type="text"
                  placeholder="Region/State"
                  value={newDeal.region}
                  onChange={(e) => setNewDeal({...newDeal, region: e.target.value})}
                  required
                />
                <input
                  type="number"
                  placeholder="Borrower Credit Score"
                  value={newDeal.borrower_credit_score}
                  onChange={(e) => setNewDeal({...newDeal, borrower_credit_score: e.target.value})}
                  required
                />
                <input
                  type="number"
                  step="0.01"
                  placeholder="LTV Ratio (e.g., 0.8 for 80%)"
                  value={newDeal.ltv_ratio}
                  onChange={(e) => setNewDeal({...newDeal, ltv_ratio: e.target.value})}
                  required
                />
                <input
                  type="text"
                  placeholder="Property Type"
                  value={newDeal.property_type}
                  onChange={(e) => setNewDeal({...newDeal, property_type: e.target.value})}
                  required
                />
                <textarea
                  placeholder="Deal Description"
                  value={newDeal.description}
                  onChange={(e) => setNewDeal({...newDeal, description: e.target.value})}
                  required
                />
                <div className="modal-buttons">
                  <button type="submit">Create Deal</button>
                  <button type="button" onClick={() => setShowCreateForm(false)}>Cancel</button>
                </div>
              </form>
            </div>
          </div>
        )}

        <div className="deals-grid">
          {deals.map((deal) => (
            <div key={deal.id} className="deal-card">
              <h3>{deal.title}</h3>
              <div className="deal-details">
                <p><strong>Type:</strong> {deal.loan_type}</p>
                <p><strong>Amount:</strong> ${deal.amount.toLocaleString()}</p>
                <p><strong>Region:</strong> {deal.region}</p>
                <p><strong>Status:</strong> <span className={`status ${deal.status}`}>{deal.status}</span></p>
                <p><strong>Credit Score:</strong> {deal.borrower_credit_score}</p>
                <p><strong>LTV:</strong> {(deal.ltv_ratio * 100).toFixed(1)}%</p>
              </div>
              <p className="deal-description">{deal.description}</p>
              <div className="deal-actions">
                <Link to={`/deal/${deal.id}`} className="view-btn">View Details</Link>
              </div>
            </div>
          ))}
        </div>

        {deals.length === 0 && (
          <div className="empty-state">
            <h3>No deals yet</h3>
            <p>Create your first deal to get started!</p>
          </div>
        )}
      </div>
    </div>
  );
};

const LenderDashboard = () => {
  const [criteria, setCriteria] = useState(null);
  const [deals, setDeals] = useState([]);
  const [showCriteriaForm, setShowCriteriaForm] = useState(false);
  const [newCriteria, setNewCriteria] = useState({
    loan_types: [],
    min_amount: '',
    max_amount: '',
    regions: [],
    credit_score_min: '',
    ltv_max: ''
  });

  useEffect(() => {
    fetchCriteria();
    fetchAvailableDeals();
  }, []);

  const fetchCriteria = async () => {
    try {
      const response = await axios.get(`${API}/lender/criteria`);
      setCriteria(response.data);
    } catch (error) {
      console.error('Error fetching criteria:', error);
    }
  };

  const fetchAvailableDeals = async () => {
    try {
      const response = await axios.get(`${API}/lender/deals`);
      setDeals(response.data);
    } catch (error) {
      console.error('Error fetching deals:', error);
    }
  };

  const handleCriteriaSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/lender/criteria`, {
        ...newCriteria,
        min_amount: parseFloat(newCriteria.min_amount),
        max_amount: parseFloat(newCriteria.max_amount),
        credit_score_min: parseInt(newCriteria.credit_score_min),
        ltv_max: parseFloat(newCriteria.ltv_max)
      });
      setShowCriteriaForm(false);
      fetchCriteria();
      fetchAvailableDeals();
      alert('Criteria saved successfully!');
    } catch (error) {
      alert('Error saving criteria');
      console.error(error);
    }
  };

  const handleExpressInterest = async (dealId) => {
    try {
      await axios.post(`${API}/lender/interest`, {
        deal_id: dealId,
        interest_type: 'full',
        message: 'I am interested in funding this deal.'
      });
      alert('Interest expressed successfully!');
      fetchAvailableDeals();
    } catch (error) {
      alert('Error expressing interest');
      console.error(error);
    }
  };

  return (
    <div className="dashboard">
      <div className="container">
        <div className="dashboard-header">
          <h1>Lender Dashboard</h1>
          <button 
            className="create-btn"
            onClick={() => setShowCriteriaForm(true)}
          >
            {criteria ? 'Update Criteria' : 'Set Lending Criteria'}
          </button>
        </div>

        {criteria && (
          <div className="criteria-summary">
            <h3>Your Lending Criteria</h3>
            <div className="criteria-details">
              <p><strong>Loan Types:</strong> {criteria.loan_types.join(', ')}</p>
              <p><strong>Amount Range:</strong> ${criteria.min_amount.toLocaleString()} - ${criteria.max_amount.toLocaleString()}</p>
              <p><strong>Regions:</strong> {criteria.regions.join(', ')}</p>
              <p><strong>Min Credit Score:</strong> {criteria.credit_score_min}</p>
              <p><strong>Max LTV:</strong> {(criteria.ltv_max * 100).toFixed(1)}%</p>
            </div>
          </div>
        )}

        {showCriteriaForm && (
          <div className="modal-overlay">
            <div className="modal">
              <h3>Set Lending Criteria</h3>
              <form onSubmit={handleCriteriaSubmit}>
                <div className="checkbox-group">
                  <label>Loan Types:</label>
                  {['residential', 'commercial', 'construction', 'refinance'].map(type => (
                    <label key={type} className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={newCriteria.loan_types.includes(type)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setNewCriteria({
                              ...newCriteria,
                              loan_types: [...newCriteria.loan_types, type]
                            });
                          } else {
                            setNewCriteria({
                              ...newCriteria,
                              loan_types: newCriteria.loan_types.filter(t => t !== type)
                            });
                          }
                        }}
                      />
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </label>
                  ))}
                </div>
                <input
                  type="number"
                  placeholder="Minimum Amount"
                  value={newCriteria.min_amount}
                  onChange={(e) => setNewCriteria({...newCriteria, min_amount: e.target.value})}
                  required
                />
                <input
                  type="number"
                  placeholder="Maximum Amount"
                  value={newCriteria.max_amount}
                  onChange={(e) => setNewCriteria({...newCriteria, max_amount: e.target.value})}
                  required
                />
                <input
                  type="text"
                  placeholder="Regions (comma-separated)"
                  value={newCriteria.regions.join(', ')}
                  onChange={(e) => setNewCriteria({
                    ...newCriteria, 
                    regions: e.target.value.split(',').map(r => r.trim())
                  })}
                  required
                />
                <input
                  type="number"
                  placeholder="Minimum Credit Score"
                  value={newCriteria.credit_score_min}
                  onChange={(e) => setNewCriteria({...newCriteria, credit_score_min: e.target.value})}
                  required
                />
                <input
                  type="number"
                  step="0.01"
                  placeholder="Maximum LTV Ratio (e.g., 0.8 for 80%)"
                  value={newCriteria.ltv_max}
                  onChange={(e) => setNewCriteria({...newCriteria, ltv_max: e.target.value})}
                  required
                />
                <div className="modal-buttons">
                  <button type="submit">Save Criteria</button>
                  <button type="button" onClick={() => setShowCriteriaForm(false)}>Cancel</button>
                </div>
              </form>
            </div>
          </div>
        )}

        <div className="section">
          <h3>Available Deals Matching Your Criteria</h3>
          <div className="deals-grid">
            {deals.map((deal) => (
              <div key={deal.id} className="deal-card">
                <h4>{deal.title}</h4>
                <div className="deal-details">
                  <p><strong>Broker:</strong> {deal.broker_name}</p>
                  <p><strong>Type:</strong> {deal.loan_type}</p>
                  <p><strong>Amount:</strong> ${deal.amount.toLocaleString()}</p>
                  <p><strong>Region:</strong> {deal.region}</p>
                  <p><strong>Credit Score:</strong> {deal.borrower_credit_score}</p>
                  <p><strong>LTV:</strong> {(deal.ltv_ratio * 100).toFixed(1)}%</p>
                </div>
                <p className="deal-description">{deal.description}</p>
                <div className="deal-actions">
                  <button 
                    className="interest-btn"
                    onClick={() => handleExpressInterest(deal.id)}
                  >
                    Express Interest
                  </button>
                  <Link to={`/deal/${deal.id}`} className="view-btn">View Details</Link>
                </div>
              </div>
            ))}
          </div>

          {deals.length === 0 && (
            <div className="empty-state">
              <h4>No matching deals available</h4>
              <p>{criteria ? 'No deals currently match your criteria.' : 'Set your lending criteria to see matching deals.'}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div className="loading">Loading...</div>;
  }
  
  return user ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <BrowserRouter>
          <Header />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/about" element={<About />} />
              <Route path="/services" element={<Services />} />
              <Route path="/login" element={<Login />} />
              <Route path="/dashboard" element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              } />
            </Routes>
          </main>
        </BrowserRouter>
      </AuthProvider>
    </div>
  );
}

export default App;
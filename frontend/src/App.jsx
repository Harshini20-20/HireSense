
import { useState } from 'react'
import './App.css'

const navigation = [
  { id: 'dashboard', label: 'Dashboard', icon: '◫' },
  { id: 'jobs', label: 'Job Management', icon: '▤' },
  { id: 'resumes', label: 'Resume Upload', icon: '⇧' },
  { id: 'candidates', label: 'Candidates', icon: '♙' },
]

function App() {
  const [activePage, setActivePage] = useState('dashboard')
  const [jobTitle, setJobTitle] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [jobId, setJobId] = useState('')
  const [files, setFiles] = useState([])
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  async function apiRequest(url, options = {}) {
    const response = await fetch(url, options)
    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || 'Something went wrong')
    }

    return data
  }

  async function createJob(event) {
    event.preventDefault()
    setLoading(true)
    setMessage('')
    setError('')

    try {
      const data = await apiRequest('/api/jobs/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: jobTitle,
          description: jobDescription,
        }),
      })

      setJobId(String(data.id))
      setMessage(`Job created successfully. Job ID: ${data.id}`)
      setJobTitle('')
      setJobDescription('')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function uploadResumes(event) {
    event.preventDefault()

    if (!files.length) {
      setError('Please select at least one resume.')
      return
    }

    setLoading(true)
    setMessage('')
    setError('')

    try {
      const formData = new FormData()
      files.forEach(file => formData.append('files', file))

      const data = await apiRequest('/api/resumes/upload', {
        method: 'POST',
        body: formData,
      })

      setMessage(
        `Upload complete: ${data.successful} successful, ${data.failed} failed.`
      )
      setFiles([])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function evaluateCandidates(event) {
    event.preventDefault()

    if (!jobId.trim() || !Number.isInteger(Number(jobId))) {
      setError('Enter a valid job ID.')
      return
    }

    setLoading(true)
    setMessage('')
    setError('')
    setResults(null)

    try {
      const data = await apiRequest(
        `/api/matching/${Number(jobId)}/evaluate`,
        { method: 'POST' }
      )

      setResults(data)
      setActivePage('candidates')
      setMessage(`Evaluation completed for ${data.job_title}.`)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function navigate(page) {
    setActivePage(page)
    setMessage('')
    setError('')
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">H</div>
          <div>
            <h2>HireSense</h2>
            <span>RECRUITMENT INTELLIGENCE</span>
          </div>
        </div>

        <div className="sidebar-label">WORKSPACE</div>

        <nav className="navigation">
          {navigation.map(item => (
            <button
              key={item.id}
              className={`nav-item ${activePage === item.id ? 'active' : ''}`}
              onClick={() => navigate(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="profile-avatar">HS</div>
          <div className="profile-info">
            <strong>Recruitment Team</strong>
            <span>Administrator</span>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <span className="breadcrumb">Workspace / </span>
            <strong>
              {navigation.find(item => item.id === activePage)?.label}
            </strong>
          </div>
          <div className="connection-status">
            <span className="status-dot"></span>
            Backend connected
          </div>
        </header>

        <section className="page-content">
          <div className="page-heading">
            <div>
              <span className="eyebrow">HIRESENSE WORKSPACE</span>
              <h1>
                {activePage === 'dashboard' && 'Dashboard'}
                {activePage === 'jobs' && 'Job Management'}
                {activePage === 'resumes' && 'Resume Upload'}
                {activePage === 'candidates' && 'Candidate Rankings'}
              </h1>
              <p>
                {activePage === 'dashboard' &&
                  'Manage your recruitment workflow in one place.'}
                {activePage === 'jobs' &&
                  'Create and manage job descriptions.'}
                {activePage === 'resumes' &&
                  'Upload candidate resumes for AI-powered evaluation.'}
                {activePage === 'candidates' &&
                  'Review candidate matches and evaluation results.'}
              </p>
            </div>
          </div>

          {message && <div className="alert success">{message}</div>}
          {error && <div className="alert error">{error}</div>}

          {activePage === 'dashboard' && (
            <>
              <div className="welcome-card">
                <div>
                  <span className="eyebrow">AI-POWERED RECRUITMENT</span>
                  <h2>Find the right candidate, faster.</h2>
                  <p>
                    Create a job, upload resumes and let HireSense
                    evaluate candidates using intelligent matching.
                  </p>
                  <button
                    className="primary-button"
                    onClick={() => navigate('jobs')}
                  >
                    Create a job <span>→</span>
                  </button>
                </div>
                <div className="welcome-decoration">H</div>
              </div>

              <h3 className="section-heading">Recruitment workflow</h3>

              <div className="workflow-grid">
                <button
                  className="workflow-card"
                  onClick={() => navigate('jobs')}
                >
                  <span className="workflow-icon purple">▤</span>
                  <h3>Create a job</h3>
                  <p>Add a job title and description.</p>
                  <span className="card-link">Get started →</span>
                </button>

                <button
                  className="workflow-card"
                  onClick={() => navigate('resumes')}
                >
                  <span className="workflow-icon blue">⇧</span>
                  <h3>Upload resumes</h3>
                  <p>Upload PDF or DOCX candidate resumes.</p>
                  <span className="card-link">Upload files →</span>
                </button>

                <button
                  className="workflow-card"
                  onClick={() => navigate('candidates')}
                >
                  <span className="workflow-icon green">♙</span>
                  <h3>Evaluate candidates</h3>
                  <p>Rank candidates against a job description.</p>
                  <span className="card-link">View rankings →</span>
                </button>
              </div>

              <div className="info-panel">
                <div>
                  <h3>How HireSense evaluates candidates</h3>
                  <p>
                    Five matching components contribute to the overall score.
                    The backend handles scoring and weight redistribution.
                  </p>
                </div>
                <div className="weight-list">
                  {[
                    ['Skills', '35%'],
                    ['Semantic relevance', '30%'],
                    ['Experience', '20%'],
                    ['Education', '10%'],
                    ['Projects', '5%'],
                  ].map(([label, value]) => (
                    <div className="weight-item" key={label}>
                      <span>{label}</span>
                      <strong>{value}</strong>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {activePage === 'jobs' && (
            <div className="form-card">
              <h2>Create a new job</h2>
              <p className="form-description">
                Enter the job details to create a new recruitment requirement.
              </p>

              <form onSubmit={createJob}>
                <label htmlFor="job-title">Job title</label>
                <input
                  id="job-title"
                  value={jobTitle}
                  onChange={event => setJobTitle(event.target.value)}
                  placeholder="e.g. AI Engineer"
                  required
                />

                <label htmlFor="job-description">Job description</label>
                <textarea
                  id="job-description"
                  value={jobDescription}
                  onChange={event => setJobDescription(event.target.value)}
                  placeholder="Enter responsibilities, required skills, experience and qualifications..."
                  rows={9}
                  required
                />

                <button className="primary-button" disabled={loading}>
                  {loading ? 'Creating...' : 'Create job'}
                </button>
              </form>

              {jobId && (
                <div className="created-job">
                  <strong>Latest created job ID:</strong> {jobId}
                </div>
              )}
            </div>
          )}

          {activePage === 'resumes' && (
            <div className="form-card">
              <h2>Upload candidate resumes</h2>
              <p className="form-description">
                Select one or more PDF or DOCX files. Each file will be
                processed by the existing resume ingestion service.
              </p>

              <form onSubmit={uploadResumes}>
                <label className="upload-area">
                  <span className="upload-icon">⇧</span>
                  <strong>Choose resume files</strong>
                  <span>PDF and DOCX formats supported</span>
                  <input
                    type="file"
                    accept=".pdf,.docx"
                    multiple
                    onChange={event =>
                      setFiles(Array.from(event.target.files || []))
                    }
                  />
                </label>

                {files.length > 0 && (
                  <div className="selected-files">
                    {files.map(file => (
                      <div key={`${file.name}-${file.size}`}>
                        <span>▤ {file.name}</span>
                        <span>{(file.size / 1024).toFixed(1)} KB</span>
                      </div>
                    ))}
                  </div>
                )}

                <button className="primary-button" disabled={loading}>
                  {loading ? 'Uploading...' : 'Upload resumes'}
                </button>
              </form>
            </div>
          )}

          {activePage === 'candidates' && (
            <>
              <div className="form-card evaluation-form">
                <h2>Evaluate candidates</h2>
                <p className="form-description">
                  Enter the ID of an existing job to evaluate uploaded resumes.
                </p>

                <form onSubmit={evaluateCandidates}>
                  <label htmlFor="evaluation-job-id">Job ID</label>
                  <input
                    id="evaluation-job-id"
                    type="number"
                    min="1"
                    value={jobId}
                    onChange={event => setJobId(event.target.value)}
                    placeholder="Enter job ID"
                    required
                  />
                  <button className="primary-button" disabled={loading}>
                    {loading ? 'Evaluating...' : 'Run candidate evaluation'}
                  </button>
                </form>
              </div>

              {results && (
                <div className="results-section">
                  <div className="results-heading">
                    <div>
                      <span className="eyebrow">EVALUATION RESULTS</span>
                      <h2>{results.job_title}</h2>
                      <p>{results.total_candidates} candidates evaluated</p>
                    </div>
                  </div>

                  {results.candidates.length === 0 ? (
                    <div className="empty-state">
                      No candidates with processed resumes were found for
                      this evaluation.
                    </div>
                  ) : (
                    <div className="candidate-list">
                      {results.candidates.map((candidate, index) => (
                        <div
                          className="candidate-card"
                          key={candidate.candidate_id}
                        >
                          <div className="candidate-rank">#{index + 1}</div>
                          <div className="candidate-details">
                            <h3>{candidate.candidate_name}</h3>
                            <p>{candidate.email || 'No email available'}</p>
                            <span>{candidate.resume_name}</span>
                          </div>
                          <div className="candidate-score">
                            <strong>
                              {Number(candidate.overall_score).toFixed(1)}%
                            </strong>
                            <span>Overall match</span>
                          </div>
                          <div className="candidate-breakdown">
                            {Object.entries(candidate.component_scores || {})
                              .map(([name, score]) => (
                                <span key={name}>
                                  {name}: {score == null
                                    ? 'N/A'
                                    : `${Number(score).toFixed(0)}%`}
                                </span>
                              ))}
                          </div>
                          <div className="candidate-explanation">
                            {candidate.explanation?.summary ||
                              'Evaluation completed.'}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </section>
      </main>
    </div>
  )
}

export default App

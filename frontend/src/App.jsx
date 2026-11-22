
import { useEffect, useState } from 'react'
import './App.css'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')

const navigation = [
  { id: 'dashboard', label: 'Dashboard', icon: '◫' },
  { id: 'jobs', label: 'Job Management', icon: '▤' },
  { id: 'resumes', label: 'Resume Upload', icon: '⇧' },
  { id: 'candidates', label: 'Candidate Rankings', icon: '♙' },
  { id: 'manage-candidates', label: 'Manage Candidates', icon: '⌕' },
]

function App() {
  const [activePage, setActivePage] = useState('dashboard')
  const [jobTitle, setJobTitle] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [jobId, setJobId] = useState('')
  const [jobs, setJobs] = useState([])
  const [candidateProfiles, setCandidateProfiles] = useState([])
  const [files, setFiles] = useState([])
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [candidateSearch, setCandidateSearch] = useState('')
  const [candidateProfileSearch, setCandidateProfileSearch] = useState('')
  const [minimumScore, setMinimumScore] = useState('0')
  const [sortOrder, setSortOrder] = useState('highest')
  const [expandedCandidate, setExpandedCandidate] = useState(null)

  useEffect(() => {
    fetch(`${API_BASE_URL}/jobs/`).then(response => response.ok ? response.json() : [])
      .then(data => setJobs(Array.isArray(data) ? data : []))
      .catch(() => setJobs([]))
    fetch(`${API_BASE_URL}/candidates/`).then(response => response.ok ? response.json() : [])
      .then(data => setCandidateProfiles(Array.isArray(data) ? data : []))
      .catch(() => setCandidateProfiles([]))
  }, [])

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
      const data = await apiRequest(`${API_BASE_URL}/jobs/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: jobTitle,
          description: jobDescription,
        }),
      })

      setJobId(String(data.id))
      setJobs(previous => [data, ...previous.filter(job => job.id !== data.id)])
      setMessage(`Job created successfully. Job ID: ${data.id}`)
      setJobTitle('')
      setJobDescription('')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function refreshJobs() {
    const data = await apiRequest(`${API_BASE_URL}/jobs/`)
    setJobs(Array.isArray(data) ? data : [])
  }

  async function refreshCandidates() {
    const data = await apiRequest(`${API_BASE_URL}/candidates/`)
    setCandidateProfiles(Array.isArray(data) ? data : [])
  }

  async function deleteJob(job) {
    if (!window.confirm(`Delete job "${job.title}" (ID ${job.id})? Its requirements and analyses will be deleted. Candidate profiles and resumes will be preserved.`)) return
    setMessage('')
    setError('')
    try {
      await apiRequest(`${API_BASE_URL}/jobs/${job.id}`, { method: 'DELETE' })
      await refreshJobs()
      if (String(job.id) === String(jobId)) setJobId('')
      if (results?.job_id === job.id) setResults(null)
      setMessage(`Job "${job.title}" deleted. Candidate profiles and resumes were preserved.`)
    } catch (err) {
      setError(err.message)
    }
  }

  async function deleteResume(candidate, resume) {
    if (!window.confirm(`Remove resume "${resume.file_name}" from ${candidate.name || 'this candidate'}? Its dependent analysis records will also be removed.`)) return
    setMessage('')
    setError('')
    try {
      await apiRequest(`${API_BASE_URL}/candidates/${candidate.id}/resumes/${resume.id}`, { method: 'DELETE' })
      await refreshCandidates()
      if (results?.candidates?.some(item => item.candidate_id === candidate.id)) setResults(null)
      setMessage(`Resume "${resume.file_name}" removed successfully.`)
    } catch (err) {
      setError(err.message)
    }
  }

  async function deleteCandidate(candidate) {
    const name = candidate.name || `Candidate ${candidate.id}`
    if (!window.confirm(`Delete ${name} and all of their resumes, skills, job associations, and analysis records? Job records will be preserved.`)) return
    setMessage('')
    setError('')
    try {
      await apiRequest(`${API_BASE_URL}/candidates/${candidate.id}`, { method: 'DELETE' })
      await refreshCandidates()
      if (results?.candidates?.some(item => item.candidate_id === candidate.id)) setResults(null)
      setMessage(`${name} and their resume files were deleted successfully.`)
    } catch (err) {
      setError(err.message)
    }
  }

  async function uploadResumes(event) {
    event.preventDefault()

    if (!files.length) {
      setError('Please select at least one resume.')
      return
    }
    if (!jobId.trim() || !Number.isInteger(Number(jobId)) || Number(jobId) < 1) {
      setError('Enter a valid job ID before uploading.')
      return
    }

    setLoading(true)
    setMessage('')
    setError('')

    try {
      const formData = new FormData()
      formData.append('job_id', String(Number(jobId)))
      files.forEach(file => formData.append('files', file))

      const data = await apiRequest(`${API_BASE_URL}/resumes/upload`, {
        method: 'POST',
        body: formData,
      })

      await refreshCandidates()
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
        `${API_BASE_URL}/matching/${Number(jobId)}/evaluate`,
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
    if (page === 'manage-candidates') {
      refreshCandidates().catch(err => setError(err.message))
    }
  }

  const allCandidates = results?.candidates || []
  const averageScore = allCandidates.length
    ? allCandidates.reduce((total, candidate) => total + Number(candidate.overall_score || 0), 0) / allCandidates.length
    : 0
  const topScore = allCandidates.length
    ? Math.max(...allCandidates.map(candidate => Number(candidate.overall_score || 0)))
    : 0
  const strongMatches = allCandidates.filter(candidate => Number(candidate.overall_score || 0) >= 70).length
  const filteredCandidateProfiles = candidateProfiles.filter(candidate => {
    const query = candidateProfileSearch.trim().toLowerCase()
    return !query ||
      String(candidate.name || '').toLowerCase().includes(query) ||
      String(candidate.email || '').toLowerCase().includes(query)
  })
  const visibleCandidates = allCandidates
    .filter(candidate => {
      const query = candidateSearch.trim().toLowerCase()
      const matchesSearch = !query ||
        String(candidate.candidate_name || '').toLowerCase().includes(query) ||
        String(candidate.email || '').toLowerCase().includes(query)
      return matchesSearch && Number(candidate.overall_score || 0) >= Number(minimumScore)
    })
    .sort((a, b) => sortOrder === 'lowest'
      ? Number(a.overall_score || 0) - Number(b.overall_score || 0)
      : Number(b.overall_score || 0) - Number(a.overall_score || 0))

  function renderCandidateGroup(items, groupLabel, isRecommended = false) {
    return (
      <section className="candidate-group">
        <div className="candidate-group-heading">
          <h3>{groupLabel}</h3>
          <span>{items.length} candidates</span>
        </div>
        {items.length === 0 ? (
          <div className="empty-state">No candidates in this section yet.</div>
        ) : (
          <div className="candidate-list">
            {items.map((candidate, index) => {
              const isExpanded = expandedCandidate === candidate.candidate_id
              const score = Number(candidate.overall_score || 0)
              return (
                <div className={`candidate-card ${isExpanded ? 'expanded' : ''}`} key={`${groupLabel}-${candidate.candidate_id}`}>
                  <div className="candidate-rank">#{index + 1}</div>
                  <div className="candidate-details">
                    <h3>{candidate.candidate_name}</h3>
                    <p>{candidate.email || 'No email available'}</p>
                    <span>{candidate.resume_name}</span>
                  </div>
                  <div className="candidate-score">
                    <strong>{score.toFixed(1)}%</strong>
                    <span>Overall match</span>
                    {isRecommended && candidate.match_level && (
                      <span className="match-level">{candidate.match_level}</span>
                    )}
                  </div>
                  <div className="candidate-breakdown">
                    {Object.entries(candidate.component_scores || {}).map(([name, value]) => (
                      <span key={name}>{name}: {value == null ? 'N/A' : `${Number(value).toFixed(0)}%`}</span>
                    ))}
                  </div>
                  <button type="button" className="candidate-expand-button"
                    aria-expanded={isExpanded}
                    onClick={() => setExpandedCandidate(isExpanded ? null : candidate.candidate_id)}>
                    {isExpanded ? 'Hide details −' : 'View details +'}
                  </button>
                  {isRecommended && (
                    <button type="button" className="secondary-button"
                      disabled={candidate.addedToJob}
                      onClick={async () => {
                        try {
                          await apiRequest(`${API_BASE_URL}/matching/${Number(jobId)}/candidates/${candidate.candidate_id}/add`, { method: 'POST' })
                          setResults(previous => ({
                            ...previous,
                            applied_candidates: [...(previous.applied_candidates || []), { ...candidate, source: 'RECRUITER_ADDED' }],
                            recommended_candidates: (previous.recommended_candidates || []).filter(item => item.candidate_id !== candidate.candidate_id),
                            applied_count: (previous.applied_count || 0) + 1,
                            recommended_count: Math.max(0, (previous.recommended_count || 0) - 1),
                          }))
                          setMessage(`${candidate.candidate_name} added to this job's workflow.`)
                        } catch (err) {
                          setError(err.message)
                        }
                      }}>
                      Add to job
                    </button>
                  )}
                  {isExpanded && (
                    <div className="candidate-expanded-details">
                      <h4>Matching breakdown</h4>
                      {Object.entries(candidate.component_scores || {}).map(([name, value]) => (
                        <div className="score-row" key={name}>
                          <div className="score-row-label">
                            <span>{name}</span>
                            <strong>{value == null ? 'N/A' : `${Number(value).toFixed(0)}%`}</strong>
                          </div>
                          <div className="score-track">
                            <div className="score-fill" style={{ width: `${value == null ? 0 : Math.max(0, Math.min(100, Number(value)))}%` }} />
                          </div>
                        </div>
                      ))}
                      <h4>Evaluation explanation</h4>
                      <p>{candidate.explanation?.summary || 'No additional explanation is available for this candidate.'}</p>
                      {candidate.explanation?.details && <p>{candidate.explanation.details}</p>}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </section>
    )
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
                {activePage === 'manage-candidates' && 'Manage Candidates'}
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
                {activePage === 'manage-candidates' &&
                  'Search candidate profiles and manage their uploaded resumes.'}
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

              <section className="management-section">
                <div className="management-heading">
                  <div>
                    <h2>Existing jobs</h2>
                    <p className="form-description">Delete a job without deleting its candidates or resumes.</p>
                  </div>
                  <span>{jobs.length} jobs</span>
                </div>
                {jobs.length === 0 ? (
                  <div className="empty-state">No jobs have been created yet.</div>
                ) : (
                  <div className="managed-job-list">
                    {jobs.map(job => (
                      <div className="managed-job" key={job.id}>
                        <div>
                          <strong>{job.title}</strong>
                          <span>Job ID: {job.id}</span>
                        </div>
                        <button type="button" className="danger-button" onClick={() => deleteJob(job)}>
                          Delete job
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            </div>
          )}

          {activePage === 'resumes' && (
            <div className="form-card">
              <h2>Upload candidate resumes</h2>
              <p className="form-description">
                Select the job these resumes were submitted for, then upload PDF or DOCX files.
              </p>

              <form onSubmit={uploadResumes}>
                <label htmlFor="upload-job-id">Select job</label>
                <select
                  id="upload-job-id"
                  value={jobId}
                  onChange={event => setJobId(event.target.value)}
                  required
                >
                  <option value="">Choose a job...</option>
                  {jobs.map(job => <option key={job.id} value={job.id}>#{job.id} · {job.title}</option>)}
                </select>
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

          {activePage === 'manage-candidates' && (
            <section className="management-section candidate-management">
              <div className="management-heading">
                <div>
                  <h2>Candidate profiles</h2>
                  <p className="form-description">Manage profiles and their uploaded resumes.</p>
                </div>
                <span>{filteredCandidateProfiles.length} of {candidateProfiles.length} candidates</span>
              </div>
              <div className="candidate-profile-toolbar">
                <input
                  type="search"
                  aria-label="Search candidate profiles"
                  placeholder="Search by name or email..."
                  value={candidateProfileSearch}
                  onChange={event => setCandidateProfileSearch(event.target.value)}
                />
              </div>
              {candidateProfiles.length === 0 ? (
                <div className="empty-state">No candidate profiles are available.</div>
              ) : filteredCandidateProfiles.length === 0 ? (
                <div className="empty-state">No candidates match this search.</div>
              ) : (
                <div className="managed-candidate-list">
                  {filteredCandidateProfiles.map(candidate => (
                    <article className="managed-candidate" key={candidate.id}>
                      <div className="managed-candidate-heading">
                        <div>
                          <h3>{candidate.name || `Candidate ${candidate.id}`}</h3>
                          <p>{candidate.email || 'No email available'}{candidate.phone ? ` · ${candidate.phone}` : ''}</p>
                        </div>
                        <button type="button" className="danger-button" onClick={() => deleteCandidate(candidate)}>
                          Delete candidate
                        </button>
                      </div>
                      <div className="managed-resume-list">
                        {(candidate.resumes || []).length === 0 ? (
                          <span className="no-resumes">No resumes remain on this profile.</span>
                        ) : candidate.resumes.map((resume, index) => (
                          <div className="managed-resume" key={resume.id}>
                            <div>
                              <strong>{resume.file_name}</strong>
                              {index === 0 && <span className="latest-resume-label">Latest resume</span>}
                              {resume.uploaded_at && <small>Uploaded {new Date(resume.uploaded_at).toLocaleString()}</small>}
                            </div>
                            <div className="resume-actions">
                              <a
                                className="resume-view-button"
                                href={`${API_BASE_URL}/candidates/${candidate.id}/resumes/${resume.id}/file`}
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                View Resume
                              </a>
                              <button type="button" className="danger-button secondary-danger" onClick={() => deleteResume(candidate, resume)}>
                                Remove Resume
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </section>
          )}

          {activePage === 'candidates' && (
            <>
              <div className="form-card evaluation-form">
                <h2>Evaluate candidates</h2>
                <p className="form-description">
                  Enter the ID of an existing job to evaluate uploaded resumes.
                </p>

                <form onSubmit={evaluateCandidates}>
                  <label htmlFor="evaluation-job-id">Select job</label>
                  <select
                    id="evaluation-job-id"
                    value={jobId}
                    onChange={event => setJobId(event.target.value)}
                    required
                  >
                    <option value="">Choose a job...</option>
                    {jobs.map(job => <option key={job.id} value={job.id}>#{job.id} · {job.title}</option>)}
                  </select>
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

                  <div className="evaluation-stats">
                    <div className="stat-card">
                      <span>Total candidates</span>
                      <strong>{allCandidates.length}</strong>
                      <small>Evaluated resumes</small>
                    </div>
                    <div className="stat-card">
                      <span>Top match</span>
                      <strong>{topScore.toFixed(1)}%</strong>
                      <small>Highest overall score</small>
                    </div>
                    <div className="stat-card">
                      <span>Average match</span>
                      <strong>{averageScore.toFixed(1)}%</strong>
                      <small>Across evaluated candidates</small>
                    </div>
                    <div className="stat-card">
                      <span>Strong matches</span>
                      <strong>{strongMatches}</strong>
                      <small>70% match or higher</small>
                    </div>
                  </div>

                  <div className="candidate-toolbar">
                    <input
                      type="search"
                      aria-label="Search candidates"
                      placeholder="Search by candidate name or email..."
                      value={candidateSearch}
                      onChange={event => setCandidateSearch(event.target.value)}
                    />
                    <select
                      aria-label="Minimum match score"
                      value={minimumScore}
                      onChange={event => setMinimumScore(event.target.value)}
                    >
                      <option value="0">All match scores</option>
                      <option value="50">50% and above</option>
                      <option value="70">70% and above</option>
                      <option value="80">80% and above</option>
                    </select>
                    <select
                      aria-label="Sort candidates"
                      value={sortOrder}
                      onChange={event => setSortOrder(event.target.value)}
                    >
                      <option value="highest">Highest score first</option>
                      <option value="lowest">Lowest score first</option>
                    </select>
                  </div>

                  {renderCandidateGroup(
                    (results.applied_candidates || []).filter(candidate => {
                      const query = candidateSearch.trim().toLowerCase()
                      return (!query || String(candidate.candidate_name || '').toLowerCase().includes(query) ||
                        String(candidate.email || '').toLowerCase().includes(query)) &&
                        Number(candidate.overall_score || 0) >= Number(minimumScore)
                    }).sort((a, b) => sortOrder === 'lowest'
                      ? Number(a.overall_score || 0) - Number(b.overall_score || 0)
                      : Number(b.overall_score || 0) - Number(a.overall_score || 0)),
                    'Applied Candidates'
                  )}
                  {renderCandidateGroup(
                    (results.recommended_candidates || []).filter(candidate => {
                      const query = candidateSearch.trim().toLowerCase()
                      return (!query || String(candidate.candidate_name || '').toLowerCase().includes(query) ||
                        String(candidate.email || '').toLowerCase().includes(query)) &&
                        Number(candidate.overall_score || 0) >= Number(minimumScore)
                    }).sort((a, b) => sortOrder === 'lowest'
                      ? Number(a.overall_score || 0) - Number(b.overall_score || 0)
                      : Number(b.overall_score || 0) - Number(a.overall_score || 0)),
                    'AI-Recommended Talent',
                    true
                  )}
                  <p className="results-count">
                    {results.applied_count || 0} applied · {results.recommended_count || 0} AI-recommended · {allCandidates.length} total
                  </p>
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

import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { FiArrowRight, FiCheck, FiClock, FiLogOut, FiPlus, FiRefreshCw, FiSearch, FiShield, FiTrash2, FiX } from 'react-icons/fi'
import { useAuth } from '../auth/authContext'
import * as profileApi from '../api/profile'
import * as membershipApi from '../api/membership'
import * as attendanceApi from '../api/attendance'
import * as dashboardApi from '../api/dashboard'
import * as workoutApi from '../api/workouts'
import * as adminApi from '../api/admin'
import { getErrorMessage } from '../api/client'
import './PortalPages.css'

function isRecord(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

function isRecordArray(value) {
  return Array.isArray(value) && value.every(isRecord)
}

function hasScalarFields(value, fields) {
  return isRecord(value) && fields.every((field) => {
    const fieldValue = value[field]
    return fieldValue == null || ['string', 'number', 'boolean'].includes(typeof fieldValue)
  })
}

function isMembership(value) {
  return value === null || (
    hasScalarFields(value, ['plan_name', 'status', 'end_date', 'remaining_days', 'price', 'start_date'])
  )
}

function isMembershipRecords(value) {
  return isRecordArray(value)
    && value.every((record) => hasScalarFields(record, ['id', 'plan_name', 'start_date', 'end_date', 'status', 'price']))
}

function isAttendanceRecords(value) {
  return isRecordArray(value)
    && value.every((record) => hasScalarFields(record, ['id', 'attendance_date', 'check_in_time', 'check_out_time', 'status']))
}

function isWorkoutRecords(value) {
  return isRecordArray(value)
    && value.every((record) => (
      hasScalarFields(record, ['id', 'workout_type', 'workout_date', 'duration'])
      && (record.exercises == null || isRecordArray(record.exercises))
    ))
}

function isProgressRecords(value) {
  return isRecordArray(value)
    && value.every((record) => hasScalarFields(record, ['id', 'record_date', 'weight', 'body_fat']))
}

function isMemberRecords(value) {
  return isRecordArray(value)
    && value.every((member) => (
      hasScalarFields(member, ['id', 'name', 'email', 'phone', 'status', 'membership_status', 'is_active'])
      && (member.membership == null || hasScalarFields(member.membership, ['plan_name']))
    ))
}

function isPlanRecords(value) {
  return isRecordArray(value)
    && value.every((plan) => (
      hasScalarFields(plan, ['id', 'name', 'plan_type', 'monthly_price', 'is_active'])
      && Array.isArray(plan.durations_months)
      && plan.durations_months.every((duration) => ['number', 'string'].includes(typeof duration))
    ))
}

function isAnnouncementRecords(value) {
  return isRecordArray(value)
    && value.every((item) => hasScalarFields(item, ['id', 'title', 'body', 'is_active', 'created_at']))
}

function useLoad(loader, dependencies = [], validate) {
  const loaderRef = useRef(loader)
  const validateRef = useRef(validate)
  const [state, setState] = useState({ key: null, data: null, error: '' })
  const [reload, setReload] = useState(0)
  const dependencyKey = JSON.stringify(dependencies)
  const requestKey = `${dependencyKey}:${reload}`

  useEffect(() => {
    loaderRef.current = loader
  }, [loader])

  useEffect(() => {
    validateRef.current = validate
  }, [validate])

  useEffect(() => {
    let current = true
    loaderRef.current()
      .then((result) => {
        if (!current) return
        if (validateRef.current && !validateRef.current(result)) {
          throw new Error('FitZone returned data in an unexpected format. Please try again.')
        }
        setState({ key: requestKey, data: result, error: '' })
      })
      .catch((reason) => {
        if (current) {
          const fallback = reason instanceof Error
            ? reason.message
            : 'Unable to load FitZone data. Please try again.'
          setState({ key: requestKey, data: null, error: getErrorMessage(reason, fallback) })
        }
      })
    return () => { current = false }
  }, [requestKey])

  return {
    data: state.key === requestKey ? state.data : null,
    loading: state.key !== requestKey,
    error: state.key === requestKey ? state.error : '',
    reload: () => setReload((value) => value + 1),
  }
}

function PortalShell({ eyebrow, title, description, children }) {
  const { user, signOut } = useAuth()
  return (
    <main className="portal-page">
      <div className="portal-topline">
        <div className="portal-container portal-topline-inner">
          <span><FiShield /> SECURE FITZONE PORTAL</span>
          <div><span>{user?.name}</span><button type="button" onClick={signOut}><FiLogOut /> Sign out</button></div>
        </div>
      </div>
      <header className="portal-hero">
        <div className="portal-container">
          <p className="portal-eyebrow">{eyebrow}</p>
          <h1>{title}</h1>
          {description && <p>{description}</p>}
        </div>
      </header>
      <div className="portal-container portal-content">{children}</div>
    </main>
  )
}

function PortalState({ loading, error, empty, onRetry, loadingMessage = 'Loading FitZone data…', children }) {
  if (loading) return <div className="portal-state" role="status">{loadingMessage}</div>
  if (error) {
    return <div className="portal-state portal-error" role="alert"><span>{error}</span>{onRetry && <button type="button" onClick={onRetry}><FiRefreshCw /> Try again</button>}</div>
  }
  if (empty) return <div className="portal-state">{empty}</div>
  return children
}

function Feedback({ message, error = false }) {
  if (!message) return null
  return <p className={`portal-feedback${error ? ' is-error' : ''}`} role={error ? 'alert' : 'status'}>{message}</p>
}

export function LoginPage() {
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const user = await signIn({ email: email.trim(), password })
      navigate(user.role === 'admin' ? '/admin' : '/dashboard', { replace: true })
    } catch (reason) {
      setError(reason.status === 401 ? 'Email or password was incorrect, or the account is inactive.' : getErrorMessage(reason))
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="portal-auth-page">
      <section className="portal-auth-card">
        <p className="portal-eyebrow">WELCOME BACK</p>
        <h1>Log in to <span>FitZone.</span></h1>
        <p className="portal-auth-intro">Access your training, membership, and progress.</p>
        <Feedback message={error} error />
        <form className="portal-form" onSubmit={submit}>
          <label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required /></label>
          <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required /></label>
          <button className="portal-primary" disabled={busy}>{busy ? 'Signing in…' : 'SIGN IN'} <FiArrowRight /></button>
        </form>
        <p className="portal-auth-switch">New to FitZone? <Link to="/register">Create your account</Link></p>
        <Link className="portal-back-link" to="/">← Back to FitZone</Link>
      </section>
    </main>
  )
}

export function RegisterPage() {
  const { signUp } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', phone: '', password: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  function update(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }))
  }

  async function submit(event) {
    event.preventDefault()
    setError('')
    setSuccess('')
    if (form.name.trim().length > 120 || form.password.length < 8 || form.password.length > 128) {
      setError('Enter a name under 120 characters and a password between 8 and 128 characters.')
      return
    }
    setBusy(true)
    try {
      await signUp({ ...form, name: form.name.trim(), email: form.email.trim(), phone: form.phone.trim() })
      setSuccess('Account created. Sign in to access your member dashboard.')
      window.setTimeout(() => navigate('/login', { replace: true }), 700)
    } catch (reason) {
      setError(reason.status === 409 ? 'An account with this email already exists.' : getErrorMessage(reason))
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="portal-auth-page">
      <section className="portal-auth-card">
        <p className="portal-eyebrow">START YOUR JOURNEY</p>
        <h1>Join <span>FitZone.</span></h1>
        <p className="portal-auth-intro">Create your member account to track your fitness journey.</p>
        <Feedback message={error} error />
        <Feedback message={success} />
        <form className="portal-form" onSubmit={submit}>
          <label>Full name<input name="name" value={form.name} onChange={update} autoComplete="name" maxLength="120" required /></label>
          <label>Email<input name="email" type="email" value={form.email} onChange={update} autoComplete="email" required /></label>
          <label>Phone<input name="phone" type="tel" value={form.phone} onChange={update} autoComplete="tel" minLength="7" required /></label>
          <label>Password<input name="password" type="password" value={form.password} onChange={update} autoComplete="new-password" minLength="8" maxLength="128" required /></label>
          <button className="portal-primary" disabled={busy}>{busy ? 'Creating account…' : 'CREATE ACCOUNT'} <FiArrowRight /></button>
        </form>
        <p className="portal-auth-switch">Already a member? <Link to="/login">Sign in</Link></p>
      </section>
    </main>
  )
}

export function ProfilePage() {
  const { token, refreshProfile } = useAuth()
  const { data, loading, error, reload } = useLoad(
    () => profileApi.getProfile(token),
    [token],
    (result) => isRecord(result)
      && hasScalarFields(result.user, ['id', 'name', 'email', 'phone', 'fitness_goal', 'date_of_birth', 'gender', 'profile_photo'])
      && typeof result.user.name === 'string'
      && typeof result.user.email === 'string',
  )
  const membership = useLoad(
    () => membershipApi.getCurrentMembership(token),
    [token],
    (result) => isRecord(result) && isMembership(result.membership),
  )
  const profileUser = isRecord(data?.user) ? data.user : null
  const currentMembership = isMembership(membership.data?.membership) && isRecord(membership.data.membership)
    ? membership.data.membership
    : null
  const [formOverride, setFormOverride] = useState(null)
  const [message, setMessage] = useState('')
  const [saving, setSaving] = useState(false)
  const form = formOverride || (profileUser ? {
      name: profileUser.name || '',
      phone: profileUser.phone || '',
      fitness_goal: profileUser.fitness_goal || '',
      date_of_birth: profileUser.date_of_birth || '',
      gender: profileUser.gender || '',
      profile_photo: profileUser.profile_photo || '',
    } : null)

  async function submit(event) {
    event.preventDefault()
    setSaving(true)
    setMessage('')
    const values = Object.fromEntries(Object.entries(form).map(([key, value]) => [key, value || null]))
    try {
      await profileApi.updateProfile(token, values)
      await refreshProfile()
      setFormOverride(Object.fromEntries(Object.entries(values).map(([key, value]) => [key, value || ''])))
      setMessage('Profile updated successfully.')
      reload()
    } catch (reason) {
      setMessage(getErrorMessage(reason))
    } finally {
      setSaving(false)
    }
  }

  return (
    <PortalShell eyebrow="YOUR ACCOUNT" title="PROFILE" description="Keep your member information up to date.">
      <PortalState loading={loading} error={error} onRetry={reload}>
        {form && profileUser && <section className="portal-panel">
          <div className="portal-section-heading"><h2>Personal information</h2><p>Email: {profileUser.email}</p></div>
          <Feedback message={message} error={Boolean(message && !message.includes('successfully'))} />
          <form className="portal-form portal-form-grid" onSubmit={submit}>
            <label>Full name<input value={form.name} onChange={(e) => setFormOverride({ ...form, name: e.target.value })} required /></label>
            <label>Phone<input value={form.phone} onChange={(e) => setFormOverride({ ...form, phone: e.target.value })} /></label>
            <label>Fitness goal<input value={form.fitness_goal} maxLength="80" onChange={(e) => setFormOverride({ ...form, fitness_goal: e.target.value })} /></label>
            <label>Date of birth<input type="date" value={form.date_of_birth} onChange={(e) => setFormOverride({ ...form, date_of_birth: e.target.value })} /></label>
            <label>Gender<select value={form.gender} onChange={(e) => setFormOverride({ ...form, gender: e.target.value })}><option value="">Choose</option><option value="male">Male</option><option value="female">Female</option><option value="non-binary">Non-binary</option><option value="other">Other</option><option value="prefer_not_to_say">Prefer not to say</option></select></label>
            <label>Profile photo URL<input type="url" value={form.profile_photo} onChange={(e) => setFormOverride({ ...form, profile_photo: e.target.value })} /></label>
            <button className="portal-primary" disabled={saving}>{saving ? 'Saving…' : 'SAVE PROFILE'} <FiCheck /></button>
          </form>
        </section>}
      </PortalState>
      <section className="portal-panel">
        <div className="portal-section-heading"><h2>Membership</h2><Link to="/membership">View plans <FiArrowRight /></Link></div>
        <PortalState loading={membership.loading} error={membership.error} onRetry={membership.reload} empty={!membership.loading && !membership.error && !currentMembership ? 'No current membership. Contact the team to choose a plan.' : null}>
          {currentMembership
            ? <p>{currentMembership.plan_name} · {currentMembership.status} · expires {currentMembership.end_date} · {currentMembership.remaining_days} days remaining</p>
            : <EmptyHint>No current membership. Contact the team to choose a plan.</EmptyHint>}
        </PortalState>
        {profileUser?.email && <p className="portal-auth-intro">Account: {profileUser.email}</p>}
      </section>
    </PortalShell>
  )
}

export function MemberMembershipPage() {
  const { token } = useAuth()
  const current = useLoad(
    () => membershipApi.getCurrentMembership(token),
    [token],
    (response) => isRecord(response) && isMembership(response.membership),
  )
  const plans = useLoad(
    () => membershipApi.getPlans(),
    [token],
    (response) => isRecord(response) && isRecordArray(response.plans)
      && response.plans.every((plan) => (
        typeof plan.plan_type === 'string'
        && typeof plan.plan_name === 'string'
        && Array.isArray(plan.durations_months)
        && isRecord(plan.prices)
      )),
  )
  const activeMembership = isRecord(current.data?.membership) ? current.data.membership : null
  const availablePlans = isRecordArray(plans.data?.plans) ? plans.data.plans : []

  return (
    <PortalShell eyebrow="MEMBER AREA" title="MEMBERSHIP" description="Review your current membership and explore available FitZone plans.">
      <section className="portal-panel">
        <div className="portal-section-heading"><h2>Your current membership</h2></div>
        <PortalState
          loading={current.loading}
          error={current.error}
          onRetry={current.reload}
          empty={!current.loading && !current.error && !activeMembership ? 'You do not have an active membership. Contact the FitZone team to get started.' : null}
        >
          {activeMembership && <div className="portal-inline-stats">
            <div><strong>{activeMembership.plan_name}</strong><span>Current plan</span></div>
            <div><strong>{activeMembership.status}</strong><span>Membership status</span></div>
            <div><strong>{activeMembership.remaining_days ?? '—'}</strong><span>Days remaining</span></div>
            <div><strong>{activeMembership.end_date || '—'}</strong><span>Expiry date</span></div>
          </div>}
        </PortalState>
      </section>
      <section className="portal-panel">
        <div className="portal-section-heading"><h2>Available plans</h2><p>Ask the FitZone team about joining or changing your plan.</p></div>
        <PortalState
          loading={plans.loading}
          error={plans.error}
          onRetry={plans.reload}
          empty={!plans.loading && !plans.error && !availablePlans.length ? 'No plans are currently available.' : null}
        >
          <div className="portal-dashboard-grid">
            {availablePlans.map((plan) => (
              <article className="portal-stat-card" key={plan.plan_type}>
                <p>{plan.plan_type.toUpperCase()}</p>
                <strong>{plan.plan_name}</strong>
                <span>{formatINR(plan.monthly_price)} / month</span>
                <small>{plan.durations_months.join(', ')} month durations available</small>
              </article>
            ))}
          </div>
        </PortalState>
      </section>
    </PortalShell>
  )
}

export function MemberDashboardPage() {
  const { token, user } = useAuth()
  const [todayDate] = useState(() => new Date())
  const { data, loading, error, reload } = useLoad(
    () => dashboardApi.getMemberDashboard(token),
    [token],
    (response) => isRecord(response)
      && isRecord(response.user)
      && hasScalarFields(response.attendance, ['current_streak', 'longest_streak', 'current_month_attendance', 'total_attendance_days', 'last_attendance_date'])
      && isMembership(response.membership)
      && (response.progress === null || hasScalarFields(response.progress, ['record_date', 'weight', 'body_fat', 'height']))
      && isWorkoutRecords(response.recent_workouts)
      && isAnnouncementRecords(response.recent_notifications),
  )
  const recentAttendance = useLoad(() => attendanceApi.getAttendanceHistory(token, {
    month: todayDate.getMonth() + 1,
    year: todayDate.getFullYear(),
  }), [token], (result) => isRecord(result) && isAttendanceRecords(result.attendance))
  const membershipHistory = useLoad(
    () => membershipApi.getMembershipHistory(token),
    [token],
    (result) => isRecord(result) && isMembershipRecords(result.memberships),
  )
  const membershipRecords = isMembershipRecords(membershipHistory.data?.memberships)
    ? membershipHistory.data.memberships
    : null
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const attendance = isRecord(data?.attendance) ? data.attendance : {}
  const todayKey = localDateValue(todayDate)
  const recentAttendanceRecords = isAttendanceRecords(recentAttendance.data?.attendance)
    ? recentAttendance.data.attendance
    : []
  const todayRecord = recentAttendanceRecords.find((item) => item.attendance_date === todayKey)

  async function markAttendance(action) {
    setBusy(true)
    setMessage('')
    try {
      const response = action === 'in'
        ? await attendanceApi.checkIn(token)
        : await attendanceApi.checkOut(token)
      setMessage(response.message)
      reload()
      recentAttendance.reload()
    } catch (reason) {
      setMessage(getErrorMessage(reason))
    } finally {
      setBusy(false)
    }
  }

  if (loading || error || !data) {
    return (
      <PortalShell eyebrow="MEMBER DASHBOARD" title={`WELCOME, ${(user?.name || 'MEMBER').split(' ')[0].toUpperCase()}.`} description="Your membership, training consistency, and progress at a glance.">
        <PortalState
          loading={loading}
          error={error}
          empty={!loading && !error ? 'No dashboard data available.' : null}
          onRetry={reload}
          loadingMessage="Loading your dashboard..."
        />
      </PortalShell>
    )
  }

  return (
    <PortalShell eyebrow="MEMBER DASHBOARD" title={`WELCOME, ${(user?.name || 'MEMBER').split(' ')[0].toUpperCase()}.`} description="Your membership, training consistency, and progress at a glance.">
        <Feedback message={message} error={Boolean(message && /expired|already|active membership|must check in/i.test(message))} />
        <div className="portal-stat-grid">
          <StatCard label="MEMBERSHIP" value={data.membership ? data.membership.plan_name : 'No active plan'} detail={data.membership ? `Expires ${data.membership.end_date}` : 'Talk to the team to get started'} />
          <StatCard label="DAYS REMAINING" value={data.membership ? data.membership.remaining_days : '—'} detail={data.membership ? 'On your current membership' : 'Membership not active'} />
          <StatCard label="CURRENT STREAK" value={attendance?.current_streak ?? 0} detail="Consecutive attendance days" />
          <StatCard label="LONGEST STREAK" value={attendance?.longest_streak ?? 0} detail="Your personal best" />
        </div>
        <div className="portal-dashboard-grid">
          <section className="portal-panel">
            <div className="portal-section-heading"><h2>Training consistency</h2><p>Real attendance from your FitZone account.</p></div>
            <div className="portal-inline-stats"><div><strong>{attendance?.current_month_attendance ?? 0}</strong><span>This month</span></div><div><strong>{attendance?.total_attendance_days ?? 0}</strong><span>Total visits</span></div><div><strong>{attendance?.last_attendance_date || '—'}</strong><span>Last visit</span></div></div>
            <div className="portal-action-row">
              <button className="portal-primary" disabled={busy || recentAttendance.loading || Boolean(todayRecord)} onClick={() => markAttendance('in')}>{busy ? 'Working…' : todayRecord ? 'CHECKED IN TODAY' : 'CHECK IN'} <FiCheck /></button>
              <button className="portal-secondary" disabled={busy || !todayRecord || Boolean(todayRecord.check_out_time)} onClick={() => markAttendance('out')}>CHECK OUT <FiClock /></button>
              <Link className="portal-secondary portal-link-button" to="/attendance">ATTENDANCE HISTORY <FiArrowRight /></Link>
            </div>
            {recentAttendance.error && <Feedback message={recentAttendance.error} error />}
          </section>
          <section className="portal-panel">
            <div className="portal-section-heading"><h2>Membership history</h2><Link to="/membership">View plans <FiArrowRight /></Link></div>
            <PortalState
              loading={membershipHistory.loading}
              error={membershipHistory.error}
              onRetry={membershipHistory.reload}
              empty={!membershipHistory.loading && !membershipHistory.error && !membershipRecords?.length ? 'No membership history available.' : null}
            >
              {membershipRecords && <div className="portal-record-list">{membershipRecords.map((item) => <article key={item.id}><div><strong>{item.plan_name}</strong><span>{item.start_date} — {item.end_date}</span></div><small>{item.status} · {formatINR(item.price)}</small></article>)}</div>}
            </PortalState>
          </section>
          <section className="portal-panel">
            <div className="portal-section-heading"><h2>Latest progress</h2><Link to="/workouts">Workouts &amp; progress <FiArrowRight /></Link></div>
            {data.progress ? <div className="portal-measurements"><Measure label="Weight" value={data.progress.weight} unit="kg" /><Measure label="Body fat" value={data.progress.body_fat} unit="%" /><Measure label="Height" value={data.progress.height} unit="cm" /><p>Recorded {data.progress.record_date}</p></div> : <EmptyHint>No progress records yet.</EmptyHint>}
          </section>
        </div>
        <section className="portal-panel">
          <div className="portal-section-heading"><h2>Recent workouts</h2><Link to="/workouts">View workouts <FiArrowRight /></Link></div>
          {data.recent_workouts?.length ? <div className="portal-table-wrap"><table><thead><tr><th>Date</th><th>Workout</th><th>Duration</th><th>Exercises</th></tr></thead><tbody>{data.recent_workouts.map((workout) => <tr key={workout.id}><td>{workout.workout_date}</td><td>{workout.workout_type}</td><td>{workout.duration} min</td><td>{workout.exercises?.length || 0}</td></tr>)}</tbody></table></div> : <EmptyHint>No workouts recorded yet.</EmptyHint>}
        </section>
        {data.recent_notifications?.length > 0 && <section className="portal-panel"><div className="portal-section-heading"><h2>Gym announcements</h2></div>{data.recent_notifications.map((item) => <article className="portal-announcement" key={item.id}><h3>{item.title}</h3><p>{item.body}</p></article>)}</section>}
    </PortalShell>
  )
}

function StatCard({ label, value, detail }) {
  return <article className="portal-stat-card"><p>{label}</p><strong>{value}</strong><span>{detail}</span></article>
}

function Measure({ label, value, unit }) {
  return <div><span>{label}</span><strong>{value == null ? '—' : `${value} ${unit}`}</strong></div>
}

function EmptyHint({ children }) {
  return <p className="portal-empty-hint">{children}</p>
}

function localDateValue(value) {
  return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`
}

export function AttendancePage() {
  const { token } = useAuth()
  const [todayDate] = useState(() => new Date())
  const [filter, setFilter] = useState({ month: String(todayDate.getMonth() + 1), year: String(todayDate.getFullYear()) })
  const summary = useLoad(
    () => attendanceApi.getAttendanceSummary(token),
    [token],
    (result) => isRecord(result)
      && hasScalarFields(result.summary, ['current_streak', 'longest_streak', 'total_attendance_days', 'current_month_attendance', 'last_attendance_date']),
  )
  const history = useLoad(
    () => attendanceApi.getAttendanceHistory(token, filter),
    [token, filter.month, filter.year],
    (result) => isRecord(result) && isAttendanceRecords(result.attendance),
  )
  const todayHistory = useLoad(() => attendanceApi.getAttendanceHistory(token, {
    month: todayDate.getMonth() + 1,
    year: todayDate.getFullYear(),
  }), [token], (result) => isRecord(result) && isAttendanceRecords(result.attendance))
  const [actionMessage, setActionMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const todayKey = localDateValue(todayDate)
  const attendanceRecords = isAttendanceRecords(history.data?.attendance) ? history.data.attendance : []
  const todayRecords = isAttendanceRecords(todayHistory.data?.attendance) ? todayHistory.data.attendance : []
  const today = todayRecords.find((record) => record.attendance_date === todayKey) || null
  const reload = () => { summary.reload(); history.reload(); todayHistory.reload() }
  async function mark(action) {
    setBusy(true)
    setActionMessage('')
    try {
      const result = action === 'in' ? await attendanceApi.checkIn(token) : await attendanceApi.checkOut(token)
      setActionMessage(result.message)
      reload()
    } catch (error) {
      setActionMessage(getErrorMessage(error))
    } finally {
      setBusy(false)
    }
  }
  const currentSummary = summary.data?.summary
  return (
    <PortalShell eyebrow="MEMBER AREA" title="ATTENDANCE" description="Check in, review your visits, and keep your streak moving.">
      <PortalState loading={summary.loading} error={summary.error} onRetry={summary.reload}>
        <div className="portal-stat-grid">
          <StatCard label="CURRENT STREAK" value={currentSummary?.current_streak ?? 0} detail="Consecutive days" />
          <StatCard label="LONGEST STREAK" value={currentSummary?.longest_streak ?? 0} detail="Personal best" />
          <StatCard label="TOTAL VISITS" value={currentSummary?.total_attendance_days ?? 0} detail="All recorded visits" />
          <StatCard label="THIS MONTH" value={currentSummary?.current_month_attendance ?? 0} detail="Attendance days" />
        </div>
        <section className="portal-panel portal-checkin-panel">
          <div><p className="portal-eyebrow">TODAY'S SESSION</p><h2>{today ? `Checked in at ${new Date(today.check_in_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : 'Ready to train?'}</h2><p>{today?.check_out_time ? `Checked out at ${new Date(today.check_out_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : 'Your check-in is recorded against your active membership.'}</p></div>
          <div className="portal-action-row"><button className="portal-primary" disabled={busy || todayHistory.loading || Boolean(today)} onClick={() => mark('in')}>{busy ? 'Working…' : today ? 'CHECKED IN' : 'CHECK IN'} <FiCheck /></button><button className="portal-secondary" disabled={busy || todayHistory.loading || !today || Boolean(today.check_out_time)} onClick={() => mark('out')}>CHECK OUT <FiClock /></button></div>
          {todayHistory.error && <Feedback message={todayHistory.error} error />}
          <Feedback message={actionMessage} error={Boolean(actionMessage && /expired|already|membership/i.test(actionMessage))} />
        </section>
        <section className="portal-panel">
          <div className="portal-section-heading"><div><h2>Attendance history</h2><p>Last attendance: {currentSummary?.last_attendance_date || 'No visits recorded'}</p></div><div className="portal-filter-row"><label>Month<select value={filter.month} onChange={(e) => setFilter({ ...filter, month: e.target.value })}>{Array.from({ length: 12 }, (_, index) => <option key={index + 1} value={index + 1}>{new Date(2000, index).toLocaleString('en', { month: 'long' })}</option>)}</select></label><label>Year<input type="number" value={filter.year} onChange={(e) => setFilter({ ...filter, year: e.target.value })} min="2000" max="9999" /></label></div></div>
          <PortalState loading={history.loading} error={history.error} onRetry={history.reload} empty={!history.loading && !history.error && !attendanceRecords.length ? 'No attendance records for this period.' : null}>
            <AttendanceTable records={attendanceRecords} />
          </PortalState>
        </section>
      </PortalState>
    </PortalShell>
  )
}

function AttendanceTable({ records }) {
  const attendanceRecords = isAttendanceRecords(records) ? records : []
  return <div className="portal-table-wrap"><table><thead><tr><th>Date</th><th>Check in</th><th>Check out</th><th>Status</th></tr></thead><tbody>{attendanceRecords.map((record, index) => {
    const status = typeof record.status === 'string' ? record.status : 'unknown'
    return <tr key={record.id ?? `${record.attendance_date || 'attendance'}-${index}`}><td>{record.attendance_date || '—'}</td><td>{record.check_in_time ? new Date(record.check_in_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—'}</td><td>{record.check_out_time ? new Date(record.check_out_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—'}</td><td><span className={`portal-status ${status}`}>{status.replace('_', ' ')}</span></td></tr>
  })}</tbody></table></div>
}

export function WorkoutsPage() {
  const { token } = useAuth()
  const [todayDate] = useState(() => new Date())
  const workouts = useLoad(
    () => workoutApi.getWorkouts(token),
    [token],
    (result) => isRecord(result) && isWorkoutRecords(result.workouts),
  )
  const progress = useLoad(
    () => workoutApi.getProgress(token),
    [token],
    (result) => isRecord(result) && isProgressRecords(result.progress),
  )
  const workoutRecords = isWorkoutRecords(workouts.data?.workouts) ? workouts.data.workouts : []
  const progressRecords = isProgressRecords(progress.data?.progress) ? progress.data.progress : []
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [progressBusy, setProgressBusy] = useState(false)
  const [progressMessage, setProgressMessage] = useState('')
  async function submit(event) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const body = {
      workout_type: data.get('workout_type'),
      duration: Number(data.get('duration')),
      workout_date: data.get('workout_date'),
      notes: data.get('notes') || null,
      exercises: [],
    }
    setBusy(true)
    setMessage('')
    try {
      const result = await workoutApi.createWorkout(token, body)
      setMessage(result.message)
      event.target.reset()
      workouts.reload()
    } catch (error) {
      setMessage(getErrorMessage(error))
    } finally {
      setBusy(false)
    }
  }
  async function submitProgress(event) {
    event.preventDefault()
    const form = event.currentTarget
    const data = new FormData(form)
    const body = { record_date: data.get('record_date') }
    for (const field of ['weight', 'height', 'body_fat', 'chest', 'waist', 'arms']) {
      const value = data.get(field)
      if (value !== '') body[field] = Number(value)
    }
    if (data.get('notes')) body.notes = data.get('notes')
    setProgressBusy(true)
    setProgressMessage('')
    try {
      const result = await workoutApi.createProgress(token, body)
      setProgressMessage(result.message)
      form.reset()
      progress.reload()
    } catch (error) {
      setProgressMessage(getErrorMessage(error))
    } finally {
      setProgressBusy(false)
    }
  }
  return (
    <PortalShell eyebrow="MEMBER AREA" title="TRAINING LOG" description="Your workout and body-measurement records, connected to your FitZone account.">
      <section className="portal-panel">
        <div className="portal-section-heading"><h2>Log a workout</h2><p>Record workout type and duration. Add sets and exercises through the API when your full workout editor is ready.</p></div>
        <Feedback message={message} error={Boolean(message && /unable|must|valid/i.test(message))} />
        <form className="portal-form portal-form-grid" onSubmit={submit}><label>Workout type<input name="workout_type" required maxLength="80" placeholder="Strength training" /></label><label>Duration (minutes)<input name="duration" type="number" required min="1" /></label><label>Date<input name="workout_date" type="date" defaultValue={localDateValue(todayDate)} required /></label><label>Notes<input name="notes" maxLength="5000" /></label><button className="portal-primary" disabled={busy}>{busy ? 'Saving…' : 'SAVE WORKOUT'} <FiPlus /></button></form>
      </section>
      <section className="portal-panel">
        <div className="portal-section-heading"><h2>Record progress</h2><p>Only the measurements you enter are saved.</p></div>
        <Feedback message={progressMessage} error={Boolean(progressMessage && /unable|must|valid|provide/i.test(progressMessage))} />
        <form className="portal-form portal-form-grid" onSubmit={submitProgress}>
          <label>Record date<input name="record_date" type="date" defaultValue={localDateValue(todayDate)} required /></label>
          <label>Weight (kg)<input name="weight" type="number" min="0.1" step="0.1" /></label>
          <label>Height (cm)<input name="height" type="number" min="0.1" step="0.1" /></label>
          <label>Body fat (%)<input name="body_fat" type="number" min="0" max="100" step="0.1" /></label>
          <label>Chest (cm)<input name="chest" type="number" min="0.1" step="0.1" /></label>
          <label>Waist (cm)<input name="waist" type="number" min="0.1" step="0.1" /></label>
          <label>Arms (cm)<input name="arms" type="number" min="0.1" step="0.1" /></label>
          <label>Notes<input name="notes" maxLength="5000" /></label>
          <button className="portal-primary" disabled={progressBusy}>{progressBusy ? 'Saving…' : 'SAVE PROGRESS'} <FiPlus /></button>
        </form>
      </section>
      <div className="portal-dashboard-grid">
        <section className="portal-panel"><div className="portal-section-heading"><h2>Workout history</h2></div><PortalState loading={workouts.loading} error={workouts.error} onRetry={workouts.reload} empty={!workouts.loading && !workouts.error && !workoutRecords.length ? 'No workouts recorded yet.' : null}><div className="portal-record-list">{workoutRecords.map((item) => <article key={item.id}><div><strong>{item.workout_type}</strong><span>{item.workout_date} · {item.duration} min</span></div><small>{item.exercises?.length || 0} exercises</small></article>)}</div></PortalState></section>
        <section className="portal-panel"><div className="portal-section-heading"><h2>Progress history</h2></div><PortalState loading={progress.loading} error={progress.error} onRetry={progress.reload} empty={!progress.loading && !progress.error && !progressRecords.length ? 'No progress measurements recorded yet.' : null}><div className="portal-record-list">{progressRecords.map((item) => <article key={item.id}><div><strong>{item.record_date}</strong><span>{item.weight == null ? 'Weight not recorded' : `${item.weight} kg`}</span></div><small>{item.body_fat == null ? '—' : `${item.body_fat}% fat`}</small></article>)}</div></PortalState></section>
      </div>
    </PortalShell>
  )
}

export function ProgressPage() {
  const { token } = useAuth()
  const [todayDate] = useState(() => new Date())
  const progress = useLoad(
    () => workoutApi.getProgress(token),
    [token],
    (response) => isRecord(response) && isProgressRecords(response.progress),
  )
  const progressRecords = isProgressRecords(progress.data?.progress) ? progress.data.progress : []
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')

  async function submitProgress(event) {
    event.preventDefault()
    const form = event.currentTarget
    const data = new FormData(form)
    const body = { record_date: data.get('record_date') }
    for (const field of ['weight', 'height', 'body_fat', 'chest', 'waist', 'arms']) {
      const value = data.get(field)
      if (value !== '') body[field] = Number(value)
    }
    if (data.get('notes')) body.notes = data.get('notes')
    setBusy(true)
    setMessage('')
    try {
      const response = await workoutApi.createProgress(token, body)
      setMessage(response.message || 'Progress saved.')
      form.reset()
      progress.reload()
    } catch (error) {
      setMessage(getErrorMessage(error))
    } finally {
      setBusy(false)
    }
  }

  return (
    <PortalShell eyebrow="MEMBER AREA" title="FITNESS PROGRESS" description="Record and review your fitness measurements over time.">
      <section className="portal-panel">
        <div className="portal-section-heading"><h2>Record progress</h2><p>Only the measurements you enter are saved.</p></div>
        <Feedback message={message} error={Boolean(message && /unable|must|valid|provide/i.test(message))} />
        <form className="portal-form portal-form-grid" onSubmit={submitProgress}>
          <label>Record date<input name="record_date" type="date" defaultValue={localDateValue(todayDate)} required /></label>
          <label>Weight (kg)<input name="weight" type="number" min="0.1" step="0.1" /></label>
          <label>Height (cm)<input name="height" type="number" min="0.1" step="0.1" /></label>
          <label>Body fat (%)<input name="body_fat" type="number" min="0" max="100" step="0.1" /></label>
          <label>Chest (cm)<input name="chest" type="number" min="0.1" step="0.1" /></label>
          <label>Waist (cm)<input name="waist" type="number" min="0.1" step="0.1" /></label>
          <label>Arms (cm)<input name="arms" type="number" min="0.1" step="0.1" /></label>
          <label>Notes<input name="notes" maxLength="5000" /></label>
          <button className="portal-primary" disabled={busy}>{busy ? 'Saving…' : 'SAVE PROGRESS'} <FiPlus /></button>
        </form>
      </section>
      <section className="portal-panel">
        <div className="portal-section-heading"><h2>Progress history</h2></div>
        <PortalState
          loading={progress.loading}
          error={progress.error}
          onRetry={progress.reload}
          empty={!progress.loading && !progress.error && !progressRecords.length ? 'No progress measurements recorded yet.' : null}
        >
          <div className="portal-record-list">{progressRecords.map((item) => (
            <article key={item.id}>
              <div><strong>{item.record_date}</strong><span>{item.weight == null ? 'Weight not recorded' : `${item.weight} kg`}</span></div>
              <small>{item.body_fat == null ? '—' : `${item.body_fat}% fat`}</small>
            </article>
          ))}</div>
        </PortalState>
      </section>
    </PortalShell>
  )
}

export function AdminDashboardPage() {
  const { token } = useAuth()
  const result = useLoad(
    () => adminApi.getAdminDashboard(token),
    [token],
    (response) => isRecord(response)
      && isRecord(response.statistics)
      && hasScalarFields(response.statistics, ['total_members', 'active_members', 'expired_members', 'today_attendance', 'new_members', 'members_expiring_soon', 'monthly_revenue', 'total_revenue'])
      && isRecord(response.trends)
      && isRecordArray(response.trends.daily_last_7_days)
      && response.trends.daily_last_7_days.every((item) => hasScalarFields(item, ['date', 'attendance', 'revenue'])),
  )
  const statistics = isRecord(result.data?.statistics) ? result.data.statistics : {}
  const dailyTrend = isRecordArray(result.data?.trends?.daily_last_7_days)
    ? result.data.trends.daily_last_7_days
    : []
  return (
    <AdminLayout title="ADMIN OVERVIEW" description="Gym operations and performance, powered by live backend data.">
      <PortalState loading={result.loading} error={result.error} onRetry={result.reload}>
        <div className="portal-stat-grid admin-stat-grid">
          <StatCard label="TOTAL MEMBERS" value={statistics.total_members ?? '—'} detail="Registered member accounts" />
          <StatCard label="ACTIVE MEMBERS" value={statistics.active_members ?? '—'} detail="Currently in membership" />
          <StatCard label="EXPIRED MEMBERS" value={statistics.expired_members ?? '—'} detail="No active membership" />
          <StatCard label="TODAY'S VISITS" value={statistics.today_attendance ?? '—'} detail="Attendance records today" />
          <StatCard label="NEW MEMBERS" value={statistics.new_members ?? '—'} detail="Joined this month" />
          <StatCard label="EXPIRING SOON" value={statistics.members_expiring_soon ?? '—'} detail="Membership ends within 7 days" />
          <StatCard label="MONTH REVENUE" value={statistics.monthly_revenue == null ? '—' : formatINR(statistics.monthly_revenue)} detail="Completed payments" />
          <StatCard label="ALL-TIME REVENUE" value={statistics.total_revenue == null ? '—' : formatINR(statistics.total_revenue)} detail="Completed payments" />
        </div>
        <section className="portal-panel"><div className="portal-section-heading"><h2>Last seven days</h2><p>Daily attendance and completed-payment revenue</p></div><TrendChart data={dailyTrend} /></section>
      </PortalState>
    </AdminLayout>
  )
}

function formatINR(value) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value || 0)
}

function TrendChart({ data }) {
  const records = isRecordArray(data) ? data : []
  const maxAttendance = Math.max(...records.map((item) => Number(item.attendance) || 0), 1)
  const maxRevenue = Math.max(...records.map((item) => Number(item.revenue) || 0), 1)
  return <div className="portal-trend-chart">{records.map((item) => <div key={item.date} className="portal-trend-day"><div className="portal-trend-bars"><span title={`${item.attendance} attendance`} style={{ height: `${Math.max(((Number(item.attendance) || 0) / maxAttendance) * 100, 3)}%` }} /><span title={formatINR(item.revenue)} className="revenue-bar" style={{ height: `${Math.max(((Number(item.revenue) || 0) / maxRevenue) * 100, 3)}%` }} /></div><time>{new Date(`${item.date}T12:00:00`).toLocaleDateString('en', { weekday: 'short' })}</time><small>{item.attendance} visits</small><small>{formatINR(item.revenue)}</small></div>)}</div>
}

function AdminLayout({ title, description, children }) {
  const links = [
    ['/admin', 'Overview'],
    ['/admin/members', 'Members'],
    ['/admin/membership', 'Membership'],
    ['/admin/attendance', 'Attendance'],
    ['/admin/announcements', 'Announcements'],
  ]
  return <PortalShell eyebrow="GYM ADMINISTRATION" title={title} description={description}><nav className="portal-admin-nav">{links.map(([to, label]) => <Link key={to} to={to}>{label}</Link>)}</nav>{children}</PortalShell>
}

export function AdminMembersPage() {
  const { token } = useAuth()
  const [filters, setFilters] = useState({ search: '', status: '', membership: '', page: 1, per_page: 20 })
  const result = useLoad(
    () => adminApi.getMembers(token, filters),
    [token, JSON.stringify(filters)],
    (response) => isRecord(response)
      && isMemberRecords(response.members)
      && (response.pagination == null || hasScalarFields(response.pagination, ['total', 'pages'])),
  )
  const [selected, setSelected] = useState(null)
  const [notice, setNotice] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [busy, setBusy] = useState(false)
  async function openMember(id) {
    try {
      const response = await adminApi.getMember(token, id)
      if (
        !isRecord(response)
        || !hasScalarFields(response.member, ['id', 'name', 'email', 'phone', 'fitness_goal', 'date_of_birth', 'is_active'])
        || !isRecordArray(response.memberships)
        || !response.memberships.every((item) => hasScalarFields(item, ['id', 'plan_name', 'status', 'end_date']))
        || !isAttendanceRecords(response.attendance)
        || !isRecordArray(response.payments)
        || !response.payments.every((item) => hasScalarFields(item, ['id', 'paid_at', 'amount', 'status']))
      ) {
        throw new Error('FitZone returned incomplete member details. Please try again.')
      }
      setSelected(response)
    } catch (error) {
      setNotice(getErrorMessage(error))
    }
  }
  async function deactivate(id) {
    if (!window.confirm('Deactivate this member account? Their history will remain available.')) return
    try {
      await adminApi.deactivateMember(token, id)
      setNotice('Member deactivated.')
      result.reload()
    } catch (error) {
      setNotice(getErrorMessage(error))
    }
  }
  async function create(event) {
    event.preventDefault()
    const body = Object.fromEntries(new FormData(event.currentTarget))
    setBusy(true)
    try {
      await adminApi.createMember(token, body)
      setNotice('Member created successfully.')
      setShowCreate(false)
      result.reload()
    } catch (error) {
      setNotice(getErrorMessage(error))
    } finally {
      setBusy(false)
    }
  }
  async function saveMember(id, body) {
    try {
      await adminApi.updateMember(token, id, body)
      setNotice('Member updated successfully.')
      setSelected(null)
      result.reload()
      return ''
    } catch (error) {
      return getErrorMessage(error)
    }
  }
  const pagination = result.data?.pagination
  const memberRecords = isMemberRecords(result.data?.members) ? result.data.members : []
  return (
    <AdminLayout title="MEMBER MANAGEMENT" description="Find members and manage their accounts, memberships, and activity.">
      <section className="portal-panel">
        <div className="portal-section-heading"><div><h2>Members</h2><p>{pagination?.total ?? '—'} results</p></div><button className="portal-primary" onClick={() => setShowCreate((value) => !value)}><FiPlus /> ADD MEMBER</button></div>
        <Feedback message={notice} />
        <div className="portal-filter-row admin-filters"><label><FiSearch /> Search<input value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value, page: 1 })} placeholder="Name, email or phone" /></label><label>Status<select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value, page: 1 })}><option value="">All accounts</option><option value="active">Active</option><option value="inactive">Inactive</option></select></label><label>Membership<select value={filters.membership} onChange={(e) => setFilters({ ...filters, membership: e.target.value, page: 1 })}><option value="">Any membership</option><option value="active">Active</option><option value="expired">Expired</option><option value="cancelled">Cancelled</option><option value="none">None</option></select></label></div>
        {showCreate && <form className="portal-form portal-form-grid portal-create-form" onSubmit={create}><label>Name<input name="name" required /></label><label>Email<input name="email" type="email" required /></label><label>Phone<input name="phone" required /></label><label>Temporary password<input name="password" type="password" minLength="8" maxLength="128" required /></label><button className="portal-primary" disabled={busy}>{busy ? 'Creating…' : 'CREATE MEMBER'}</button></form>}
        <PortalState loading={result.loading} error={result.error} onRetry={result.reload} empty={!result.loading && !result.error && !memberRecords.length ? 'No members match these filters.' : null}>
          <div className="portal-table-wrap"><table><thead><tr><th>Member</th><th>Account</th><th>Membership</th><th>Contact</th><th>Actions</th></tr></thead><tbody>{memberRecords.map((member) => <tr key={member.id}><td><strong>{member.name}</strong><small>#{member.id}</small></td><td><span className={`portal-status ${member.is_active ? 'active' : 'inactive'}`}>{member.status}</span></td><td>{member.membership?.plan_name || '—'}<small>{member.membership_status}</small></td><td>{member.email}<small>{member.phone}</small></td><td><div className="portal-row-actions"><button type="button" onClick={() => openMember(member.id)}>View</button>{member.is_active && <button type="button" onClick={() => deactivate(member.id)}>Deactivate</button>}</div></td></tr>)}</tbody></table></div>
        </PortalState>
        {pagination?.pages > 1 && <div className="portal-pagination"><button disabled={filters.page <= 1} onClick={() => setFilters({ ...filters, page: filters.page - 1 })}>Previous</button><span>Page {filters.page} of {pagination.pages}</span><button disabled={filters.page >= pagination.pages} onClick={() => setFilters({ ...filters, page: filters.page + 1 })}>Next</button></div>}
      </section>
      {selected && <MemberDetail detail={selected} close={() => setSelected(null)} onSave={saveMember} />}
    </AdminLayout>
  )
}

function MemberDetail({ detail, close, onSave }) {
  const [editing, setEditing] = useState(false)
  const [saveError, setSaveError] = useState('')
  const [saving, setSaving] = useState(false)
  const member = isRecord(detail?.member) ? detail.member : null
  const memberships = isRecordArray(detail?.memberships) ? detail.memberships : []
  const attendance = isRecordArray(detail?.attendance) ? detail.attendance : []
  const payments = isRecordArray(detail?.payments) ? detail.payments : []
  if (!member) return null
  async function submit(event) {
    event.preventDefault()
    const values = Object.fromEntries(new FormData(event.currentTarget))
    values.is_active = values.is_active === 'true'
    values.fitness_goal = values.fitness_goal || null
    values.date_of_birth = values.date_of_birth || null
    setSaving(true)
    setSaveError('')
    const error = await onSave(member.id, values)
    setSaveError(error)
    setSaving(false)
    if (!error) setEditing(false)
  }
  return <div className="portal-modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && close()}><section className="portal-modal" role="dialog" aria-modal="true" aria-label="Member detail"><button className="portal-modal-close" onClick={close} aria-label="Close"><FiX /></button><p className="portal-eyebrow">MEMBER #{member.id}</p><h2>{member.name}</h2><p>{member.email} · {member.phone}</p><button className="portal-secondary" onClick={() => setEditing((value) => !value)}>{editing ? 'CANCEL EDIT' : 'EDIT PROFILE'}</button>{editing && <form className="portal-form portal-form-grid portal-edit-member-form" onSubmit={submit}><label>Name<input name="name" defaultValue={member.name} required /></label><label>Email<input name="email" type="email" defaultValue={member.email} required /></label><label>Phone<input name="phone" defaultValue={member.phone || ''} required /></label><label>Fitness goal<input name="fitness_goal" defaultValue={member.fitness_goal || ''} maxLength="80" /></label><label>Date of birth<input name="date_of_birth" type="date" defaultValue={member.date_of_birth || ''} /></label><label>Account status<select name="is_active" defaultValue={String(member.is_active)}><option value="true">Active</option><option value="false">Inactive</option></select></label><Feedback message={saveError} error /><button className="portal-primary" disabled={saving}>{saving ? 'Saving…' : 'SAVE MEMBER'}</button></form>}<h3>Membership</h3>{memberships.map((item) => <p key={item.id}>{item.plan_name} · {item.status} · through {item.end_date}</p>)}{!memberships.length && <EmptyHint>No membership history.</EmptyHint>}<h3>Recent attendance</h3>{attendance.slice(0, 10).map((item) => <p key={item.id}>{item.attendance_date} · {item.check_in_time} · {item.check_out_time || 'Not checked out'}</p>)}{!attendance.length && <EmptyHint>No attendance records.</EmptyHint>}<h3>Payment history</h3>{payments.slice(0, 10).map((item) => <p key={item.id}>{item.paid_at || 'Pending date'} · {formatINR(item.amount)} · {item.status}</p>)}{!payments.length && <EmptyHint>No payment records.</EmptyHint>}</section></div>
}

export function AdminMembershipPage() {
  const { token } = useAuth()
  const result = useLoad(
    () => adminApi.getMembershipPlans(token),
    [token],
    (response) => isRecord(response)
      && isPlanRecords(response.plans),
  )
  const members = useLoad(
    () => adminApi.getMembers(token, { status: 'active', per_page: 100 }),
    [token],
    (response) => isRecord(response) && isMemberRecords(response.members),
  )
  const [notice, setNotice] = useState('')
  const [editing, setEditing] = useState(null)
  const [assignPlanType, setAssignPlanType] = useState('')
  const [renewPlanType, setRenewPlanType] = useState('')
  const [busy, setBusy] = useState(false)
  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    const data = new FormData(event.currentTarget)
    const plan = {
      plan_type: String(data.get('plan_type')).toLowerCase().replace(/\s+/g, '_'),
      name: data.get('name'),
      monthly_price: Number(data.get('monthly_price')),
      durations_months: String(data.get('durations_months')).split(',').map((item) => Number(item.trim())),
    }
    try {
      if (editing) await adminApi.updateMembershipPlan(token, editing.id, plan)
      else await adminApi.createMembershipPlan(token, plan)
      setEditing(null)
      setNotice('Membership plan saved.')
      result.reload()
    } catch (error) {
      setNotice(getErrorMessage(error))
    } finally {
      setBusy(false)
    }
  }
  async function deactivate(id) {
    if (!window.confirm('Deactivate this plan? Existing memberships remain unchanged.')) return
    try {
      await adminApi.deactivateMembershipPlan(token, id)
      setNotice('Plan deactivated.')
      result.reload()
    } catch (error) { setNotice(getErrorMessage(error)) }
  }
  async function assign(event) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    try {
      await adminApi.assignMembership(token, {
        user_id: Number(data.get('user_id')),
        plan_type: data.get('plan_type'),
        duration_months: Number(data.get('duration_months')),
      })
      setNotice('Membership assigned.')
      event.currentTarget.reset()
    } catch (error) { setNotice(getErrorMessage(error)) }
  }
  async function renew(event) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    try {
      await adminApi.renewMembership(token, Number(data.get('membership_id')), {
        plan_type: data.get('plan_type'),
        duration_months: Number(data.get('duration_months')),
      })
      setNotice('Membership renewed.')
    } catch (error) { setNotice(getErrorMessage(error)) }
  }
  const planRecords = isPlanRecords(result.data?.plans) ? result.data.plans : []
  const memberRecords = isMemberRecords(members.data?.members) ? members.data.members : []
  const activePlans = planRecords.filter((plan) => plan.is_active)
  const selectedAssignPlan = activePlans.find((plan) => plan.plan_type === assignPlanType) || activePlans[0]
  const selectedRenewPlan = activePlans.find((plan) => plan.plan_type === renewPlanType) || activePlans[0]
  return (
    <AdminLayout title="MEMBERSHIP MANAGEMENT" description="Configure plan pricing and assign or renew a member's plan.">
      <Feedback message={notice} />
      <section className="portal-panel"><div className="portal-section-heading"><h2>{editing ? 'Update plan' : 'Create plan'}</h2></div><form key={editing?.id || 'new'} className="portal-form portal-form-grid" onSubmit={submit}><label>Plan identifier<input name="plan_type" defaultValue={editing?.plan_type || ''} required pattern="[a-z][a-z0-9_-]{1,39}" /></label><label>Display name<input name="name" defaultValue={editing?.name || ''} required /></label><label>Monthly price (₹)<input name="monthly_price" type="number" min="0" step="0.01" defaultValue={editing?.monthly_price || ''} required /></label><label>Durations (months, comma-separated)<input name="durations_months" defaultValue={editing?.durations_months?.join(', ') || '1, 3, 6'} required /></label><button className="portal-primary" disabled={busy}>{editing ? 'SAVE PLAN' : 'CREATE PLAN'} <FiCheck /></button>{editing && <button className="portal-secondary" type="button" onClick={() => setEditing(null)}>CANCEL</button>}</form></section>
      <section className="portal-panel"><div className="portal-section-heading"><h2>Plans</h2></div><PortalState loading={result.loading} error={result.error} onRetry={result.reload} empty={!result.loading && !result.error && !planRecords.length ? 'No membership plans are configured.' : null}><div className="portal-table-wrap"><table><thead><tr><th>Plan</th><th>Monthly</th><th>Durations</th><th>Status</th><th>Actions</th></tr></thead><tbody>{planRecords.map((plan) => <tr key={plan.id}><td>{plan.name}<small>{plan.plan_type}</small></td><td>{formatINR(plan.monthly_price)}</td><td>{plan.durations_months.join(', ')} months</td><td>{plan.is_active ? 'Active' : 'Inactive'}</td><td><div className="portal-row-actions"><button onClick={() => setEditing(plan)}>Edit</button>{plan.is_active && <button onClick={() => deactivate(plan.id)}>Deactivate</button>}</div></td></tr>)}</tbody></table></div></PortalState></section>
      <div className="portal-dashboard-grid"><section className="portal-panel"><h2>Assign membership</h2><PortalState loading={members.loading} error={members.error} onRetry={members.reload} empty={!members.loading && !members.error && !memberRecords.length ? 'No active members are available to assign.' : null}><form className="portal-form" onSubmit={assign}><label>Member<select name="user_id" required><option value="">Select member</option>{memberRecords.map((member) => <option key={member.id} value={member.id}>{member.name} · #{member.id}</option>)}</select></label><label>Plan<select name="plan_type" required value={selectedAssignPlan?.plan_type || ''} onChange={(event) => setAssignPlanType(event.target.value)}>{activePlans.map((plan) => <option key={plan.id} value={plan.plan_type}>{plan.name}</option>)}</select></label><label>Duration<select name="duration_months" required>{(selectedAssignPlan?.durations_months || []).map((item) => <option value={item} key={item}>{item} month(s)</option>)}</select></label><button className="portal-primary" disabled={!activePlans.length}>ASSIGN MEMBERSHIP</button></form></PortalState></section><section className="portal-panel"><h2>Renew membership</h2><form className="portal-form" onSubmit={renew}><label>Membership ID<input name="membership_id" type="number" min="1" required /></label><label>Plan<select name="plan_type" value={selectedRenewPlan?.plan_type || ''} onChange={(event) => setRenewPlanType(event.target.value)} required>{activePlans.map((plan) => <option key={plan.id} value={plan.plan_type}>{plan.name}</option>)}</select></label><label>Duration<select name="duration_months" required>{(selectedRenewPlan?.durations_months || []).map((item) => <option value={item} key={item}>{item} month(s)</option>)}</select></label><button className="portal-primary" disabled={!activePlans.length}>RENEW MEMBERSHIP</button></form></section></div>
    </AdminLayout>
  )
}

export function AdminAttendancePage() {
  const { token } = useAuth()
  const today = useLoad(
    () => adminApi.getTodayAttendance(token),
    [token],
    (response) => isRecord(response) && isAttendanceRecords(response.attendance),
  )
  const stats = useLoad(
    () => adminApi.getAttendanceStatistics(token),
    [token],
    (response) => isRecord(response)
      && hasScalarFields(response.statistics, ['today_attendance', 'today_unique_members', 'current_month_attendance', 'total_attendance_days', 'longest_member_streak']),
  )
  const [referenceDate] = useState(() => new Date())
  const [month, setMonth] = useState(String(referenceDate.getMonth() + 1))
  const [year, setYear] = useState(String(referenceDate.getFullYear()))
  const history = useLoad(
    () => adminApi.getAdminAttendance(token, { month, year }),
    [token, month, year],
    (response) => isRecord(response) && isAttendanceRecords(response.attendance),
  )
  const [memberId, setMemberId] = useState('')
  const memberAttendance = useLoad(
    () => memberId ? adminApi.getMemberAttendance(token, memberId) : Promise.resolve({ attendance: [] }),
    [token, memberId],
    (response) => isRecord(response) && isAttendanceRecords(response.attendance),
  )
  const stat = isRecord(stats.data?.statistics) ? stats.data.statistics : {}
  const todayRecords = isAttendanceRecords(today.data?.attendance) ? today.data.attendance : []
  const historyRecords = isAttendanceRecords(history.data?.attendance) ? history.data.attendance : []
  const memberAttendanceRecords = isAttendanceRecords(memberAttendance.data?.attendance)
    ? memberAttendance.data.attendance
    : []
  return <AdminLayout title="ATTENDANCE MANAGEMENT" description="Review gym attendance by day, month, or member.">
    <PortalState loading={stats.loading} error={stats.error} onRetry={stats.reload}><div className="portal-stat-grid"><StatCard label="TODAY" value={stat.today_attendance ?? '—'} detail={`${stat.today_unique_members ?? '—'} unique members`} /><StatCard label="THIS MONTH" value={stat.current_month_attendance ?? '—'} detail="Recorded visits" /><StatCard label="ALL-TIME" value={stat.total_attendance_days ?? '—'} detail="Recorded visits" /><StatCard label="LONGEST MEMBER STREAK" value={stat.longest_member_streak ?? '—'} detail="Consecutive days" /></div></PortalState>
    <section className="portal-panel"><div className="portal-section-heading"><h2>Today's attendance</h2></div><PortalState loading={today.loading} error={today.error} onRetry={today.reload} empty={!today.loading && !today.error && !todayRecords.length ? 'No visits recorded today.' : null}><AttendanceTable records={todayRecords} /></PortalState></section>
    <section className="portal-panel"><div className="portal-section-heading"><h2>Monthly attendance</h2><div className="portal-filter-row"><label>Month<select value={month} onChange={(e) => setMonth(e.target.value)}>{Array.from({ length: 12 }, (_, i) => <option key={i} value={i + 1}>{new Date(2000, i).toLocaleString('en', { month: 'long' })}</option>)}</select></label><label>Year<input type="number" value={year} onChange={(e) => setYear(e.target.value)} /></label></div></div><PortalState loading={history.loading} error={history.error} onRetry={history.reload} empty={!history.loading && !history.error && !historyRecords.length ? 'No attendance in this month.' : null}><AttendanceTable records={historyRecords} /></PortalState></section>
    <section className="portal-panel"><div className="portal-section-heading"><h2>Member attendance</h2><label>Member ID<input type="number" min="1" value={memberId} onChange={(e) => setMemberId(e.target.value)} placeholder="Enter a member ID" /></label></div>{memberId && <PortalState loading={memberAttendance.loading} error={memberAttendance.error} onRetry={memberAttendance.reload} empty={!memberAttendance.loading && !memberAttendance.error && !memberAttendanceRecords.length ? 'No attendance records for this member.' : null}><AttendanceTable records={memberAttendanceRecords} /></PortalState>}</section>
  </AdminLayout>
}

export function AdminAnnouncementsPage() {
  const { token } = useAuth()
  const result = useLoad(
    () => adminApi.getAnnouncements(token),
    [token],
    (response) => isRecord(response) && isAnnouncementRecords(response.announcements),
  )
  const announcementRecords = isAnnouncementRecords(result.data?.announcements) ? result.data.announcements : []
  const [editing, setEditing] = useState(null)
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  async function submit(event) {
    event.preventDefault()
    const values = Object.fromEntries(new FormData(event.currentTarget))
    setBusy(true)
    try {
      if (editing) await adminApi.updateAnnouncement(token, editing.id, values)
      else await adminApi.createAnnouncement(token, values)
      setEditing(null)
      setMessage('Announcement saved.')
      result.reload()
    } catch (error) { setMessage(getErrorMessage(error)) } finally { setBusy(false) }
  }
  async function remove(id) {
    if (!window.confirm('Delete this announcement?')) return
    try {
      await adminApi.deleteAnnouncement(token, id)
      setMessage('Announcement deleted.')
      result.reload()
    } catch (error) { setMessage(getErrorMessage(error)) }
  }
  return <AdminLayout title="ANNOUNCEMENTS" description="Publish updates for members in the member dashboard.">
    <section className="portal-panel"><div className="portal-section-heading"><h2>{editing ? 'Edit announcement' : 'Create announcement'}</h2></div><Feedback message={message} /><form key={editing?.id || 'new'} className="portal-form" onSubmit={submit}><label>Title<input name="title" defaultValue={editing?.title || ''} required maxLength="160" /></label><label>Message<textarea name="body" defaultValue={editing?.body || ''} required maxLength="10000" rows="4" /></label><button className="portal-primary" disabled={busy}>{busy ? 'Saving…' : editing ? 'UPDATE ANNOUNCEMENT' : 'PUBLISH ANNOUNCEMENT'} <FiArrowRight /></button>{editing && <button className="portal-secondary" type="button" onClick={() => setEditing(null)}>CANCEL</button>}</form></section>
    <section className="portal-panel"><div className="portal-section-heading"><h2>Published and archived</h2></div><PortalState loading={result.loading} error={result.error} onRetry={result.reload} empty={!result.loading && !result.error && !announcementRecords.length ? 'No announcements yet.' : null}><div className="portal-record-list">{announcementRecords.map((item) => <article key={item.id}><div><strong>{item.title}</strong><span>{item.body}</span><small>{item.is_active ? 'Visible to members' : 'Inactive'} · {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'Date unavailable'}</small></div><div className="portal-row-actions"><button onClick={() => setEditing(item)}>Edit</button><button onClick={() => remove(item.id)}><FiTrash2 /> Delete</button></div></article>)}</div></PortalState></section>
  </AdminLayout>
}

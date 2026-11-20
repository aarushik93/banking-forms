import { useEffect, useState } from 'react'

const STAGES = [
  'Submitting your application…',
  'Verifying your identity with our verification partner…',
  'Checking your funding account…',
  'Finalising your application…',
]

export function ProcessingScreen() {
  const [stage, setStage] = useState(0)

  useEffect(() => {
    const timer = setInterval(
      () => setStage((s) => Math.min(s + 1, STAGES.length - 1)),
      1700,
    )
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="processing" role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      <h2>{STAGES[stage]}</h2>
      <p className="processing-note">
        This usually takes a few seconds. Please don't close this page.
      </p>
      <ol className="processing-stages">
        {STAGES.map((label, index) => (
          <li
            key={label}
            className={
              index < stage
                ? 'stage--done'
                : index === stage
                  ? 'stage--active'
                  : 'stage--todo'
            }
          >
            {index < stage ? '✓ ' : ''}
            {label.replace('…', '')}
          </li>
        ))}
      </ol>
    </div>
  )
}

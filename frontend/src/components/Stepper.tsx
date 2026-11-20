interface StepperProps {
  steps: readonly string[]
  current: number
}

export function Stepper({ steps, current }: StepperProps) {
  return (
    <ol className="stepper" aria-label="Application progress">
      {steps.map((step, index) => {
        const state = index < current ? 'done' : index === current ? 'active' : 'todo'
        return (
          <li
            key={step}
            className={`stepper-item stepper-item--${state}`}
            aria-current={index === current ? 'step' : undefined}
          >
            <span className="stepper-index">{index < current ? '✓' : index + 1}</span>
            <span className="stepper-label">{step}</span>
          </li>
        )
      })}
    </ol>
  )
}

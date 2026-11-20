import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { PersonalStep } from '../steps/PersonalStep'

describe('PersonalStep', () => {
  it('shows validation errors and does not advance when empty', async () => {
    const onNext = vi.fn()
    render(<PersonalStep onNext={onNext} saving={false} />)

    await userEvent.click(screen.getByRole('button', { name: /continue/i }))

    const alerts = await screen.findAllByRole('alert')
    expect(alerts.length).toBeGreaterThan(0)
    expect(onNext).not.toHaveBeenCalled()
  })

  it('submits valid values', async () => {
    const onNext = vi.fn()
    render(<PersonalStep onNext={onNext} saving={false} />)

    await userEvent.selectOptions(screen.getByLabelText(/title/i), 'Ms')
    await userEvent.type(screen.getByLabelText(/first name/i), 'Jane')
    await userEvent.type(screen.getByLabelText(/last name/i), 'Smith')
    await userEvent.type(screen.getByLabelText(/date of birth/i), '1990-04-12')
    await userEvent.type(screen.getByLabelText(/email/i), 'jane@example.com')
    await userEvent.type(screen.getByLabelText(/phone/i), '+44 7700 900123')
    await userEvent.click(screen.getByRole('button', { name: /continue/i }))

    expect(onNext).toHaveBeenCalledWith(
      expect.objectContaining({ first_name: 'Jane', last_name: 'Smith' }),
      expect.anything(),
    )
  })
})

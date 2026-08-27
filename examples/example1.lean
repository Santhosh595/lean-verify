"""
Example Lean file demonstrating a simple theorem.

This file can be used for testing the lean-verify tool when the actual
Lean toolchain is available.
"""

theorem simple_example : 1 + 1 = 2 :=
  rfl

/-- A comment in the Lean file --/
def constant_example : Nat := 42

/-- Another theorem example --/
theorem double : ∀ n : Nat, n + n = n * 2 :=
  intro n
  induction n
  case zero => rfl
  case succ n_ih =>
    rw [add_succ, mul_succ]
    exact n_ih

# Margin Harbor

Margin Harbor is a recurring collateral health monitor. Position terms and two independently hosted market observations are refetched for each increasing epoch. Validators verify the exact health number, state, signals and all source digests.

Stale epochs cannot overwrite current state. Healthy positions may be acknowledged as recovered; actionable positions are final. This is an advisory alert primitive, not a liquidation engine or price feed. Run `python -m pytest -q` and `genvm-lint contract/margin_harbor.py`.

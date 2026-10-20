# Kiro Savdo Bot — callback fix

## Fix in this update
- Fixed the JSON preparation source-selection callback (`GitHub`, `Google`, `Builder ID`). It now receives the `Database` dependency required to read the admin-defined prompt. Previously, clicking a source could raise a missing-argument error, leaving the flow stuck.

## Before deploying
1. Back up the existing SQLite database and environment variables.
2. Replace the application code with the files in this archive (the archive is flat; no parent folder).
3. Keep your existing database and hosting environment variables; do not upload `.env` to GitHub.
4. Restart the bot and test `/start` → `📝 JSON tayyorlash` → `🐙 GitHub`.

Checks performed: Python syntax compilation and ZIP integrity. A live Telegram integration test was not possible here. This update fixes the identified callback bug but does not claim every unrelated bot feature is fully tested.

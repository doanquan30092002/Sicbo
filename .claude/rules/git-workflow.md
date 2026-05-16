# Git Workflow - Sicbo Project

## Branch Strategy

- `main` — production (Railway + Vercel deploy tự động)
- `develop` — integration branch
- `feature/<name>` — feature branches (từ develop)
- `fix/<name>` — bug fix branches
- `phase/<n>` — implementation phase branches (phase/1-foundation, phase/2-auth...)

## Commit Convention

Format: `<type>(<scope>): <message>`

Types:
- `feat` — tính năng mới
- `fix` — sửa bug
- `refactor` — refactor không đổi behavior
- `test` — thêm/sửa tests
- `chore` — cấu hình, dependencies
- `docs` — documentation

Examples:
```
feat(betting): add PlaceBet use case with atomic balance deduction
fix(xsmb): count duplicate numbers in all_last2 for Lô payout
feat(bot): add /bet ConversationHandler with game selection
```

## Khi nào commit

- Sau mỗi use case hoàn thành và có tests
- Sau mỗi router/handler hoàn thành
- Sau mỗi phase hoàn thành

## Khi nào KHÔNG commit

- Khi có test failing
- Khi có hardcoded credentials
- Khi implementation chưa hoàn chỉnh

# AiriLab Skill 更新日志


## [1.4.2] 2026-04-01 - Async Submit Response Rule

### Changed
- Updated submit-success response message in `core/api.py`: after job submission, explicitly tells user this round ends and result will be notified asynchronously by background worker.
- Updated `SKILL.md` async-task constraint: on successful submit, the agent must end current round and state that background completion notification will follow.

## [1.4.1] 2026-04-01 - Polling Terminal-State Rule Update

### Changed
- Updated `scheduler/worker.py` polling behavior: only `status=processing` is treated as in-progress.
- For any non-`processing` status, worker now treats the job as ended and immediately calls `fetch.py` to retrieve generation results.

### Fixed
- Removed retryable-status branch to align runtime behavior with the new terminal-state rule.
- On fetch failure after terminal state, task is marked failed with terminal status + fetch error context.

## [1.4.0] 2026-04-01 - Post-install Bootstrap and Legacy Cleanup

### Added
- Added a new `scripts/post-install.sh` bootstrap script to initialize runtime directories, install dependencies, run health checks, configure autostart, and ensure worker startup.
- Added `post-install.sh` command to SKILL runtime commands.

### Changed
- Refined `.gitignore` to ignore local config/runtime artifacts (`config/`, `scheduler/`, `*.db`, `*.log`, `*.pid`).

### Removed
- Removed obsolete scripts: `scripts/install-systemd-service.sh` and legacy `scripts/post-install.sh` implementation.
- Removed outdated setup documents tied to legacy flow: `AUTOSTART_SETUP.md` and `P1_FIXES.md`.

### Notes
- New post-install flow prioritizes user-level systemd autostart and falls back to cron `@reboot` when systemd user services are unavailable.
## [1.3.0] 2026-04-01 - Runtime Hardening and Login OTP Rules

### Changed
- Enforced strict OTP send success rule in `core/auth.py`: only `status == 200` and `message == "Otp sent"` is treated as success.
- For OTP send failures, backend `message` is now returned directly to the agent.
- Added strong agent execution constraints in `SKILL.md` to prevent pushing executable commands to users.

### Added
- Added shared runtime path resolver `core/paths.py` with `AIRILAB_HOME` override support.
- Added `health` action in `core/config.py` to report token/project readiness, worker state, and job counters.
- Added one-shot runtime diagnostics script `scripts/health.sh`.

### Fixed
- Unified runtime persistence path usage across `core/config.py`, `scripts/check_status.py`, `scripts/fetch.py`, and `scheduler/worker.py`.
- Hardened `scheduler/worker.py` with single-instance PID lock and startup self-check.
- Added retry classification for transient status/fetch failures before final task failure.
- Updated `scripts/start-worker.sh` to honor `AIRILAB_HOME` and run preflight health checks.

### Notes
- This release focuses on making background-task reliability and login UX deterministic under real runtime conditions.
# AiriLab Skill 鏇存柊鏃ュ織

## [1.2.0] 2026-04-01 - Worker Reliability and Runtime Fixes

### Fixed
- Standardized task status output in `scripts/check_status.py` to machine-readable `status:<value>`.
- Removed hardcoded `projectId/teamId` in status checking and switched to config-based project context.
- Updated `scheduler/worker.py` to call child scripts with `sys.executable` instead of hardcoded `python3`.
- Fixed result handling in worker: treat `success=false` from `fetch.py` as task failure.
- Removed duplicate unreachable `workflow_id == 13` branch in `core/api.py`.
- Added import fallbacks in core modules to support direct script execution.

### Added
- Added `requirements.txt` with `requests>=2.31.0`.

### Notes
- This release focuses on reducing false pending/unknown states and improving cross-environment runtime stability.


## [1.1.0] 2026-03-31 - P0 闂淇

### 鉁?宸蹭慨澶?

#### 1. 鏂板 `scripts/fetch.py`
- 鑾峰彇宸插畬鎴愪换鍔＄殑杈撳嚭缁撴灉
- 鏀寔 JSON 鍜屾枃鏈袱绉嶈緭鍑烘牸寮?
- 杩斿洖鎵€鏈夌敓鎴愬浘鐗囩殑 URL 鍒楄〃
- 鑷姩璇嗗埆宸ヤ綔娴佺被鍨嬶紙MJ/Upscale/Atmosphere锛?

**浣跨敤绀轰緥**:
```bash
# 鏂囨湰杈撳嚭
python3 scripts/fetch.py --job-id <job_id>

# JSON 杈撳嚭锛堜緵绋嬪簭璋冪敤锛?
python3 scripts/fetch.py --job-id <job_id> --format json
```

#### 2. 瀹炵幇鐢ㄦ埛閫氱煡鏈哄埗 (`scheduler/worker.py`)
- 浣跨敤 OpenClaw completions 鐩綍鍙戦€佹秷鎭?
- 鏀寔澶氬浘鐗?Markdown 鏍煎紡灞曠ず
- 鍖呭惈 Job ID銆佸伐鍏风被鍨嬨€佸浘鐗囨暟閲忕瓑淇℃伅
- 澶辫触浠诲姟涔熶細鍙戦€侀敊璇€氱煡

**閫氱煡鏍煎紡**:
```markdown
鉁?**浠诲姟瀹屾垚锛?*

馃搵 **Job ID**: `xxx`
馃帹 **宸ュ叿**: MJ

馃柤锔? **鐢熸垚缁撴灉**:

![鍥剧墖 1](url1)
![鍥剧墖 2](url2)
...

_鍏?4 寮犲浘鐗嘷
```

#### 3. 鏀硅繘 `process_job()` 鍑芥暟
- 姝ｇ‘瑙ｆ瀽 `fetch.py` 鐨?JSON 杈撳嚭
- 浼犻€掓墍鏈夊浘鐗?URL 缁欓€氱煡鍑芥暟
- 娣诲姞宸ュ叿绫诲瀷鍒伴€氱煡娑堟伅
- 鏀硅繘閿欒澶勭悊閫昏緫

### 馃搧 鏂囦欢鍙樻洿

| 鏂囦欢 | 鍙樻洿绫诲瀷 | 璇存槑 |
|------|---------|------|
| `scripts/fetch.py` | 鏂板 | 浠诲姟缁撴灉鑾峰彇鑴氭湰 |
| `scheduler/worker.py` | 淇敼 | 瀹炵幇閫氱煡鏈哄埗 |
| `CHANGELOG.md` | 鏂板 | 鏇存柊鏃ュ織 |

### 馃И 娴嬭瘯寤鸿

1. **娴嬭瘯 fetch.py**:
   ```bash
   python3 ~/.openclaw/skills/airilab/scripts/fetch.py --job-id <existing_job_id>
   ```

2. **娴嬭瘯瀹屾暣娴佺▼**:
   - 鎻愪氦涓€涓浘鍍忕敓鎴愪换鍔?
   - 鍚姩 worker: `python3 scheduler/worker.py`
   - 妫€鏌?completions 鐩綍鏄惁鐢熸垚閫氱煡鏂囦欢

### 鈿狅笍 娉ㄦ剰浜嬮」

- 纭繚 Token 鏈夋晥锛堟湁鏁堟湡 7 澶╋級
- 纭繚椤圭洰閰嶇疆姝ｇ‘
- worker 闇€瑕佹寔缁繍琛屾墠鑳借疆璇换鍔?

---

## [1.0.0] 2026-03-31 - 鍒濆鏁村悎鐗堟湰

鏁村悎 airi-auth, airi-upload, airi-project, api-list 鍥涗釜鎶€鑳姐€?



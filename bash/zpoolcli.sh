#!/bin/bash
# zpoolcli.sh — PAT-first where supported; JWT where required; SSH for ZFS.
# Command structure:
#   - billing balance|ledger       (PAT/JWT; claim codes and add credits on dashboard)
#   - job, pat, sshkey, zpool      (PAT or JWT as appropriate; create PATs on dashboard)
#   - zfs                          (SSH)

set -eo pipefail

# -----------------------------
# Config & defaults
# -----------------------------
DOTFILE="${HOME}/.config/zpools.io/zpoolrc"
ZPOOL_API_URL="${ZPOOL_API_URL:-}"
SSH_HOST="${SSH_HOST:-ssh.zpools.io}"
SSH_PRIVKEY_FILE="${SSH_PRIVKEY_FILE:-}"
ZPOOL_USER="${ZPOOL_USER:-}"
ZPOOL_PASSWORD="${ZPOOL_PASSWORD:-}"
ZPOOLPAT="${ZPOOLPAT:-}"   # optional; may come from env or rcfile
MAX_AGE_SECONDS="${MAX_AGE_SECONDS:-3600}"

emit_json() {
  if command -v jq >/dev/null 2>&1; then
    if [[ -t 1 ]]; then
      jq -CrS . <<<"$1" || echo "$1"
    else
      jq -cS . <<<"$1" || echo "$1"
    fi
  else
    echo "$1"
  fi
}

die() {
  echo "Error: $*" >&2
  exit 1
}

note() {
  echo "$*" >&2
}

is_tty() {
  [[ -t 0 ]]
}

# -----------------------------
# Early option parsing (flags only)
# -----------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --rcfile)
      [[ -n "${2:-}" ]] || die "--rcfile requires a file path"
      [[ -f "$2" ]] || die "rcfile '$2' does not exist"
      DOTFILE="$2"
      shift 2
      ;;
    --username)
      [[ -n "${2:-}" ]] || die "--username requires a value"
      ZPOOL_USER="$2"
      shift 2
      ;;
    --password)
      [[ -n "${2:-}" ]] || die "--password requires a value"
      ZPOOL_PASSWORD="$2"
      shift 2
      ;;
    --help|-h)
      # Defer to usage() so it can show rcfile-provided domains if set
      break
      ;;
    *)
      break
      ;;
  esac
done

# -----------------------------
# Load rcfile (no passwords)
# -----------------------------
if [[ -f "$DOTFILE" ]]; then
  eval "$(
    (
      # shellcheck source=/dev/null
      source "$DOTFILE"
      for var in ZPOOL_API_URL BZFS_BIN LOCAL_POOL REMOTE_POOL SSH_HOST SSH_PRIVKEY_FILE ZPOOL_TOKEN_CACHE_DIR ZPOOL_USER ZPOOLPAT; do
        val="${!var:-}"
        if [[ -n "$val" ]]; then
          printf 'if [[ -z "${%s:-}" ]]; then export %s=%q; fi\n' "$var" "$var" "$val"
        fi
      done
    )
  )"
fi

# -----------------------------
# Usage
# -----------------------------
usage() {
  echo
  echo "API: ${ZPOOL_API_URL:-https://api.dev.zpools.io}    SSH: ${SSH_HOST:-ssh.dev.zpools.io}"
  echo
  echo "Commands (left column shows auth type; PAT-capable lines include required PAT scope):"
  echo
  echo "  === Billing ==="
  echo "  [JWTPAT]  $0 billing balance                           (scope: billing)"
  echo "  [JWTPAT]  $0 billing ledger [since YYYY-MM-DD] [until YYYY-MM-DD] [limit (default 500)]"
  echo "  (Redeem codes and add credits on the dashboard.)"
  echo
  echo "  === Personal Access Tokens ==="
  echo "  [JWTPAT]  $0 pat list                                  (scope: pat)"
  echo "  [JWTPAT]  $0 pat revoke <key_id>"
  echo "  (Create PATs on the dashboard.)"
  echo
  echo "  === SSH Keys ==="
  echo "  [JWTPAT]  $0 sshkey list                               (scope: sshkey)"
  echo "  [JWT]     $0 sshkey add <public_key>"
  echo "  [JWT]     $0 sshkey delete <pubkey_id>"
  echo
  echo "  === Jobs ==="
  echo "  [JWTPAT]  $0 job list                                  (scope: job)"
  echo "  [JWTPAT]  $0 job show <job_id>                         (scope: job)"
  echo "  [JWTPAT]  $0 job history <job_id>                      (scope: job)"
  echo
  echo "  === Zpools ==="
  echo "  [JWTPAT]  $0 zpool list                                (scope: zpool)"
  echo "  [JWT]     $0 zpool create <new_size_in_gib> <volume_type>"
  echo "  [JWT]     $0 zpool delete <zpool_id>"
  echo "  [JWTPAT]  $0 zpool scrub <zpool_id>                    (scope: zpool)"
  echo "  [JWTPAT]  $0 zpool modify <zpool_id> <volume_type>     (scope: zpool)"
  echo "            (volume_type: gp3|sc1)"
  echo
  echo "  === Misc ==="
  echo "  [JWTPAT]  $0 hello                                     (scope: none)"
  echo
  echo "  === ZFS over SSH ==="
  echo "  [SSH]     $0 zfs list <dataset> [flags...]"
  echo "  [SSH]     $0 zfs destroy <dataset> [flags...]"
  echo "  [SSH]     $0 zfs snapshot <dataset@snapshot>"
  echo "  [SSH]     $0 zfs recv [flags...] <zpool/dataset>        (stdin: zfs send ...)"
  echo "  [SSH]     $0 zfs ssh [remote command...]"
  echo "  [SSH]     $0 zfs bzfs    (requires BZFS_BIN, LOCAL_POOL, REMOTE_POOL)"
  echo
  echo "Options:"
  echo "  --rcfile <path>       Load config variables from an alternate rcfile (default: ${DOTFILE})"
  echo "  --username <value>    Username for JWT auth when needed (overrides \$ZPOOL_USER just for this run)"
  echo "  --password <value>    Password for JWT auth when needed (non-interactive/CI)"
  echo
  echo "Notes:"
  echo "  • ZPOOLPAT is used automatically for PAT-capable endpoints ([JWTPAT]). If a PAT is rejected (401/403), the command fails and does not fall back to JWT."
  echo "  • No password is ever read from the rcfile. Username *may* be read (ZPOOL_USER)."
  echo "  • For endpoints requiring JWT, if creds are missing and stdin is not a TTY, the command errors out."
  echo "  • Required config if missing: set in ${DOTFILE} or export the env var:"
  echo "      ZPOOL_API_URL      (e.g., https://api.dev.zpools.io/v1)"
  echo "      SSH_HOST           (e.g., ssh.dev.zpools.io)"
  echo "      SSH_PRIVKEY_FILE   (path to your private key)"
  echo "      ZPOOL_USER         (username; can also pass via --username)"
  echo
  exit 1
}

# -----------------------------
# HTTP helpers
# -----------------------------
HTTP_STATUS=""
RESPONSE=""

do_http() {
  # do_http METHOD PATH AUTH_HEADER [JSON_BODY]
  local method="$1"
  local path="$2"
  local auth_header="$3"
  local data="${4:-}"
  local url="${ZPOOL_API_URL}${path}"

  [[ -n "$ZPOOL_API_URL" ]] || die "ZPOOL_API_URL is required. Set it in ${DOTFILE} or export ZPOOL_API_URL"

  local tmp
  tmp="$(mktemp)"
  if [[ -n "$data" ]]; then
    HTTP_STATUS="$(
      curl -s -o "$tmp" -w '%{http_code}' -X "$method" "$url" \
        -H "$auth_header" -H "Content-Type: application/json" \
        -d "$data"
    )"
  else
    HTTP_STATUS="$(
      curl -s -o "$tmp" -w '%{http_code}' -X "$method" "$url" \
        -H "$auth_header"
    )"
  fi
  RESPONSE="$(cat "$tmp")"
  rm -f "$tmp"
}

# -----------------------------
# Auth helpers (JWT only when needed)
# -----------------------------
# When ZPOOL_TOKEN_CACHE_DIR is empty (e.g. "" or ""), caching is disabled; token_file_for_user returns empty.
token_file_for_user() {
  local user="$1"
  local domain
  domain=$(echo "$2" | sed -E 's#^https?://##; s#/.*##')
  if [[ -z "$user" ]]; then
    die "Username required for token cache path"
  fi
  if [[ "$user" == *" "* ]]; then
    die "Username must not contain spaces"
  fi
  local base="${ZPOOL_TOKEN_CACHE_DIR:-}"
  if [[ -z "$base" ]]; then
    echo ""
    return
  fi
  mkdir -p "$base"
  echo "${base}/zpool_token_${domain}_${user}"
}

prompt_username_if_needed() {
  if [[ -z "$ZPOOL_USER" ]]; then
    if is_tty; then
      read -r -p "Username: " ZPOOL_USER
    else
      die "Username required but not provided. Use --username or set ZPOOL_USER in ${DOTFILE}"
    fi
  fi
}

prompt_password_if_needed() {
  if [[ -n "$ZPOOL_PASSWORD" ]]; then
    PASSWORD="$ZPOOL_PASSWORD"
  else
    if is_tty; then
      read -r -s -p "zpools.io Password: " PASSWORD
      echo >&2
    else
      die "Password required but not provided. Use --password or run interactively"
    fi
  fi
}

login_and_cache_tokens() {
  local user="$1"
  local token_file; token_file="$(token_file_for_user "$user" "${ZPOOL_API_URL}")"

  prompt_password_if_needed

  note "Authenticating to refresh token..."
  local auth_body
  auth_body=$(jq -n --arg u "$user" --arg p "$PASSWORD" '{username: $u, password: $p}')
  local tmp; tmp="$(mktemp)"
  local code
  code="$(
    curl -s -o "$tmp" -w '%{http_code}' -X POST "${ZPOOL_API_URL}/login" \
      -H "Content-Type: application/json" \
      -d "$auth_body"
  )"
  local body; body="$(cat "$tmp")"; rm -f "$tmp"

  if [[ "$code" != "200" && "$code" != "201" ]]; then
    emit_json "$body"
    die "Authentication failed with HTTP $code"
  fi

  local access id expires
  access="$(jq -r '.detail.access_token // empty' <<<"$body")"
  id="$(jq -r '.detail.id_token // empty' <<<"$body")"
  expires="$(jq -r '.detail.expires_in // empty' <<<"$body")"

  [[ -n "$access" && -n "$id" && -n "$expires" ]] || {
    emit_json "$body"
    die "Login response missing required fields"
  }

  local expires_at
  expires_at=$(( $(date +%s) + expires ))

  if [[ -n "$token_file" ]]; then
    umask 0177
    printf '{"access_token":"%s","id_token":"%s","expires_at":%s}\n' "$access" "$id" "$expires_at" >"$token_file"
    chmod 0600 "$token_file" || true
  else
    JWT_ACCESS_TOKEN="$access"
    JWT_ID_TOKEN="$id"
  fi
  note "Tokens refreshed."
}

ensure_jwt_fresh() {
  prompt_username_if_needed
  local token_file; token_file="$(token_file_for_user "$ZPOOL_USER" "${ZPOOL_API_URL}")"

  if [[ -z "$token_file" ]]; then
    login_and_cache_tokens "$ZPOOL_USER"
  elif [[ -f "$token_file" ]]; then
    local file_json expires_at
    file_json="$(cat "$token_file")"
    expires_at="$(jq -r '.expires_at // 0' <<<"$file_json")"
    if (( $(date +%s) >= expires_at )); then
      login_and_cache_tokens "$ZPOOL_USER"
    fi
  else
    login_and_cache_tokens "$ZPOOL_USER"
  fi
}

bearer() {
  local kind="$1" # "access" or "id"
  local token_file; token_file="$(token_file_for_user "$ZPOOL_USER" "${ZPOOL_API_URL}")"
  if [[ -z "$token_file" ]]; then
    if [[ "$kind" == "access" ]]; then
      echo "$JWT_ACCESS_TOKEN"
    else
      echo "$JWT_ID_TOKEN"
    fi
  else
    jq -r --arg k "${kind}_token" '.[$k]' "$token_file"
  fi
}

# -----------------------------
# API wrappers
# -----------------------------
api_pat_or_jwt_access() {
  # api_pat_or_jwt_access METHOD PATH [JSON_BODY]
  local method="$1"
  local path="$2"
  local data="${3:-}"

  if [[ -n "$ZPOOLPAT" ]]; then
    do_http "$method" "$path" "Authorization: Bearer ${ZPOOLPAT}" "$data"
    if [[ "$HTTP_STATUS" =~ ^2[0-9][0-9]$ ]]; then
      emit_json "$RESPONSE"
      return 0
    elif [[ "$HTTP_STATUS" == "401" || "$HTTP_STATUS" == "403" ]]; then
      emit_json "$RESPONSE"
      die "PAT was rejected with HTTP ${HTTP_STATUS}. Fix ZPOOLPAT or remove it to use JWT."
    else
      emit_json "$RESPONSE"
      die "Request failed with HTTP ${HTTP_STATUS}"
    fi
  fi

  ensure_jwt_fresh
  do_http "$method" "$path" "Authorization: Bearer $(bearer access)" "$data"
  emit_json "$RESPONSE"
}

api_jwt_access() {
  # api_jwt_access METHOD PATH [JSON_BODY]
  local method="$1"
  local path="$2"
  local data="${3:-}"
  ensure_jwt_fresh
  do_http "$method" "$path" "Authorization: Bearer $(bearer access)" "$data"
  emit_json "$RESPONSE"
}

# -----------------------------
# Command groups
# -----------------------------
billing_operations() {
  case "$1" in
    balance)
      api_jwt_access GET "/billing/balance"
      ;;
    ledger)
      # billing ledger [since] [until] [limit]
      local since="${2:-}"
      local until="${3:-}"
      local limit="${4:-}"
      local qs=()
      [[ -n "$since" ]] && qs+=("since=${since}")
      [[ -n "$until" ]] && qs+=("until=${until}")
      [[ -n "$limit" ]] && qs+=("limit=${limit}")
      local query=""
      if (( ${#qs[@]} )); then
        query="?$(IFS='&'; echo "${qs[*]}")"
      fi
      api_jwt_access GET "/billing/ledger${query}"
      ;;
    usage|help|--help|-h|*)
      echo
      echo "Billing commands:"
      echo "  $0 billing balance"
      echo "  $0 billing ledger [since YYYY-MM-DD] [until YYYY-MM-DD] [limit]"
      echo "  (Redeem codes and add credits on the dashboard.)"
      echo
      exit 1
      ;;
  esac
}

job_operations() {
  case "$1" in
    list)    api_pat_or_jwt_access GET "/jobs" ;;
    show)    [[ -n "${2:-}" ]] || die "Missing job_id for job show."; api_pat_or_jwt_access GET "/job/$2" ;;
    history) [[ -n "${2:-}" ]] || die "Missing job_id for job history."; api_pat_or_jwt_access GET "/job/$2/history" ;;
    usage|help|--help|-h|*)
      echo
      echo "Jobs:"
      echo "  $0 job list"
      echo "  $0 job show <job_id>"
      echo "  $0 job history <job_id>"
      echo
      echo "Example of some useful commands:"
      echo
      echo "  List all recent jobs, their type, and parameters"
      echo "    ./zpoolcli.sh job list | jq '.detail.jobs' | mlr --ijson --opprint put '\$last_ts = \$current_status.timestamp' \\"
      echo "      then cut -o -f created_at,last_ts,job_id,job_type,parameters | sort -n"
      echo
      echo "  Showing all the events from a job in tabular form (requires 'mlr'):"
      echo "    ./zpoolcli.sh job history <job_id> | jq '.detail.history' | mlr --ijson --opprint cut -o -f timestamp,event_type,message"
      exit 1
      ;;
  esac
}

pat_operations() {
  case "$1" in
    list)
      api_pat_or_jwt_access GET "/pat"
      ;;
    revoke)
      [[ -n "${2:-}" ]] || die "Missing <key_id> for pat revoke."
      api_jwt_access DELETE "/pat/$2"
      ;;
    usage|help|--help|-h|*)
      echo
      echo "PAT:"
      echo "  $0 pat list"
      echo "  $0 pat revoke <key_id>"
      echo "  (Create PATs on the dashboard.)"
      echo
      exit 1
      ;;
  esac
}

sshkey_operations() {
  case "$1" in
    list)   api_pat_or_jwt_access GET "/sshkey" ;;
    add)    [[ -n "${2:-}" ]] || die "Missing public_key for sshkey add."; api_jwt_access POST "/sshkey" "$(jq -n --arg k "$2" '{pubkey:$k}')" ;;
    delete) [[ -n "${2:-}" ]] || die "Missing pubkey_id for sshkey delete."; api_jwt_access DELETE "/sshkey/$2" ;;
    usage|help|--help|-h|*)
      echo
      echo "SSH Keys:"
      echo "  $0 sshkey list"
      echo "  $0 sshkey add '<public_key>'"
      echo "  $0 sshkey delete <pubkey_id>"
      echo
      exit 1
      ;;
  esac
}

zpool_operations() {
  case "$1" in
    list)    api_pat_or_jwt_access GET "/zpools" ;;
    create)  [[ -n "${2:-}" && -n "${3:-}" ]] || die "Missing args for zpool create."
             api_jwt_access POST "/zpool" "$(jq -n --argjson s "$2" --arg v "$3" '{new_size_in_gib:$s, volume_type:$v}')" ;;
    delete)  [[ -n "${2:-}" ]] || die "Missing zpool_id for delete."
             api_jwt_access DELETE "/zpool/$2" ;;
    scrub)   [[ -n "${2:-}" ]] || die "Missing zpool_id for scrub."
             api_pat_or_jwt_access POST "/zpool/$2/scrub" ;;
    modify)  [[ -n "${2:-}" && -n "${3:-}" ]] || die "Usage: $0 zpool modify <zpool_id> <volume_type: gp3|sc1>"
             local zpid="$2"
             local vt; vt="$(tr '[:upper:]' '[:lower:]' <<<"$3")"
             case "$vt" in gp3|sc1) ;; *) die "Invalid volume_type '$3'. Allowed: gp3, sc1" ;; esac
             local payload; payload="$(jq -n --arg vt "$vt" '{target_volume_type:$vt, volume_type:$vt}')"
             api_pat_or_jwt_access POST "/zpool/${zpid}/modify" "$payload" ;;
    usage|help|--help|-h|*)
      echo
      echo "Zpools:"
      echo "  $0 zpool list"
      echo "  $0 zpool create <new_size_in_gib> <volume_type>"
      echo "  $0 zpool delete <zpool_id>"
      echo "  $0 zpool scrub <zpool_id>"
      echo "  $0 zpool modify <zpool_id> <gp3|sc1>"
      echo
      exit 1
      ;;
  esac
}

function sync_bzfs() {
    _LOCAL_POOL="${1}"
    _REMOTE_POOL="${2}"
    "${BZFS_BIN}" "${_LOCAL_POOL}" "${_REMOTE_POOL}" \
      --recursive \
      --include-snapshot-regex 'autosnap_.*_(daily|monthly)$' \
      --delete-dst-snapshots=snapshots \
      --delete-dst-snapshots-no-crosscheck \
      --no-privilege-elevation
}

zfs_operations() {
  local zfs_cmd="$1"; shift || true

  [[ -n "$SSH_HOST" ]] || die "SSH_HOST is required for zfs ops. Set it in ${DOTFILE} or export SSH_HOST."
  [[ -n "$SSH_PRIVKEY_FILE" ]] || die "SSH_PRIVKEY_FILE is required for zfs ops. Set it in ${DOTFILE} or export SSH_PRIVKEY_FILE."
  [[ -f "$SSH_PRIVKEY_FILE" ]] || die "SSH_PRIVKEY_FILE '$SSH_PRIVKEY_FILE' not found."
  if [[ -z "$ZPOOL_USER" ]]; then
    if is_tty; then
      read -r -p "ZFS SSH username (ZPOOL_USER): " ZPOOL_USER
    else
      die "ZPOOL_USER required for zfs ops. Set it in ${DOTFILE} or export ZPOOL_USER."
    fi
  fi

  case "$zfs_cmd" in
    bzfs)
      [[ -n "$BZFS_BIN" ]] || die "BZFS_BIN is required for bzfs sync. Set it in ${DOTFILE} or export BZFS_BIN."
      [[ -n "$LOCAL_POOL" ]] || die "LOCAL_POOL is required for bzfs sync. Set it in ${DOTFILE} or export LOCAL_POOL."
      [[ -n "$REMOTE_POOL" ]] || die "REMOTE_POOL is required for bzfs sync. Set it in ${DOTFILE} or export REMOTE_POOL."
      sync_bzfs "${LOCAL_POOL}" "${REMOTE_POOL}"
      ;;
    list)
      [[ -n "${1:-}" ]] || die "Missing dataset for zfs list."
      local dataset="$1"; shift || true
      ssh -i "$SSH_PRIVKEY_FILE" "$ZPOOL_USER@$SSH_HOST" zfs list "$dataset" "$@"
      ;;
    destroy)
      [[ -n "${1:-}" ]] || die "Missing dataset for zfs destroy."
      local dataset="$1"; shift || true
      ssh -i "$SSH_PRIVKEY_FILE" "$ZPOOL_USER@$SSH_HOST" zfs destroy "$dataset" "$@"
      ;;
    snapshot)
      [[ -n "${1:-}" ]] || die "Missing dataset@snapshot for zfs snapshot."
      local snap="$1"
      ssh -i "$SSH_PRIVKEY_FILE" "$ZPOOL_USER@$SSH_HOST" zfs snapshot "$snap"
      ;;
    recv)
      (( $# >= 1 )) || { echo; echo "Usage: zfs send localpool/ds@snap | $0 zfs recv [flags...] <zpool/dataset>"; echo; exit 1; }
      local full_dataset="${@: -1}"
      local recv_flags=("${@:1:$#-1}")
      ssh -i "$SSH_PRIVKEY_FILE" "$ZPOOL_USER@$SSH_HOST" zfs recv "${recv_flags[@]}" "$full_dataset"
      ;;
    ssh)
      ssh -i "$SSH_PRIVKEY_FILE" "$ZPOOL_USER@$SSH_HOST" "$@"
      ;;
    usage|help|--help|-h|*)
      echo
      echo "ZFS over SSH:"
      echo "  $0 zfs list <dataset> [flags...]"
      echo "  $0 zfs destroy <dataset> [flags...]"
      echo "  $0 zfs snapshot <dataset@snapshot>"
      echo "  zfs send localpool/ds@snap | $0 zfs recv [flags...] <zpool/dataset>"
      echo "  $0 zfs ssh"
      echo "  $0 zfs bzfs"
      echo
      exit 1
      ;;
  esac
}

# -----------------------------
# Main
# -----------------------------
[[ -n "${1:-}" ]] || { echo "Error: No command provided." >&2; usage; }

case "$1" in
  billing)
    shift
    [[ -n "${1:-}" ]] || { echo "Error: Missing operation for billing." >&2; billing_operations usage; }
    billing_operations "$@"
    ;;
  hello)
    api_pat_or_jwt_access GET "/hello"
    ;;
  job)
    shift
    [[ -n "${1:-}" ]] || { echo "Error: Missing operation for job." >&2; job_operations usage; }
    job_operations "$@"
    ;;
  pat)
    shift
    [[ -n "${1:-}" ]] || { echo "Error: Missing operation for pat." >&2; pat_operations usage; }
    pat_operations "$@"
    ;;
  sshkey)
    shift
    [[ -n "${1:-}" ]] || { echo "Error: Missing operation for sshkey." >&2; sshkey_operations usage; }
    sshkey_operations "$@"
    ;;
  zfs)
    shift
    [[ -n "${1:-}" ]] || { echo "Error: Missing operation for zfs." >&2; zfs_operations usage; }
    zfs_operations "$@"
    ;;
  zpool)
    shift
    [[ -n "${1:-}" ]] || { echo "Error: Missing operation for zpool." >&2; zpool_operations usage; }
    zpool_operations "$@"
    ;;
  usage|help|--help|-h)
    usage
    ;;
  *)
    echo "Error: Unknown command '$1'." >&2
    usage
    ;;
esac

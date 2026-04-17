"""
Brain Training App — End-to-End Smoke Test
==========================================
Tests the full user journey against a running backend.
Run from the brain-training/ directory with the venv active:

    python smoke_test.py

The backend must be running at http://localhost:8000.
"""

import httpx
import sys
import time
import uuid

BASE_URL = "http://localhost:8000"
PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []

def check(name, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((status, name, detail))
    print(f"  {status}  {name}" + (f" — {detail}" if detail else ""))
    return condition

def section(title):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")

def run():
    email = f"smoketest_{uuid.uuid4().hex[:8]}@test.com"
    username = f"smoketest_{uuid.uuid4().hex[:6]}"
    password = "SmokeTest123!"
    token = None
    headers = {}
    session_id = None

    # ── 1. Health check ──────────────────────────────────────────
    section("1. Health Check")
    try:
        r = httpx.get(f"{BASE_URL}/health")
        check("Backend is reachable", r.status_code == 200, f"status={r.status_code}")
        check("Health response is healthy", r.json().get("status") == "healthy")
    except Exception as e:
        check("Backend is reachable", False, str(e))
        print("\n  Cannot reach backend. Is it running at http://localhost:8000?")
        print("  Start it with: DATABASE_URL=\"sqlite:////tmp/brain_training.db\" python -m uvicorn backend.main:app --reload\n")
        summarise()
        sys.exit(1)

    # ── 2. Registration ──────────────────────────────────────────
    section("2. User Registration")
    r = httpx.post(f"{BASE_URL}/api/auth/register", json={
        "email": email, "username": username, "password": password, "consent_given": True
    })
    check("Register returns 200", r.status_code == 200, f"status={r.status_code}")
    if r.status_code == 200:
        data = r.json()
        token = data.get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        check("Token returned", bool(token))
        check("User data returned", "user" in data)
        check("Email matches", data["user"].get("email") == email)

    # ── 2b. Registration without consent (unhappy path) ──────────
    r_no_consent = httpx.post(f"{BASE_URL}/api/auth/register", json={
        "email": f"noconsent_{uuid.uuid4().hex[:6]}@test.com",
        "username": f"noconsent_{uuid.uuid4().hex[:6]}",
        "password": password,
        "consent_given": False
    })
    check("No-consent registration returns 400", r_no_consent.status_code == 400,
          f"status={r_no_consent.status_code}")

    # ── 3. Duplicate registration ────────────────────────────────
    section("3. Duplicate Registration (unhappy path)")
    r = httpx.post(f"{BASE_URL}/api/auth/register", json={
        "email": email, "username": username, "password": password, "consent_given": True
    })
    check("Duplicate email returns 400", r.status_code == 400, f"status={r.status_code}")
    check("Error message present", "message" in r.json().get("detail", {}))

    # ── 4. Login ─────────────────────────────────────────────────
    section("4. Login")
    r = httpx.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password})
    check("Login returns 200", r.status_code == 200, f"status={r.status_code}")
    if r.status_code == 200:
        token = r.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        check("Token returned on login", bool(token))

    r = httpx.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": "wrong"})
    check("Wrong password returns 401", r.status_code == 401, f"status={r.status_code}")

    # ── 5. Get current user ──────────────────────────────────────
    section("5. Auth — Get Current User")
    r = httpx.get(f"{BASE_URL}/api/auth/me", headers=headers)
    check("/api/auth/me returns 200", r.status_code == 200, f"status={r.status_code}")
    check("Email matches", r.json().get("email") == email)

    r = httpx.get(f"{BASE_URL}/api/auth/me")
    check("Unauthenticated /me returns 401", r.status_code == 401, f"status={r.status_code}")

    # ── 6. Baseline ──────────────────────────────────────────────
    section("6. Baseline Assessment")
    r = httpx.post(f"{BASE_URL}/api/baseline/start", headers=headers)
    check("Baseline start returns 200", r.status_code == 200, f"status={r.status_code}")

    domain_scores = [
        {"domain": "processing_speed", "score": 72.5},
        {"domain": "working_memory",   "score": 68.0},
        {"domain": "attention",        "score": 75.0},
    ]
    r = httpx.post(f"{BASE_URL}/api/baseline/submit", json=domain_scores, headers=headers)
    check("Baseline submit returns 200", r.status_code == 200, f"status={r.status_code}")
    if r.status_code == 200:
        data = r.json()
        check("is_original is True for first baseline", data.get("is_original") is True)
        check("baseline_number is 1", data.get("baseline_number") == 1)
        check("3 domain results returned", len(data.get("results", [])) == 3)

    r = httpx.get(f"{BASE_URL}/api/baseline/next-eligible-date", headers=headers)
    check("Next eligible date returns 200", r.status_code == 200, f"status={r.status_code}")

    r = httpx.post(f"{BASE_URL}/api/baseline/submit", json=[{"domain": "invalid_domain", "score": 50}], headers=headers)
    check("Invalid domain returns 400", r.status_code == 400, f"status={r.status_code}")

    # ── 7. Training Session ──────────────────────────────────────
    section("7. Training Session")
    r = httpx.post(f"{BASE_URL}/api/sessions/start", headers=headers, json={
        "domain_1": "processing_speed",
        "domain_2": "working_memory",
        "is_baseline": 0
    })
    check("Session start returns 200", r.status_code == 200, f"status={r.status_code}")
    if r.status_code == 200:
        session_id = r.json().get("id")
        check("Session ID returned", bool(session_id), f"id={session_id}")

    if session_id:
        # Get next exercise
        r = httpx.get(f"{BASE_URL}/api/sessions/{session_id}/next", headers=headers)
        check("Get next exercise returns 200", r.status_code == 200, f"status={r.status_code}")
        if r.status_code == 200:
            ex = r.json()
            check("Exercise type returned", "exercise_type" in ex, ex.get("exercise_type"))
            check("Domain returned", "domain" in ex, ex.get("domain"))
            check("Difficulty level returned", "difficulty_level" in ex)

        # Log 8 exercise results
        domains = ["processing_speed"] * 4 + ["working_memory"] * 4
        exercise_types = ["symbol_matching", "symbol_matching", "visual_categorisation", "visual_categorisation",
                         "n_back", "n_back", "digit_span", "digit_span"]
        all_logged = True
        for i in range(8):
            r = httpx.post(f"{BASE_URL}/api/sessions/{session_id}/exercise-result", headers=headers, json={
                "domain": domains[i],
                "exercise_type": exercise_types[i],
                "trials_presented": 10,
                "trials_correct": 7 + (i % 3),
                "avg_response_ms": 450
            })
            if r.status_code != 200:
                all_logged = False
        check("All 8 exercise results logged", all_logged)

        # Session should now be complete
        r = httpx.get(f"{BASE_URL}/api/sessions/{session_id}/next", headers=headers)
        check("Next exercise returns complete=True after 8 attempts",
              r.status_code == 200 and r.json().get("complete") is True,
              str(r.json()))

        # Complete session
        r = httpx.post(f"{BASE_URL}/api/sessions/{session_id}/complete", headers=headers)
        check("Session complete returns 200", r.status_code == 200, f"status={r.status_code}")

        # Get session
        r = httpx.get(f"{BASE_URL}/api/sessions/{session_id}", headers=headers)
        check("Get session returns 200", r.status_code == 200, f"status={r.status_code}")

        # List sessions
        r = httpx.get(f"{BASE_URL}/api/sessions", headers=headers)
        check("List sessions returns 200", r.status_code == 200)
        check("Session appears in list", any(s["id"] == session_id for s in r.json()))

    # ── 8. Progress & Dashboard ──────────────────────────────────
    section("8. Progress & Dashboard")
    r = httpx.get(f"{BASE_URL}/api/progress/dashboard", headers=headers)
    check("Dashboard returns 200", r.status_code == 200, f"status={r.status_code}")
    if r.status_code == 200:
        d = r.json()
        check("Streak present in dashboard", "streak" in d)
        check("Brain health score present", "brain_health_score" in d)
        check("Domain scores present", "domain_scores" in d)

    r = httpx.get(f"{BASE_URL}/api/progress/brain-health", headers=headers)
    check("Brain health score returns 200", r.status_code == 200, f"status={r.status_code}")

    r = httpx.get(f"{BASE_URL}/api/progress/streak", headers=headers)
    check("Streak returns 200", r.status_code == 200, f"status={r.status_code}")
    if r.status_code == 200:
        check("Streak incremented after session", r.json().get("current_streak", 0) >= 1)

    r = httpx.get(f"{BASE_URL}/api/progress/trend/processing_speed", headers=headers)
    check("Domain trend returns 200", r.status_code == 200, f"status={r.status_code}")

    r = httpx.get(f"{BASE_URL}/api/progress/domain/processing_speed", headers=headers)
    check("Domain progress returns 200", r.status_code == 200, f"status={r.status_code}")

    # ── 9. Lifestyle Logging ─────────────────────────────────────
    section("9. Lifestyle Logging")
    r = httpx.post(f"{BASE_URL}/api/lifestyle/log", headers=headers, json={
        "exercise_minutes": 35,
        "sleep_hours": 7.5,
        "sleep_quality": 4,
        "stress_level": 2,
        "mood": 4,
        "social_engagement": 1
    })
    check("Lifestyle log returns 200", r.status_code == 200, f"status={r.status_code}")

    r = httpx.get(f"{BASE_URL}/api/lifestyle/today", headers=headers)
    check("Today's lifestyle log returns 200", r.status_code == 200, f"status={r.status_code}")
    if r.status_code == 200:
        log = r.json()
        check("Exercise minutes saved correctly", log.get("exercise_minutes") == 35)
        check("Sleep hours saved correctly", log.get("sleep_hours") == 7.5)

    r = httpx.get(f"{BASE_URL}/api/lifestyle/history", headers=headers)
    check("Lifestyle history returns 200", r.status_code == 200, f"status={r.status_code}")

    # Log again (upsert — same day)
    r = httpx.post(f"{BASE_URL}/api/lifestyle/log", headers=headers, json={
        "exercise_minutes": 45, "sleep_hours": 8.0, "stress_level": 1, "mood": 5
    })
    check("Lifestyle upsert (same day) returns 200", r.status_code == 200, f"status={r.status_code}")

    # Brain health score should now include lifestyle
    r = httpx.get(f"{BASE_URL}/api/progress/brain-health", headers=headers)
    if r.status_code == 200:
        score = r.json().get("brain_health_score", 0)
        check("Brain health score > 0 after lifestyle log", score > 0, f"score={score}")

    # ── 10. Account ──────────────────────────────────────────────
    section("10. Account Management")
    r = httpx.get(f"{BASE_URL}/api/account/profile", headers=headers)
    check("Profile returns 200", r.status_code == 200, f"status={r.status_code}")

    new_time = "08:30"
    r = httpx.patch(f"{BASE_URL}/api/account/account", headers=headers, json={
        "notification_time": new_time
    })
    check("PATCH account returns 200", r.status_code == 200, f"status={r.status_code}")

    # ── 11. Count Back Match (N-Back) — self-paced game flow ────────
    section("11. Count Back Match — N-Back Game Flow")
    # Create a fresh session to log n_back results into
    r = httpx.post(f"{BASE_URL}/api/sessions/start", headers=headers, json={
        "domain_1": "working_memory",
        "domain_2": "attention",
        "is_baseline": 0
    })
    check("Session for n_back starts OK", r.status_code == 200, f"status={r.status_code}")
    if r.status_code == 200:
        nback_session_id = r.json().get("id")

        # Test 1: n_back result with avg_response_ms=0 (accuracy-only scoring)
        r = httpx.post(
            f"{BASE_URL}/api/sessions/{nback_session_id}/exercise-result",
            headers=headers,
            json={
                "domain": "working_memory",
                "exercise_type": "n_back",
                "trials_presented": 15,
                "trials_correct": 10,
                "avg_response_ms": 0
            }
        )
        check("n_back result with avg_response_ms=0 accepted (accuracy-only scoring)", r.status_code == 200, f"status={r.status_code}")
        if r.status_code == 200:
            d = r.json()
            check("trials_presented stored correctly", d.get("trials_presented") == 15)
            check("trials_correct stored correctly", d.get("trials_correct") == 10)
            check("avg_response_ms=0 stored correctly", d.get("avg_response_ms") == 0)

        # Test 2: n_back result with all-correct score (perfect game)
        r = httpx.post(
            f"{BASE_URL}/api/sessions/{nback_session_id}/exercise-result",
            headers=headers,
            json={
                "domain": "working_memory",
                "exercise_type": "n_back",
                "trials_presented": 15,
                "trials_correct": 15,
                "avg_response_ms": 0
            }
        )
        check("n_back all-correct result accepted", r.status_code == 200, f"status={r.status_code}")

        # Test 3: n_back result with zero correct (all wrong)
        r = httpx.post(
            f"{BASE_URL}/api/sessions/{nback_session_id}/exercise-result",
            headers=headers,
            json={
                "domain": "working_memory",
                "exercise_type": "n_back",
                "trials_presented": 15,
                "trials_correct": 0,
                "avg_response_ms": 0
            }
        )
        check("n_back zero-correct result accepted", r.status_code == 200, f"status={r.status_code}")

        # Test 4: n_back result without auth is rejected
        r = httpx.post(
            f"{BASE_URL}/api/sessions/{nback_session_id}/exercise-result",
            json={
                "domain": "working_memory",
                "exercise_type": "n_back",
                "trials_presented": 15,
                "trials_correct": 8,
                "avg_response_ms": 0
            }
        )
        check("Unauthenticated n_back submission rejected (401)", r.status_code == 401, f"status={r.status_code}")

    # ── 12. Logout ───────────────────────────────────────────────
    section("12. Logout")
    r = httpx.post(f"{BASE_URL}/api/auth/logout", headers=headers)
    check("Logout returns 200", r.status_code == 200, f"status={r.status_code}")

    # ── Summary ──────────────────────────────────────────────────
    summarise()

def summarise():
    section("SUMMARY")
    passed = sum(1 for s, _, _ in results if s == PASS)
    failed = sum(1 for s, _, _ in results if s == FAIL)
    total = len(results)
    print(f"  {passed}/{total} checks passed")
    if failed:
        print(f"\n  Failed checks:")
        for status, name, detail in results:
            if status == FAIL:
                print(f"    {FAIL}  {name}" + (f" — {detail}" if detail else ""))
    verdict = "PASS" if failed == 0 else "FAIL"
    print(f"\n  Overall: {verdict}\n")

if __name__ == "__main__":
    run()

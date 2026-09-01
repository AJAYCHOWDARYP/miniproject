"""
Integration tests for Report-Driven Healthcare Assistant API endpoints.
Verifies:
1. Zero fake data startup
2. Report upload -> extraction -> live analysis -> confirm to history
3. Second report upload -> dynamic delta trend generation
4. Meal timing reminders configuration
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_auth_and_dashboard_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Login
        login_res = await ac.post("/api/v1/auth/login", json={"email": "demo@healthcare.ai", "password": "DemoPassword123!"})
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Clean report state for fresh test execution
        await ac.delete("/api/v1/reports/clear-all", headers=headers)

        # 2. Get dashboard summary
        dash_res = await ac.get("/api/v1/wellness/dashboard-summary", headers=headers)
        assert dash_res.status_code == 200
        dash_data = dash_res.json()
        assert "today_overview" in dash_data

        # 3. Test meal reminders
        rem_res = await ac.get("/api/v1/wellness/reminders/diet", headers=headers)
        assert rem_res.status_code == 200
        assert len(rem_res.json()) >= 5

        # 4. Upload report 1 (Fasting Glucose + HbA1c)
        r1_text = "LABORATORY REPORT\nDate: 2026-08-10\nFasting Blood Glucose: 110.0 mg/dL (70 - 99)\nHbA1c: 6.2 % (4.0 - 5.6)\nTotal Cholesterol: 210.0 mg/dL (125 - 200)"
        upload_res = await ac.post(
            "/api/v1/reports/upload",
            headers=headers,
            files={"file": ("lab1.txt", r1_text.encode("utf-8"), "text/plain")},
            data={"title": "Baseline Metabolic Panel", "report_type": "Blood Test"}
        )
        assert upload_res.status_code == 200
        up1_data = upload_res.json()
        rep1_id = up1_data["report_id"]
        assert up1_data["results_extracted_count"] == 3
        assert "ai_insights" in up1_data

        # 5. Confirm report 1
        verify_res = await ac.put(
            f"/api/v1/reports/{rep1_id}/verify",
            headers=headers,
            json={"results": up1_data["results"]}
        )
        assert verify_res.status_code == 200

        # 6. Upload follow-up report 2 (improved Glucose & HbA1c)
        r2_text = "FOLLOW UP LAB\nDate: 2026-08-20\nFasting Blood Glucose: 98.0 mg/dL (70 - 99)\nHbA1c: 5.7 % (4.0 - 5.6)\nTotal Cholesterol: 190.0 mg/dL (125 - 200)"
        upload2_res = await ac.post(
            "/api/v1/reports/upload",
            headers=headers,
            files={"file": ("lab2.txt", r2_text.encode("utf-8"), "text/plain")},
            data={"title": "Follow-up Metabolic Panel", "report_type": "Blood Test"}
        )
        assert upload2_res.status_code == 200
        rep2_id = upload2_res.json()["report_id"]
        await ac.put(f"/api/v1/reports/{rep2_id}/verify", headers=headers, json={"results": upload2_res.json()["results"]})

        # 7. Compare the two reports
        comp_res = await ac.get(f"/api/v1/reports/compare?report_id_1={rep1_id}&report_id_2={rep2_id}", headers=headers)
        assert comp_res.status_code == 200
        comp_data = comp_res.json()
        assert len(comp_data["comparison_table"]) == 3

        # 8. Check dynamic trends
        trend_res = await ac.get("/api/v1/trends/biomarkers", headers=headers)
        assert trend_res.status_code == 200
        trend_data = trend_res.json()
        assert trend_data["has_sufficient_data"] is True
        assert len(trend_data["trends"]) >= 3

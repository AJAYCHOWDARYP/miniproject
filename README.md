# Personalized Healthcare AI Assistant

A secure, patient-centric healthcare platform designed to organize medical records, extract and explain laboratory reports and prescriptions via OCR/Document AI, track medications and adherence, provide personalized lifestyle support (safe exercise and balanced nutrition), monitor longitudinal biomarkers, and provide safe decision-support under physician oversight.

---

## 🌟 Key Features

1. **Medical Document Ingestion & Human-in-the-Loop OCR Verification**:
   - Supports PDFs, scans, and images.
   - Extracts canonical biomarkers (HbA1c, Fasting Blood Glucose, Lipid Profiles, Kidney/Liver markers, CBC).
   - Split-screen verification UI allows patient confirmation and edits before committing to health trends.

2. **5-Layer Structured Medical Explanations**:
   - **Layer 1**: Plain-Language Summary (6th-grade reading level).
   - **Layer 2**: Abnormal Findings identification against laboratory reference ranges.
   - **Layer 3**: Cautious Possible Associations ("Can be influenced by diet, hydration, metabolism...").
   - **Layer 4**: Longitudinal Historical Trends across multiple dates.
   - **Layer 5**: Suggested Questions for Doctor visits.

3. **Prescriptions, Reminders & Adherence Tracking**:
   - Digitizes prescriptions without altering doctor instructions.
   - Generates daily time slots (e.g. 08:30 AM, 08:30 PM).
   - Daily checklist with **Taken**, **Snooze**, and **Skip** actions.
   - Computes daily & weekly adherence percentage (e.g. 92%).
   - **Safe Missed-Dose Protocol**: Strictly warns against double dosing.

4. **Personalized Safe Movement & Nutrition**:
   - Health limitation screening (hypertension, cardiac, pregnancy, osteoarthritis).
   - Flags doctor clearance requirements for flagged conditions.
   - Mifflin-St Jeor energy calculations with authentic Indian and Mediterranean balanced options.

5. **Clinical Safety & Emergency Escalation Guardrails**:
   - **Zero Autonomous Diagnosis**: Strictly rejects attempts to diagnose diseases.
   - **Zero Autonomous Prescription**: Strictly refuses to prescribe drugs or alter dosages.
   - **Real-Time Emergency Triage**: Detects red-flag symptoms (chest pain, stroke symptoms, acute dyspnea) and immediately surfaces 911 / 112 hotline guidance.

6. **Secure "Share With Doctor" Portal**:
   - Time-limited (48h) tokenized link and printable 1-page clinical summary.

7. **HIPAA / GDPR Compliance & Security**:
   - AES-256 encrypted file storage.
   - Immutable audit trail recording every access and export with zero PHI logged.
   - Full "Export My Data" and "Permanent Account Deletion" capabilities.

---

## 🚀 Quickstart

```bash
# 1. Install dependencies
pip install fastapi uvicorn pydantic sqlalchemy aiosqlite python-multipart pytest pytest-asyncio pillow pypdf cryptography pyjwt apscheduler

# 2. Run Test Suite
pytest backend/tests

# 3. Launch Server
python run.py
```

Access the Web Application at: **http://127.0.0.1:8000**

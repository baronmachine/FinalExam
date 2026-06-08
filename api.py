from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import sqlite3

DB_PATH = "hospital.db"

app = FastAPI(title="Hospital Appointment API")


class Doctor(BaseModel):
    DoctorID: int
    FullName: str = Field(min_length=5, max_length=100)
    Specialization: str = Field(min_length=3, max_length=60)
    Fee: float = Field(gt=0.0, le=10000.0)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            DoctorID       INTEGER PRIMARY KEY,
            FullName       TEXT NOT NULL,
            Specialization TEXT NOT NULL,
            Fee            REAL NOT NULL
        )
    """)
    cur.execute("SELECT COUNT(*) AS c FROM doctors")
    if cur.fetchone()["c"] == 0:
        cur.executemany(
            "INSERT INTO doctors VALUES (?, ?, ?, ?)",
            [
                (1, "Dr. Aydan Mammadova", "Cardiology",    150.0),
                (2, "Dr. Rashad Aliyev",   "Neurology",     220.0),
                (3, "Dr. Leyla Huseynova", "Pediatrics",     90.0),
                (4, "Dr. Elvin Quliyev",   "Orthopedics",   180.0),
                (5, "Dr. Nigar Ismayilova","Dermatology",   120.0),
            ],
        )
    conn.commit()
    conn.close()


init_db()


@app.get("/doctors")
def list_doctors():
    conn = get_db()
    rows = conn.execute("SELECT * FROM doctors ORDER BY DoctorID").fetchall()
    conn.close()
    return [
        {
            "id":             r["DoctorID"],
            "name":           r["FullName"],
            "specialization": r["Specialization"],
            "fee":            r["Fee"],
        }
        for r in rows
    ]


@app.post("/doctors")
def add_doctor(d: Doctor):
    conn = get_db()
    cur = conn.cursor()
    exists = cur.execute(
        "SELECT 1 FROM doctors WHERE DoctorID = ?", (d.DoctorID,)
    ).fetchone()
    if exists:
        conn.close()
        raise HTTPException(status_code=400, detail="DoctorID artıq mövcuddur")
    cur.execute(
        "INSERT INTO doctors (DoctorID, FullName, Specialization, Fee) VALUES (?, ?, ?, ?)",
        (d.DoctorID, d.FullName, d.Specialization, d.Fee),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "id": d.DoctorID}


@app.delete("/doctors/{doctor_id}")
def delete_doctor(doctor_id: int):
    conn = get_db()
    cur = conn.cursor()
    row = cur.execute(
        "SELECT 1 FROM doctors WHERE DoctorID = ?", (doctor_id,)
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Doctor tapılmadı")
    cur.execute("DELETE FROM doctors WHERE DoctorID = ?", (doctor_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted", "id": doctor_id}

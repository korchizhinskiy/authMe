backend() {
  echo "Start server"
  alembic upgrade head
  uvicorn app.main:app --proxy-headers --host 0.0.0.0 --port 8000 --reload
}
$1

.PHONY: setup test run ingest clean

setup:
	python3 -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt

test:
	./venv/bin/pytest -v

ingest:
	./venv/bin/python scripts/ingest.py

eval-retrieval:
	./venv/bin/python scripts/evaluate_retrieval.py

run-api:
	./venv/bin/uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload

run-demo:
	./venv/bin/python scripts/run_realtime_demo.py

clean:
	rm -rf __pycache__ .pytest_cache data/cache data/indices

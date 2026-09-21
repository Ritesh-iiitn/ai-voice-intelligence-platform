.PHONY: setup test eval eval-q2 eval-q3 eval-q4 serve clean

setup:
	python3 -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt

test:
	./venv/bin/pytest -v

eval: eval-q2 eval-q3 eval-q4

eval-q2:
	./venv/bin/python scripts/evaluate_retrieval.py

eval-q3:
	./venv/bin/python scripts/evaluate_multilingual.py

eval-q4:
	./venv/bin/python scripts/evaluate_realtime.py

serve:
	./venv/bin/uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload

clean:
	rm -rf __pycache__ .pytest_cache data/cache data/indices .coverage htmlcov

.PHONY: setup validate load dbt-run anomalies commentary app all test

setup:
	python -m pip install -r requirements.txt

validate:
	python -c "import sys; sys.path.insert(0, 'src'); from finsight.validate import main; main()"

load:
	python -c "import sys; sys.path.insert(0, 'src'); from finsight.load_duckdb import main; main()"

dbt-run:
	cd dbt_finance && dbt run --profiles-dir .

anomalies:
	python -c "import sys; sys.path.insert(0, 'src'); from finsight.anomalies import main; main()"

commentary:
	python -c "import sys; sys.path.insert(0, 'src'); from finsight.commentary import main; main()"

app:
	streamlit run app/streamlit_app.py

all: validate load dbt-run anomalies commentary

test:
	pytest

# Exemple pour le test de concurrence avec 10 utilisateurs
export BENCHMARK_PARAM=10
export BENCHMARK_FILE=conc.csv
for run in 1 2 3
do
    export BENCHMARK_RUN=$run
    locust -f locustfile.py --headless -u 10 -r 2 --run-time 10s --host https://tinyinsta-gcp.ew.r.appspot.com
done
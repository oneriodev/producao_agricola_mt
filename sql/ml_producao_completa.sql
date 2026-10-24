vscode ➜ /workspaces/producao_agricola_mt (main) $ mkdir -p src/ml notebooks
touch src/ml/__init__.py
vscode ➜ /workspaces/producao_agricola_mt (main) $ python -m src.ml.features
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/workspaces/producao_agricola_mt/src/ml/features.py", line 134, in <module>
    feats = features_clusterizacao()
            ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/producao_agricola_mt/src/ml/features.py", line 117, in features_clusterizacao
    df = carregar_producao()
         ^^^^^^^^^^^^^^^^^^^
  File "/workspaces/producao_agricola_mt/src/ml/features.py", line 37, in carregar_producao
    return queries.executar("ml_producao_completa")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/producao_agricola_mt/src/queries.py", line 30, in executar
    consulta = text(ler_sql(nome))
                    ^^^^^^^^^^^^^
  File "/workspaces/producao_agricola_mt/src/queries.py", line 25, in ler_sql
    return (SQL_DIR / f"{nome}.sql").read_text(encoding="utf-8")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/pathlib.py", line 1058, in read_text
    with self.open(mode='r', encoding=encoding, errors=errors) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/pathlib.py", line 1044, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/workspaces/producao_agricola_mt/sql/ml_producao_completa.sql'
vscode ➜ /workspaces/producao_agricola_mt (main) $ 
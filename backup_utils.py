import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from database import get_db_config


BASE_DIR = Path(__file__).resolve().parent
BACKUP_DIR = BASE_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)


class BackupError(Exception):
    pass


def _find_mysql_tool(tool_name):
    mysql_bin_dir = os.getenv("MYSQL_BIN_DIR", "").strip()
    candidates = []
    if mysql_bin_dir:
        candidates.append(Path(mysql_bin_dir) / tool_name)

    candidates.extend(
        [
            Path(r"C:\Program Files\MySQL\MySQL Server 8.0\bin") / tool_name,
            Path(r"C:\Program Files\MySQL\MySQL Server 8.4\bin") / tool_name,
            Path(r"C:\xampp\mysql\bin") / tool_name,
        ]
    )

    which_path = shutil.which(tool_name)
    if which_path:
        candidates.insert(0, Path(which_path))

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    raise BackupError(f"NAO FOI POSSIVEL LOCALIZAR {tool_name}. CONFIGURE MYSQL_BIN_DIR OU INSTALE O CLIENTE MYSQL.")


def _db_env():
    cfg = get_db_config()
    env = os.environ.copy()
    env["MYSQL_PWD"] = cfg["password"]
    return cfg, env


def criar_backup_completo():
    cfg, env = _db_env()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_estacionamento_{timestamp}.zip"
    backup_path = BACKUP_DIR / backup_name

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        sql_path = tmp_path / "estacionamento.sql"
        mysqldump = _find_mysql_tool("mysqldump.exe")

        dump_cmd = [
            mysqldump,
            "-h",
            cfg["host"],
            "-P",
            str(cfg["port"]),
            "-u",
            cfg["user"],
            "--databases",
            cfg["database"],
            "--routines",
            "--events",
            "--triggers",
            "--single-transaction",
            "--result-file",
            str(sql_path),
        ]
        result = subprocess.run(dump_cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            raise BackupError(result.stderr.strip() or "NAO FOI POSSIVEL GERAR O DUMP DO MYSQL.")

        with ZipFile(backup_path, "w", compression=ZIP_DEFLATED) as zip_file:
            for file_path in BASE_DIR.rglob("*"):
                if not file_path.is_file():
                    continue
                if BACKUP_DIR in file_path.parents:
                    continue

                arcname = Path("app_files") / file_path.relative_to(BASE_DIR)
                zip_file.write(file_path, arcname)

            zip_file.write(sql_path, Path("database") / "estacionamento.sql")

    return backup_path


def restaurar_backup_completo(backup_file):
    cfg, env = _db_env()
    mysql = _find_mysql_tool("mysql.exe")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        extract_dir = tmp_path / "restore"
        extract_dir.mkdir(parents=True, exist_ok=True)

        with ZipFile(backup_file, "r") as zip_file:
            zip_file.extractall(extract_dir)

        sql_path = extract_dir / "database" / "estacionamento.sql"
        app_files_dir = extract_dir / "app_files"
        if not sql_path.exists():
            raise BackupError("ARQUIVO estacionamento.sql NAO ENCONTRADO NO BACKUP.")
        if not app_files_dir.exists():
            raise BackupError("PASTA app_files NAO ENCONTRADA NO BACKUP.")

        restore_cmd = [
            mysql,
            "-h",
            cfg["host"],
            "-P",
            str(cfg["port"]),
            "-u",
            cfg["user"],
        ]
        with sql_path.open("rb") as sql_file:
            result = subprocess.run(restore_cmd, env=env, stdin=sql_file, capture_output=True, text=False)
        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="ignore").strip() if result.stderr else ""
            raise BackupError(stderr or "NAO FOI POSSIVEL RESTAURAR O BANCO DE DADOS.")

        for source in app_files_dir.rglob("*"):
            if not source.is_file():
                continue
            relative = source.relative_to(app_files_dir)
            if relative.parts and relative.parts[0].lower() == "backups":
                continue

            target = BASE_DIR / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    return True

"""
JCL Generator Engine
Loads modular JCL templates from jcl_templates/ and renders valid IBM z/OS JCL
with 71-column continuation compliance, Job Card parameter toggles, all major
mainframe utilities, DD customization, COND= parameters, and IF/THEN/ELSE/ENDIF logic.
"""

import os
import re
from datetime import datetime
from string import Template
from typing import Any, Dict, List

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jcl_templates")

UTILITY_METADATA: Dict[str, Dict[str, Any]] = {
    "IEFBR14": {
        "name": "IEFBR14",
        "title": "IEFBR14 — Allocate / Delete Datasets",
        "category": "Dataset Management",
        "description": "No-op utility used to allocate new datasets, delete/uncatalog existing datasets, or check DD syntax.",
        "template": "iefbr14.jcl.tpl",
        "default_step_name": "STEP010",
        "default_dds": [
            {
                "dd_name": "DD1",
                "dsn": "PROD.USER.NEW.DATA",
                "disp_status": "NEW",
                "disp_normal": "CATLG",
                "disp_abnormal": "DELETE",
                "include_space": True,
                "space_unit": "CYL",
                "space_pri": "10",
                "space_sec": "5",
                "space_dir": "0",
                "include_dcb": True,
                "recfm": "FB",
                "lrecl": "80",
                "blksize": "0",
                "unit": "SYSDA",
                "vol_ser": "",
                "dsntype": "",
                "dummy": False,
                "sysout": "",
            }
        ],
        "default_sysin": "",
    },
    "IEBGENER": {
        "name": "IEBGENER",
        "title": "IEBGENER — Sequential Copy / Print",
        "category": "Dataset Copy",
        "description": "Copies sequential datasets, creates backup flat files, or reformats records with control statements.",
        "template": "iebgener.jcl.tpl",
        "default_step_name": "COPY010",
        "default_dds": [
            {
                "dd_name": "SYSUT1",
                "dsn": "PROD.INPUT.SEQ.FILE",
                "disp_status": "SHR",
                "disp_normal": "",
                "disp_abnormal": "",
                "include_space": False,
                "space_unit": "TRK",
                "space_pri": "10",
                "space_sec": "5",
                "space_dir": "0",
                "include_dcb": False,
                "recfm": "FB",
                "lrecl": "80",
                "blksize": "0",
                "unit": "",
                "vol_ser": "",
                "dsntype": "",
                "dummy": False,
                "sysout": "",
            },
            {
                "dd_name": "SYSUT2",
                "dsn": "PROD.OUTPUT.SEQ.BACKUP",
                "disp_status": "NEW",
                "disp_normal": "CATLG",
                "disp_abnormal": "DELETE",
                "include_space": True,
                "space_unit": "CYL",
                "space_pri": "15",
                "space_sec": "5",
                "space_dir": "0",
                "include_dcb": True,
                "recfm": "FB",
                "lrecl": "80",
                "blksize": "0",
                "unit": "SYSDA",
                "vol_ser": "",
                "dsntype": "",
                "dummy": False,
                "sysout": "",
            },
        ],
        "default_sysin": "DUMMY",
    },
    "IDCAMS": {
        "name": "IDCAMS",
        "title": "IDCAMS — VSAM / Access Method Services",
        "category": "VSAM & Catalog",
        "description": "Defines/deletes VSAM clusters (KSDS, ESDS, RRDS), GDGs, executes REPRO, PRINT, and LISTCAT.",
        "template": "idcams.jcl.tpl",
        "default_step_name": "VSAM010",
        "default_dds": [
            {
                "dd_name": "INDD",
                "dsn": "PROD.INPUT.SEQ.DATA",
                "disp_status": "SHR",
                "disp_normal": "",
                "disp_abnormal": "",
                "include_space": False,
                "space_unit": "TRK",
                "space_pri": "10",
                "space_sec": "5",
                "space_dir": "0",
                "include_dcb": False,
                "recfm": "FB",
                "lrecl": "80",
                "blksize": "0",
                "unit": "",
                "vol_ser": "",
                "dsntype": "",
                "dummy": False,
                "sysout": "",
            },
            {
                "dd_name": "OUTDD",
                "dsn": "PROD.VSAM.KSDS.CLUSTER",
                "disp_status": "SHR",
                "disp_normal": "",
                "disp_abnormal": "",
                "include_space": False,
                "space_unit": "TRK",
                "space_pri": "10",
                "space_sec": "5",
                "space_dir": "0",
                "include_dcb": False,
                "recfm": "FB",
                "lrecl": "80",
                "blksize": "0",
                "unit": "",
                "vol_ser": "",
                "dsntype": "",
                "dummy": False,
                "sysout": "",
            },
        ],
        "default_sysin": (
            "  DELETE PROD.VSAM.KSDS.CLUSTER CLUSTER PURGE\n"
            "  IF LASTCC = 8 THEN SET MAXCC = 0\n"
            "  DEFINE CLUSTER (NAME(PROD.VSAM.KSDS.CLUSTER) -\n"
            "         INDEXED -\n"
            "         CYLINDERS(10 5) -\n"
            "         KEYS(10 0) -\n"
            "         RECORDSIZE(80 80) -\n"
            "         SHAREOPTIONS(2 3)) -\n"
            "    DATA (NAME(PROD.VSAM.KSDS.CLUSTER.DATA)) -\n"
            "    INDEX (NAME(PROD.VSAM.KSDS.CLUSTER.INDEX))\n"
            "  REPRO INFILE(INDD) OUTFILE(OUTDD)"
        ),
    },
    "SORT": {
        "name": "SORT",
        "title": "SORT / DFSORT — Sort, Merge & Filter",
        "category": "Data Processing",
        "description": "High-speed sorting, merging, copying, INCLUDE/OMIT filtering, OUTREC reformatting, and deduplication (SUM FIELDS=NONE).",
        "template": "sort.jcl.tpl",
        "default_step_name": "SORT010",
        "default_dds": [
            {
                "dd_name": "SORTIN",
                "dsn": "PROD.UNSORTED.INPUT.FILE",
                "disp_status": "SHR",
                "disp_normal": "",
                "disp_abnormal": "",
                "include_space": False,
                "space_unit": "TRK",
                "space_pri": "10",
                "space_sec": "5",
                "space_dir": "0",
                "include_dcb": False,
                "recfm": "FB",
                "lrecl": "80",
                "blksize": "0",
                "unit": "",
                "vol_ser": "",
                "dsntype": "",
                "dummy": False,
                "sysout": "",
            },
            {
                "dd_name": "SORTOUT",
                "dsn": "PROD.SORTED.OUTPUT.FILE",
                "disp_status": "NEW",
                "disp_normal": "CATLG",
                "disp_abnormal": "DELETE",
                "include_space": True,
                "space_unit": "CYL",
                "space_pri": "20",
                "space_sec": "10",
                "space_dir": "0",
                "include_dcb": True,
                "recfm": "FB",
                "lrecl": "80",
                "blksize": "0",
                "unit": "SYSDA",
                "vol_ser": "",
                "dsntype": "",
                "dummy": False,
                "sysout": "",
            },
        ],
        "default_sysin": (
            "  SORT FIELDS=(1,10,CH,A)\n"
            "  SUM FIELDS=NONE"
        ),
    },
    "IEBCOPY": {
        "name": "IEBCOPY",
        "title": "IEBCOPY — PDS / PDSE Copy & Compress",
        "category": "Dataset Copy",
        "description": "Copies selected or all members between Partitioned Datasets (PDS/PDSE), compresses PDS in-place, or unloads/loads PDS.",
        "template": "iebcopy.jcl.tpl",
        "default_step_name": "PDSCPY10",
        "default_dds": [
            {
                "dd_name": "SYSUT1",
                "dsn": "PROD.SOURCE.COPYBOOK.PDS",
                "disp_status": "SHR",
                "disp_normal": "",
                "disp_abnormal": "",
                "include_space": False,
                "space_unit": "TRK",
                "space_pri": "10",
                "space_sec": "5",
                "space_dir": "20",
                "include_dcb": False,
                "recfm": "FB",
                "lrecl": "80",
                "blksize": "0",
                "unit": "",
                "vol_ser": "",
                "dsntype": "",
                "dummy": False,
                "sysout": "",
            },
            {
                "dd_name": "SYSUT2",
                "dsn": "PROD.BACKUP.COPYBOOK.PDS",
                "disp_status": "NEW",
                "disp_normal": "CATLG",
                "disp_abnormal": "DELETE",
                "include_space": True,
                "space_unit": "CYL",
                "space_pri": "10",
                "space_sec": "5",
                "space_dir": "45",
                "include_dcb": True,
                "recfm": "FB",
                "lrecl": "80",
                "blksize": "0",
                "unit": "SYSDA",
                "vol_ser": "",
                "dsntype": "PDS",
                "dummy": False,
                "sysout": "",
            },
        ],
        "default_sysin": "  COPY OUTDD=SYSUT2,INDD=SYSUT1",
    },
    "IKJEFT01": {
        "name": "IKJEFT01",
        "title": "IKJEFT01 — TSO Batch / DB2 Program Runner",
        "category": "TSO & DB2",
        "description": "Executes TSO commands, REXX execs, or DB2 COBOL batch programs using DSN SYSTEM(DB2P) and RUN PROGRAM(...).",
        "template": "ikjeft01.jcl.tpl",
        "default_step_name": "TSODB210",
        "default_dds": [
            {
                "dd_name": "STEPLIB",
                "dsn": "PROD.DB2.LOADLIB",
                "disp_status": "SHR",
                "disp_normal": "",
                "disp_abnormal": "",
                "include_space": False,
                "space_unit": "TRK",
                "space_pri": "10",
                "space_sec": "5",
                "space_dir": "0",
                "include_dcb": False,
                "recfm": "FB",
                "lrecl": "80",
                "blksize": "0",
                "unit": "",
                "vol_ser": "",
                "dsntype": "",
                "dummy": False,
                "sysout": "",
            }
        ],
        "default_sysin": (
            "  DSN SYSTEM(DB2P)\n"
            "  RUN PROGRAM(COBDB2PG) PLAN(PRODPLAN) -\n"
            "      LIB('PROD.APPL.LOADLIB')\n"
            "  END"
        ),
    },
    "IEBCOMPR": {
        "name": "IEBCOMPR",
        "title": "IEBCOMPR — Compare Sequential or PDS Datasets",
        "category": "Dataset Verification",
        "description": "Compares two sequential or partitioned datasets record-by-record to verify data integrity.",
        "template": "iebcompr.jcl.tpl",
        "default_step_name": "COMP010",
        "default_dds": [
            {
                "dd_name": "SYSUT1",
                "dsn": "PROD.BASE.DATA.FILE",
                "disp_status": "SHR",
                "disp_normal": "",
                "disp_abnormal": "",
                "include_space": False,
                "space_unit": "TRK",
                "space_pri": "10",
                "space_sec": "5",
                "space_dir": "0",
                "include_dcb": False,
                "recfm": "FB",
                "lrecl": "80",
                "blksize": "0",
                "unit": "",
                "vol_ser": "",
                "dsntype": "",
                "dummy": False,
                "sysout": "",
            },
            {
                "dd_name": "SYSUT2",
                "dsn": "PROD.NEW.DATA.FILE",
                "disp_status": "SHR",
                "disp_normal": "",
                "disp_abnormal": "",
                "include_space": False,
                "space_unit": "TRK",
                "space_pri": "10",
                "space_sec": "5",
                "space_dir": "0",
                "include_dcb": False,
                "recfm": "FB",
                "lrecl": "80",
                "blksize": "0",
                "unit": "",
                "vol_ser": "",
                "dsntype": "",
                "dummy": False,
                "sysout": "",
            },
        ],
        "default_sysin": "  COMPARE TYPORG=PS",
    },
    "IEBUPDTE": {
        "name": "IEBUPDTE",
        "title": "IEBUPDTE — Create / Update PDS Members",
        "category": "PDS Maintenance",
        "description": "Adds, replaces, or updates members inside a Partitioned Dataset (PDS) using ./ ADD and ./ CHANGE control cards.",
        "template": "iebupdte.jcl.tpl",
        "default_step_name": "UPDT010",
        "default_dds": [
            {
                "dd_name": "SYSUT1",
                "dsn": "PROD.SOURCE.JCL.PDS",
                "disp_status": "SHR",
                "disp_normal": "",
                "disp_abnormal": "",
                "include_space": False,
                "space_unit": "TRK",
                "space_pri": "10",
                "space_sec": "5",
                "space_dir": "0",
                "include_dcb": False,
                "recfm": "FB",
                "lrecl": "80",
                "blksize": "0",
                "unit": "",
                "vol_ser": "",
                "dsntype": "",
                "dummy": False,
                "sysout": "",
            },
            {
                "dd_name": "SYSUT2",
                "dsn": "PROD.SOURCE.JCL.PDS",
                "disp_status": "SHR",
                "disp_normal": "",
                "disp_abnormal": "",
                "include_space": False,
                "space_unit": "TRK",
                "space_pri": "10",
                "space_sec": "5",
                "space_dir": "0",
                "include_dcb": False,
                "recfm": "FB",
                "lrecl": "80",
                "blksize": "0",
                "unit": "",
                "vol_ser": "",
                "dsntype": "",
                "dummy": False,
                "sysout": "",
            },
        ],
        "default_sysin": (
            "./ ADD NAME=NEWMEM01,LIST=ALL\n"
            "//* SAMPLE MEMBER CONTENT ADDED VIA IEBUPDTE\n"
            "./ ENDUP"
        ),
    },
    "ICEGENER": {
        "name": "ICEGENER",
        "title": "ICEGENER — High-Speed DFSORT Copy Replacement",
        "category": "Dataset Copy",
        "description": "Drop-in faster replacement for IEBGENER powered by DFSORT for copying sequential files.",
        "template": "icegener.jcl.tpl",
        "default_step_name": "FASTCP10",
        "default_dds": [
            {
                "dd_name": "SYSUT1",
                "dsn": "PROD.LARGE.INPUT.FILE",
                "disp_status": "SHR",
                "disp_normal": "",
                "disp_abnormal": "",
                "include_space": False,
                "space_unit": "TRK",
                "space_pri": "10",
                "space_sec": "5",
                "space_dir": "0",
                "include_dcb": False,
                "recfm": "FB",
                "lrecl": "80",
                "blksize": "0",
                "unit": "",
                "vol_ser": "",
                "dsntype": "",
                "dummy": False,
                "sysout": "",
            },
            {
                "dd_name": "SYSUT2",
                "dsn": "PROD.LARGE.OUTPUT.FILE",
                "disp_status": "NEW",
                "disp_normal": "CATLG",
                "disp_abnormal": "DELETE",
                "include_space": True,
                "space_unit": "CYL",
                "space_pri": "50",
                "space_sec": "25",
                "space_dir": "0",
                "include_dcb": True,
                "recfm": "FB",
                "lrecl": "80",
                "blksize": "0",
                "unit": "SYSDA",
                "vol_ser": "",
                "dsntype": "",
                "dummy": False,
                "sysout": "",
            },
        ],
        "default_sysin": "DUMMY",
    },
    "CUSTOM": {
        "name": "CUSTOM",
        "title": "CUSTOM PGM — User COBOL / Assembler Program",
        "category": "Application Execution",
        "description": "Execute any custom batch program (PGM=yourprog) with STEPLIB, PARM, custom DD statements, and SYSIN.",
        "template": "custom_pgm.jcl.tpl",
        "default_step_name": "RUNPGM10",
        "default_dds": [
            {
                "dd_name": "INFILE",
                "dsn": "PROD.APPL.TRANS.INPUT",
                "disp_status": "SHR",
                "disp_normal": "",
                "disp_abnormal": "",
                "include_space": False,
                "space_unit": "TRK",
                "space_pri": "10",
                "space_sec": "5",
                "space_dir": "0",
                "include_dcb": False,
                "recfm": "FB",
                "lrecl": "80",
                "blksize": "0",
                "unit": "",
                "vol_ser": "",
                "dsntype": "",
                "dummy": False,
                "sysout": "",
            },
            {
                "dd_name": "OUTFILE",
                "dsn": "PROD.APPL.REPORT.OUTPUT",
                "disp_status": "NEW",
                "disp_normal": "CATLG",
                "disp_abnormal": "DELETE",
                "include_space": True,
                "space_unit": "CYL",
                "space_pri": "10",
                "space_sec": "5",
                "space_dir": "0",
                "include_dcb": True,
                "recfm": "FB",
                "lrecl": "133",
                "blksize": "0",
                "unit": "SYSDA",
                "vol_ser": "",
                "dsntype": "",
                "dummy": False,
                "sysout": "",
            },
        ],
        "default_sysin": "2026-10-14,BATCH_MODE=FULL",
    },
}


def sanitize_jcl_identifier(value: str, default: str = "MYJOB01", max_len: int = 8) -> str:
    """Sanitize a JCL label (Job name, Step name, DD name) to valid uppercase 1-8 characters."""
    if not value:
        return default
    cleaned = re.sub(r"[^A-Z0-9@#$]", "", str(value).upper())
    if not cleaned:
        return default
    if cleaned[0].isdigit():
        cleaned = "J" + cleaned
    return cleaned[:max_len]


def sanitize_dsn(dsn: str) -> str:
    """Clean and uppercase a dataset name while allowing GDG (+1), member (MEM), and temp &&DSN."""
    if not dsn:
        return "PROD.SAMPLE.DATASET"
    return str(dsn).strip().upper()


def load_template(template_filename: str) -> Template:
    """Load a `.jcl.tpl` file from `jcl_templates/`."""
    path = os.path.join(TEMPLATE_DIR, template_filename)
    with open(path, "r", encoding="utf-8") as f:
        return Template(f.read())


def wrap_jcl_parameters(prefix: str, params: List[str], cont_indent: str = "//             ") -> str:
    """
    Join JCL comma-separated parameters onto lines that never exceed column 71.
    If a parameter would push the line past column 71, wrap onto a continuation line.
    """
    if not params:
        return prefix.rstrip()

    lines: List[str] = []
    current_line = prefix

    for idx, param in enumerate(params):
        is_last = idx == len(params) - 1
        suffix = "" if is_last else ","
        candidate = f"{current_line}{param}{suffix}"

        # Column 71 is the max code column in JCL (1-indexed -> length <= 71)
        if len(candidate) <= 71 or current_line == prefix and len(prefix) + len(param) > 71:
            current_line = candidate
        else:
            # Ensure previous line ends with a comma before continuation
            if not current_line.endswith(","):
                current_line += ","
            lines.append(current_line)
            current_line = f"{cont_indent}{param}{suffix}"

    lines.append(current_line)
    return "\n".join(lines)


def build_job_card(job_config: Dict[str, Any]) -> str:
    """Render the Job Card using `job_card.jcl.tpl` and enabled toggle parameters."""
    job_name = sanitize_jcl_identifier(job_config.get("job_name", "JCLGEN01"), "JCLGEN01", 8)
    job_desc = str(job_config.get("job_desc", "GENERATED BY Z/OS JCL GENERATOR")).upper()[:50]

    positional_and_keyword_params: List[str] = []

    # 1. Job Accounting Info toggle
    use_acct = bool(job_config.get("use_acct", True))
    acct_info = str(job_config.get("acct_info", "ACCT001,DEPT10")).strip()

    # 2. Programmer Name toggle
    use_pgmr = bool(job_config.get("use_pgmr", True))
    pgmr_name = str(job_config.get("pgmr_name", "MAINFRAME DEV")).strip().replace("'", "")

    if use_acct and acct_info:
        # Wrap in parens if comma or not already wrapped
        if not (acct_info.startswith("(") and acct_info.endswith(")")):
            acct_str = f"({acct_info.upper()})"
        else:
            acct_str = acct_info.upper()
        positional_and_keyword_params.append(acct_str)
    elif use_pgmr and pgmr_name:
        # If accounting info is omitted but programmer name is present, add a leading comma placeholder
        positional_and_keyword_params.append("")

    if use_pgmr and pgmr_name:
        positional_and_keyword_params.append(f"'{pgmr_name.upper()[:20]}'")

    # Keyword parameters (each controlled by its toggle)
    if job_config.get("use_class", True):
        job_class = str(job_config.get("job_class", "A")).strip().upper()[:1] or "A"
        positional_and_keyword_params.append(f"CLASS={job_class}")

    if job_config.get("use_msgclass", True):
        msgclass = str(job_config.get("msgclass", "X")).strip().upper()[:1] or "X"
        positional_and_keyword_params.append(f"MSGCLASS={msgclass}")

    if job_config.get("use_msglevel", True):
        msglevel = str(job_config.get("msglevel", "(1,1)")).strip()
        positional_and_keyword_params.append(f"MSGLEVEL={msglevel}")

    if job_config.get("use_notify", True):
        notify = str(job_config.get("notify", "&SYSUID")).strip().upper()
        positional_and_keyword_params.append(f"NOTIFY={notify}")

    if job_config.get("use_region", False):
        region = str(job_config.get("region", "0M")).strip().upper()
        positional_and_keyword_params.append(f"REGION={region}")

    if job_config.get("use_time", False):
        time_val = str(job_config.get("time_val", "(0,30)")).strip().upper()
        positional_and_keyword_params.append(f"TIME={time_val}")

    if job_config.get("use_typrun", False):
        typrun = str(job_config.get("typrun", "SCAN")).strip().upper()
        positional_and_keyword_params.append(f"TYPRUN={typrun}")

    if job_config.get("use_prty", False):
        prty = str(job_config.get("prty", "10")).strip()
        positional_and_keyword_params.append(f"PRTY={prty}")

    if job_config.get("use_restart", False):
        restart = sanitize_jcl_identifier(job_config.get("restart", "STEP010"), "STEP010", 8)
        positional_and_keyword_params.append(f"RESTART={restart}")

    if not positional_and_keyword_params:
        positional_and_keyword_params.append("CLASS=A,MSGCLASS=X")

    # Format job card lines with column-71 continuation
    prefix = f"//{job_name:<8} JOB "
    cont_indent = "//             "

    # Handle case where first item is empty string (omitted accounting info before programmer name)
    if len(positional_and_keyword_params) >= 2 and positional_and_keyword_params[0] == "":
        first_real = "," + positional_and_keyword_params[1]
        clean_params = [first_real] + positional_and_keyword_params[2:]
    else:
        clean_params = positional_and_keyword_params

    wrapped_job_line = wrap_jcl_parameters(prefix, clean_params, cont_indent)
    # Extract everything after `//{job_name} JOB ` for the template placeholder
    job_params_rendered = wrapped_job_line[len(f"//{job_name} JOB ") :]
    # Normalize first line spacing
    first_line_prefix = f"//{job_name} JOB "
    if wrapped_job_line.startswith(prefix):
        job_params_rendered = wrapped_job_line[len(prefix) :]

    jcllib_line = ""
    if job_config.get("use_jcllib", False):
        jcllib_dsn = sanitize_dsn(job_config.get("jcllib_dsn", "PROD.PROCLIB"))
        jcllib_prefix = "//MYLIBS   JCLLIB "
        jcllib_wrapped = wrap_jcl_parameters(jcllib_prefix, [f"ORDER=({jcllib_dsn})"], "//             ")
        jcllib_line = f"\n{jcllib_wrapped}"

    tpl = load_template("job_card.jcl.tpl")
    rendered_job = tpl.safe_substitute(
        JOB_NAME=job_name,
        JOB_NAME_PAD8=f"{job_name:<8}",
        JOB_NAME_PAD=f"{job_name:<52}",
        JOB_PARAMS=job_params_rendered,
        JOB_DESC=f"{job_desc:<52}",
        TIMESTAMP=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<52}",
        JCLLIB_LINE=jcllib_line,
    )
    return rendered_job.rstrip("\n") + "\n"


def format_dd_statement(dd: Dict[str, Any]) -> str:
    """
    Format a single DD statement with strict z/OS positioning:
    - Cols 1-2 : //
    - Cols 3-10: DD Name (1-8 chars, left-aligned, padded to 8)
    - Col 11   : Blank
    - Cols 12-13: DD
    - Cols 14-15: Blanks
    - Col 16+  : Operands (and continuation lines start at Col 16, within Cols 4-16 rule)
    """
    dd_name = sanitize_jcl_identifier(dd.get("dd_name", "DD1"), "DD1", 8)
    prefix = f"//{dd_name:<8} DD  "
    cont_indent = "//             "

    if dd.get("dummy", False):
        return f"{prefix}DUMMY"

    sysout_val = str(dd.get("sysout", "")).strip().upper()
    if sysout_val:
        return f"{prefix}SYSOUT={sysout_val}"

    params: List[str] = []

    dsn = sanitize_dsn(dd.get("dsn", ""))
    if dsn:
        params.append(f"DSN={dsn}")

    # DISP=(status,normal,abnormal)
    disp_status = str(dd.get("disp_status", "SHR")).strip().upper()
    disp_normal = str(dd.get("disp_normal", "")).strip().upper()
    disp_abnormal = str(dd.get("disp_abnormal", "")).strip().upper()

    if disp_status:
        if disp_normal and disp_abnormal:
            params.append(f"DISP=({disp_status},{disp_normal},{disp_abnormal})")
        elif disp_normal:
            params.append(f"DISP=({disp_status},{disp_normal})")
        else:
            params.append(f"DISP={disp_status}")

    # UNIT & VOL=SER
    unit = str(dd.get("unit", "")).strip().upper()
    if unit and (disp_status in ("NEW", "MOD") or dd.get("include_space", False)):
        params.append(f"UNIT={unit}")

    vol_ser = str(dd.get("vol_ser", "")).strip().upper()
    if vol_ser:
        params.append(f"VOL=SER={vol_ser}")

    # SPACE=(unit,(pri,sec,dir),RLSE)
    if dd.get("include_space", False):
        space_unit = str(dd.get("space_unit", "CYL")).strip().upper() or "CYL"
        pri = str(dd.get("space_pri", "10")).strip() or "10"
        sec = str(dd.get("space_sec", "5")).strip() or "0"
        directory = str(dd.get("space_dir", "0")).strip() or "0"
        rlse = ",RLSE" if dd.get("space_rlse", True) else ""
        if directory and directory != "0":
            params.append(f"SPACE=({space_unit},({pri},{sec},{directory}){rlse})")
        else:
            params.append(f"SPACE=({space_unit},({pri},{sec}){rlse})")

    # DCB=(RECFM=..,LRECL=..,BLKSIZE=..)
    if dd.get("include_dcb", False):
        dcb_parts: List[str] = []
        recfm = str(dd.get("recfm", "FB")).strip().upper()
        lrecl = str(dd.get("lrecl", "80")).strip()
        blksize = str(dd.get("blksize", "0")).strip()
        if recfm:
            dcb_parts.append(f"RECFM={recfm}")
        if lrecl:
            dcb_parts.append(f"LRECL={lrecl}")
        if blksize != "":
            dcb_parts.append(f"BLKSIZE={blksize}")
        if dcb_parts:
            params.append(f"DCB=({','.join(dcb_parts)})")

    dsntype = str(dd.get("dsntype", "")).strip().upper()
    if dsntype:
        params.append(f"DSNTYPE={dsntype}")

    return wrap_jcl_parameters(prefix, params, cont_indent)


def build_step_jcl(step: Dict[str, Any], step_index: int = 1) -> str:
    """Render a single step from its utility template, DD list, COND parameter, and IF/THEN/ELSE wrapper."""
    utility = str(step.get("utility", "IEFBR14")).upper()
    if utility not in UTILITY_METADATA:
        utility = "IEFBR14"

    meta = UTILITY_METADATA[utility]
    default_step = f"STEP{step_index * 10:03d}"
    step_name = sanitize_jcl_identifier(step.get("step_name", meta["default_step_name"]), default_step, 8)
    sysout_class = str(step.get("sysout_class", "*")).strip().upper() or "*"
    sysprint_dd = sanitize_jcl_identifier(step.get("sysprint_dd", "SYSPRINT"), "SYSPRINT", 8)
    sysin_dd = sanitize_jcl_identifier(step.get("sysin_dd", "SYSIN"), "SYSIN", 8)

    # Custom program / utility specifics for EXEC statement
    program_name = sanitize_jcl_identifier(step.get("program_name", "MYCOBOL"), "MYCOBOL", 8)
    parm_val = str(step.get("parm", "")).strip().replace("'", "")
    updte_parm = str(step.get("updte_parm", "NEW")).strip().upper() or "NEW"

    exec_params: List[str] = []
    if utility == "CUSTOM":
        exec_params.append(f"PGM={program_name}")
        if parm_val:
            exec_params.append(f"PARM='{parm_val[:42]}'")
    elif utility == "IKJEFT01":
        exec_params.append("PGM=IKJEFT01")
        exec_params.append("DYNAMNBR=20")
    elif utility == "IEBUPDTE":
        exec_params.append("PGM=IEBUPDTE")
        exec_params.append(f"PARM={updte_parm}")
    else:
        exec_params.append(f"PGM={utility}")

    # EXEC-level COND= parameter
    cond_param = ""
    if step.get("use_cond", False):
        cond_type = str(step.get("cond_type", "CODE")).upper()
        if cond_type in ("EVEN", "ONLY"):
            cond_token = f"COND={cond_type}"
        else:
            cond_rc = str(step.get("cond_rc", "4")).strip() or "0"
            cond_op = str(step.get("cond_op", "LT")).strip().upper() or "LT"
            cond_step = str(step.get("cond_step", "")).strip().upper()
            if cond_step:
                cond_step_clean = sanitize_jcl_identifier(cond_step, "", 8)
                cond_token = f"COND=({cond_rc},{cond_op},{cond_step_clean})"
            else:
                cond_token = f"COND=({cond_rc},{cond_op})"
        exec_params.append(cond_token)
        cond_param = f",{cond_token}"

    # Build wrapped EXEC statement:
    # Cols 1-2: //, Cols 3-10: step_name:<8, Col 11: space, Cols 12-15: EXEC, Col 16: space
    # Continuation lines start at Col 16 ("//             ")
    exec_prefix = f"//{step_name:<8} EXEC "
    exec_statement = wrap_jcl_parameters(exec_prefix, exec_params, "//             ")

    # Format DD statements
    dds = step.get("dds", meta["default_dds"])
    dd_lines: List[str] = []
    for dd in dds:
        dd_lines.append(format_dd_statement(dd))
    dd_statements = ("\n".join(dd_lines) + "\n") if dd_lines else ""

    # Format SYSIN content (ensure no line exceeds 71 chars)
    sysin_raw = str(step.get("sysin_cards", meta["default_sysin"])).rstrip()
    if sysin_raw.upper() == "DUMMY" or not sysin_raw:
        sysin_content = "DUMMY\n"
        sysin_cards = ""
        sysin_block = f"//{sysin_dd:<8} DD  DUMMY\n"
    else:
        cleaned_sysin_lines = [
            ln[:71] for ln in sysin_raw.splitlines() if ln.strip() != ""
        ]
        sysin_cards = "\n".join(cleaned_sysin_lines)
        sysin_content = f"*\n{sysin_cards}\n/*"
        sysin_block = f"//{sysin_dd:<8} DD  *\n{sysin_cards}\n/*\n"

    # IF / THEN / ELSE / ENDIF conditional block around this step
    if_start = ""
    if_else_block = ""
    if_end = ""
    if step.get("use_if_else", False):
        if_label = sanitize_jcl_identifier(step.get("if_label", f"IF{step_index:02d}"), f"IF{step_index:02d}", 8)
        if_condition = str(step.get("if_condition", "RC = 0")).strip().upper()[:45] or "RC = 0"
        if_start = f"//{if_label:<8} IF ({if_condition}) THEN\n"

        if step.get("include_else", False):
            else_step_name = sanitize_jcl_identifier(
                step.get("else_step_name", f"{step_name[:6]}EL"), f"ELSE{step_index:02d}", 8
            )
            else_pgm = sanitize_jcl_identifier(step.get("else_pgm", "IEFBR14"), "IEFBR14", 8)
            else_comment = str(step.get("else_comment", "FALLBACK STEP ON ELSE CONDITION")).upper()[:56]
            else_dd_dsn = str(step.get("else_dd_dsn", "")).strip().upper()
            else_dd_line = ""
            if else_dd_dsn:
                else_dd_line = format_dd_statement(
                    {"dd_name": "ERRDD", "dsn": else_dd_dsn, "disp_status": "SHR"}
                ) + "\n"
            if_else_block = (
                f"//{if_label:<8} ELSE\n"
                f"//*        {else_comment}\n"
                f"//{else_step_name:<8} EXEC PGM={else_pgm}\n"
                f"{else_dd_line}"
            )
        if_end = f"//{if_label:<8} ENDIF\n"

    steplib_dsn = str(step.get("steplib_dsn", "")).strip().upper()
    steplib_block = ""
    if steplib_dsn:
        steplib_block = format_dd_statement(
            {"dd_name": "STEPLIB", "dsn": steplib_dsn, "disp_status": "SHR"}
        ) + "\n"

    parm_string = f",PARM='{parm_val[:42]}'" if parm_val else ""

    tpl = load_template(meta["template"])
    rendered = tpl.safe_substitute(
        STEP_NAME=f"{step_name:<8}",
        EXEC_STATEMENT=exec_statement,
        COND_PARAM=cond_param,
        SYSPRINT_DD=f"{sysprint_dd:<8}",
        SYSIN_DD=f"{sysin_dd:<8}",
        SYSOUT_CLASS=sysout_class,
        DD_STATEMENTS=dd_statements,
        SYSIN_CONTENT=sysin_content.rstrip("\n"),
        SYSIN_CARDS=sysin_cards,
        SYSIN_BLOCK=sysin_block,
        IF_START=if_start,
        IF_ELSE_BLOCK=if_else_block,
        IF_END=if_end,
        PROGRAM_NAME=program_name,
        PROGRAM_NAME_PAD=f"{program_name:<8}",
        PARM_STRING=parm_string,
        STEPLIB_BLOCK=steplib_block,
        UPDTE_PARM=updte_parm,
    )
    return rendered.rstrip() + "\n"


def validate_strict_jcl(jcl_text: str) -> List[str]:
    """
    Strictly validate IBM z/OS JCL positioning and syntax rules:
    1. No blank/empty lines anywhere in the JCL deck.
    2. Every line must be <= 71 characters (Columns 1-71; Col 72 is continuation, 73-80 sequence).
    3. Outside instream data (DD * / DD DATA ... /*), every line must begin with '//' or '//*'.
    4. Name field (if present) must start strictly at Column 3, be 1-8 chars [A-Z@#$][A-Z0-9@#$]*,
       padded with spaces through Column 10, with Column 11 blank.
    5. Operation field (JOB, EXEC, DD, JCLLIB, IF, ELSE, ENDIF) must start strictly at Column 12.
    6. Continuation lines (following a line ending with ',') must have '// ' in Columns 1-3 and
       begin their continued operand in Columns 4-16 (never Column 17+).
    """
    warnings: List[str] = []
    lines = jcl_text.splitlines()
    in_instream_mode = ""  # "" | "*" | "DATA"
    expecting_continuation = False

    valid_ops = {"JOB", "EXEC", "DD", "JCLLIB", "IF", "ELSE", "ENDIF"}

    for line_no, line in enumerate(lines, start=1):
        if len(line) == 0:
            warnings.append(f"Line {line_no}: Blank line is invalid in z/OS JCL (use //* for spacer comments).")
            continue

        if len(line) > 71:
            warnings.append(
                f"Line {line_no}: Exceeds Column 71 ({len(line)} cols): {line[:28]}..."
            )

        if in_instream_mode:
            if line.startswith("/*"):
                in_instream_mode = ""
                continue
            if in_instream_mode == "*" and line.startswith("//") and not line.startswith("//*"):
                in_instream_mode = ""
            else:
                continue

        if line.startswith("//*"):
            continue

        if line == "//":
            if expecting_continuation:
                warnings.append(f"Line {line_no}: Null statement '//' found when continuation was expected.")
            continue

        if not line.startswith("//"):
            warnings.append(f"Line {line_no}: JCL statement must start with '//' in Columns 1-2.")
            continue

        if expecting_continuation:
            # Must start with '// ' in cols 1-3, and first non-blank in cols 4-16 (0-indexed 3..15)
            if len(line) < 4 or line[2] != " ":
                warnings.append(f"Line {line_no}: Continuation line must have a blank in Column 3.")
            else:
                rest = line[2:]
                first_non_blank_col = 3 + (len(rest) - len(rest.lstrip(" ")))
                if first_non_blank_col < 4 or first_non_blank_col > 16:
                    warnings.append(
                        f"Line {line_no}: Continuation operand starts at Column {first_non_blank_col} "
                        f"(must start between Columns 4 and 16)."
                    )
            expecting_continuation = line.rstrip().endswith(",")
            continue

        # Standard JCL statement (not a continuation line)
        if len(line) < 12:
            warnings.append(f"Line {line_no}: Statement too short to contain Operation at Column 12.")
            continue

        name_field = line[2:10]
        col11 = line[10]
        if name_field.strip():
            if line[2] == " ":
                warnings.append(f"Line {line_no}: Name field '{name_field.strip()}' must start at Column 3.")
            label = name_field.rstrip(" ")
            if " " in label or not re.match(r"^[A-Z@#$][A-Z0-9@#$]{0,7}$", label):
                warnings.append(f"Line {line_no}: Invalid JCL label '{label}' in Columns 3-10.")

        if col11 != " ":
            warnings.append(f"Line {line_no}: Column 11 must be a blank space separating Name and Operation.")

        after_col12 = line[11:]
        parts = after_col12.split(None, 1)
        op = parts[0] if parts else ""
        if op not in valid_ops or after_col12[0] == " ":
            warnings.append(
                f"Line {line_no}: Operation '{op}' must begin strictly at Column 12."
            )

        # Check if this DD statement starts instream data (DD * or DD DATA)
        if op == "DD" and len(parts) > 1:
            operand_str = parts[1].strip()
            if operand_str == "*" or operand_str.startswith("* "):
                in_instream_mode = "*"
            elif operand_str == "DATA" or operand_str.startswith("DATA "):
                in_instream_mode = "DATA"

        expecting_continuation = line.rstrip().endswith(",")

    return warnings


def generate_full_jcl(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate complete JCL from job_config and steps (supports single active step or multi-step list).
    Performs strict z/OS JCL column positioning and continuation validation.
    """
    job_config = payload.get("job_config", {})
    steps = payload.get("steps", [])
    if not steps and "current_step" in payload:
        steps = [payload["current_step"]]

    job_card_str = build_job_card(job_config)
    step_blocks: List[str] = []

    for idx, step in enumerate(steps, start=1):
        step_blocks.append(build_step_jcl(step, step_index=idx))

    # Join Job Card and Steps using '//*' comment lines (never empty lines)
    full_jcl = job_card_str + "//*\n" + "//*\n".join(step_blocks) + "//\n"

    warnings = validate_strict_jcl(full_jcl)
    lines = full_jcl.splitlines()

    file_name = str(job_config.get("file_name", "")).strip()
    if not file_name:
        job_name = sanitize_jcl_identifier(job_config.get("job_name", "JCLGEN01"), "JCLGEN01", 8)
        file_name = f"{job_name.lower()}.jcl"
    elif not file_name.lower().endswith((".jcl", ".txt", ".cntl")):
        file_name += ".jcl"

    return {
        "jcl": full_jcl,
        "file_name": file_name,
        "line_count": len(lines),
        "step_count": len(steps),
        "warnings": warnings,
    }


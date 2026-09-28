#!/usr/bin/env python3
"""Prepare private inputs and execute one bounded native Exomiser analysis."""
import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def hpo_terms(text):
    terms = [line.strip() for line in text.splitlines()
             if line.strip() and not line.lstrip().startswith('#')]
    if not terms or any(not re.fullmatch(r'HP:[0-9]{7}', term) for term in terms):
        raise ValueError('Expected nonempty source-grounded HPO identifiers')
    return sorted(set(terms))


def physical_memory():
    if sys.platform == 'darwin':
        return int(subprocess.check_output(['sysctl', '-n', 'hw.memsize'], text=True))
    return os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')


def tree_rss(pid):
    lines = subprocess.check_output(['ps', '-axo', 'pid=,ppid=,rss='], text=True).splitlines()
    processes = [tuple(map(int, line.split())) for line in lines if line.strip()]
    members = {pid}
    while True:
        children = {p for p, parent, _ in processes if parent in members}
        new = members | children
        if new == members:
            return sum(rss * 1024 for p, _, rss in processes if p in members)
        members = new


def output_size(root):
    return sum(p.stat().st_size for p in root.rglob('*') if p.is_file())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--vcf', type=Path, required=True)
    p.add_argument('--phenotypes', type=Path, required=True, help='Private text file, one HPO ID per line')
    p.add_argument('--exomiser-home', type=Path, required=True)
    p.add_argument('--java', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--prepare-only', action='store_true')
    args = p.parse_args()
    import pysam
    vcf_path = args.vcf.resolve(strict=True)
    home = args.exomiser_home.resolve(strict=True)
    java = args.java.resolve(strict=True)
    jar = home / 'exomiser-cli-15.1.0.jar'
    if not jar.is_file() or not (home / 'data/2602_hg38').is_dir() or not (home / 'data/2602_phenotype').is_dir():
        p.error('Expected Exomiser 15.1.0 and both release 2602 databases')
    version = subprocess.check_output([str(java), '-version'], stderr=subprocess.STDOUT, text=True)
    if not re.search(r'version "21[.\"]', version):
        p.error('This reproduced environment requires Java 21')
    try:
        terms = hpo_terms(args.phenotypes.read_text())
    except ValueError as exc:
        p.error(str(exc))
    with pysam.VariantFile(str(vcf_path)) as vcf:
        if len(vcf.header.samples) != 1:
            p.error('Expected one sample; no pedigree or de novo status is inferred')
        sample = next(iter(vcf.header.samples))
    rss_limit = min(8 * 1024**3, physical_memory() // 2)
    if rss_limit < 7 * 1024**3:
        p.error('Insufficient measured RAM for the fixed heap plus native-memory allowance')
    out = args.output.resolve()
    if out.exists():
        p.error('Use a new output directory')
    if not out.parent.is_dir() or shutil.disk_usage(out.parent).free < 30 * 1024**3:
        p.error('Parent must exist with at least 30 GiB free before launch')
    out.mkdir(mode=0o700)
    properties = out / 'application.properties'
    properties.write_text(f'exomiser.data-directory={(home / "data").as_posix()}\n'
                          'exomiser.hg38.data-version=2602\nexomiser.phenotype.data-version=2602\n'
                          'spring.cache.type=none\nlogging.level.com.zaxxer.hikari=ERROR\n')
    sample_path = out / 'sample.yml'
    # JSON is a YAML subset; strings are safely escaped, not interpolated YAML.
    sample_path.write_text(json.dumps({'id': sample, 'subject': {'id': sample},
        'phenotypicFeatures': [{'type': {'id': term}} for term in sorted(set(terms))],
        'htsFiles': [{'uri': str(vcf_path), 'htsFormat': 'VCF', 'genomeAssembly': 'GRCh38'}],
        'metaData': {'phenopacketSchemaVersion': '1.0'}}, indent=2) + '\n')
    analysis = out / 'analysis.yml'
    analysis.write_bytes((ROOT / 'config/analysis.yml').read_bytes())
    command = [str(java), f'-Dspring.config.location={properties.as_uri()}', '-Xms512m', '-Xmx5g',
               '-XX:MaxDirectMemorySize=512m', '-XX:MaxMetaspaceSize=512m', '-XX:ActiveProcessorCount=4',
               '-XX:+UseSerialGC', '-jar', str(jar), 'analyse', '--sample', str(sample_path),
               '--vcf', str(vcf_path), '--assembly', 'GRCh38', '--analysis', str(analysis),
               '--output-directory', str(out), '--output-filename', 'native-patient-e1',
               '--output-format', 'JSON,TSV_GENE,TSV_VARIANT,PARQUET']
    receipt = {'status': 'PREPARED', 'command': command, 'java_version': version.strip(),
               'rss_limit_bytes': rss_limit, 'timeout_seconds': 6600,
               'analysis_sha256': hashlib.sha256(analysis.read_bytes()).hexdigest(),
               'sample_sha256': hashlib.sha256(sample_path.read_bytes()).hexdigest()}
    receipt_path = out / 'execution_receipt.json'
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    if args.prepare_only:
        print('PREPARED: inspect private configuration before execution')
        return
    start, peak, reason, process = time.monotonic(), 0, None, None
    try:
        with (out / 'stdout.log').open('w') as stdout, (out / 'stderr.log').open('w') as stderr, (out / 'monitor.tsv').open('w') as monitor:
            monitor.write('elapsed_seconds\trss_bytes\tfree_disk_bytes\toutput_bytes\n')
            process = subprocess.Popen(command, cwd=home, stdout=stdout, stderr=stderr, start_new_session=True)
            while process.poll() is None:
                elapsed = time.monotonic() - start
                rss = tree_rss(process.pid)
                peak = max(peak, rss)
                free, size = shutil.disk_usage(out).free, output_size(out)
                monitor.write(f'{elapsed:.3f}\t{rss}\t{free}\t{size}\n')
                monitor.flush()
                if elapsed > 6600 or rss > rss_limit or free < 20 * 1024**3 or size > 10 * 1024**3:
                    raise RuntimeError('Resource/time ceiling exceeded')
                time.sleep(5)
            if process.returncode:
                raise RuntimeError(f'Exomiser exit {process.returncode}')
            paths = [out / ('native-patient-e1.' + ext) for ext in ('jsonl', 'genes.tsv', 'variants.tsv', 'parquet')]
            if any(not path.is_file() or not path.stat().st_size for path in paths):
                raise RuntimeError('Missing expected output')
            records = [json.loads(line) for line in paths[0].read_text().splitlines() if line.strip()]
            if not records or 'Exomising finished' not in (out / 'stdout.log').read_text():
                raise RuntimeError('Completion marker or parsed result missing')
            receipt.update(status='COMPLETE', genes=len(records), output_hashes={
                path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths})
    except BaseException as exc:
        reason = str(exc)
        receipt.update(status='FAILED', reason=reason)
        raise
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        receipt.update(elapsed_seconds=time.monotonic()-start, peak_observed_rss_bytes=peak,
                       exit_code=process.returncode if process else None)
        receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    print('COMPLETE: evaluate scientific results separately from execution success')


if __name__ == '__main__':
    main()

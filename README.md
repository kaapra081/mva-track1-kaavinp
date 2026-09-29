# MVA Track 1 — kaavinp

**Author: Kaavin Prasanna** · Hugging Face: `kaavinp`

I used Exomiser 15.1.0 with GRCh38/2602 resources, followed by case-specific manual disease-context review, to prioritize candidate genotype hypotheses for the MVA Hackathon 2026.

**Status:** local research submission package; not submitted and no official score measured. My primary hypothesis is an unphased BUB1B pair that includes a variant of uncertain significance. I do not claim a confirmed diagnosis, calibrated probabilities, or a validated general-purpose ranking improvement.

## Submission files

- [Ranked predictions](submission/kaavinp_exomiser15-context-review.csv)
- [Methods report (PDF)](submission/kaavinp_track1_report.pdf)
- [Methods report (Markdown)](submission/kaavinp_track1_report.md)
- Repository URL: https://github.com/kaapra081/mva-track1-kaavinp

## Reproduce my workflow

I keep gated VCF/phenotype inputs, reference sequences, Exomiser databases and full patient outputs outside this repository. Authorized participants must obtain their own inputs under the dataset terms. The CSV and report are derived submission artifacts.

Requirements: Python 3.10+, Java 21, Exomiser 15.1.0 with installed hg38/phenotype release 2602, and a compatible GRCh38 FASTA with its index. `requirements.txt` pins the Python VCF dependency used in my original analysis. No hosted annotation service is required.

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v

# hpo.txt: one source-grounded proband HPO ID per line, supplied privately.
# Use external private input locations; do not add these files to git.
python scripts/run_exomiser.py \
  --vcf /private/input.vcf.gz --phenotypes /private/hpo.txt \
  --exomiser-home /tools/exomiser-cli-15.1.0 \
  --java /tools/java21/bin/java --output /private/exomiser-run

python scripts/build_submission.py \
  --native /private/exomiser-run/native-patient-e1.jsonl \
  --output /private/reproduced.csv

python scripts/validate_submission.py /private/reproduced.csv \
  --vcf /private/input.vcf.gz --reference /private/GRCh38.fa \
  --native /private/exomiser-run/native-patient-e1.jsonl
```

The runner supports `--prepare-only` for inspecting effective configuration without starting Java. It uses a bounded single analysis (four processors, a 5-GiB heap, 110-minute timeout), checks free space and monitors process-tree RSS. Adjusting those limits requires an explicit new run configuration; a heap limit alone is not a process memory limit.

An existing native JSONL output can be used directly with the builder. My packaging verification regenerated the final CSV from the frozen native output without rerunning Exomiser. External database installation and a new full patient run were not repeated during repository assembly.

## What is automated and what I adjudicated

Exomiser performs broad coding/splice-oriented prioritization across the supplied VCF. My case-specific policy then promotes the native two-allele BUB1B recessive model with an MVA disease match, excludes the BUB1B singleton tied to a somatic colorectal-cancer annotation, and retains compatible-disease alternatives. This is an explicit, retrospective manual adjudication encoded for reproducibility—not a learned classifier or independent validation. Models lacking a native compatible disease annotation are retained in the local audit but excluded from this submission; absence of annotation does not prove a model is biologically impossible.

The code exports up to ten distinct allele-set hypotheses and canonical `chr` chromosome names. EPCR values encode my reviewed order, not posterior probabilities. Full native output is preserved locally separately from this reviewed ranking.

## Repository map

- `config/analysis.yml`: exact Exomiser analysis settings.
- `config/adjudication.json`: explicit case-specific review decisions.
- `scripts/`: portable runner, ranking/export, validator and package-check utilities.
- `tests/`: synthetic tests; no gated input fixtures.
- `submission/`: final CSV and first-person report.
- `results/`: compact validation/provenance summaries without private paths or raw genotypes.
- `docs/`: input requirements and reproducibility boundaries.

For report rendering: `pandoc submission/kaavinp_track1_report.md --from=markdown --standalone --pdf-engine=xelatex -o submission/kaavinp_track1_report.pdf`.

## Data access and acknowledgements

I used the [official gated dataset](https://huggingface.co/datasets/SageBio/mva-hackathon-2026-data). This repository does not grant access to it. See the [challenge instructions](https://huggingface.co/spaces/SageBio/rare-disease-real-kid-mva-hackathon-2026) and [data/reproduction notes](docs/DATA_AND_REPRODUCTION.md).

The report includes the organizer acknowledgement and my AI-assistance disclosure. The repository is private during preparation; the challenge's rules require a public code repository after the hackathon. No upload to the challenge has been performed by this repository workflow.

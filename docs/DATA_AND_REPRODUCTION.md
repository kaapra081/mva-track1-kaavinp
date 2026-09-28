# Data and reproduction boundaries

I acquired case inputs through the official gated challenge access process. I do not redistribute the VCF, its index, FASTQ files, clinical document, source phenotype export, full annotation output or Exomiser databases here.

## Authorized local inputs

- Single-sample GRCh38 VCF and compatible index, obtained under the challenge terms.
- Proband phenotype HPO IDs extracted from the authorized clinical source, one per line in a private text file. I used seven documented proband terms and kept family history separate. A reproducer must perform or reuse source-grounded extraction; no phenotype truth labels belong in this input.
- Compatible GRCh38 FASTA and index for exact REF checks.
- Exomiser 15.1.0, Java 21, hg38 and phenotype release 2602 databases.

The scripts identify the actual VCF sample at runtime; `PROBAND01` is the submission identifier, not an instruction to rewrite the VCF header. No trio or parental evidence is synthesized.

## Installation

Use the official [Exomiser release](https://github.com/exomiser/Exomiser/releases/tag/15.1.0) and its installation instructions. Confirm archive checksums where a publisher checksum is available, archive integrity, extraction, selected data release and database loading. A locally computed SHA-256 identifies bytes but does not independently authenticate their origin.

My original configuration did not install REMM or CADD. It is a coding/splice-oriented route, not comprehensive regulatory prioritization. Native population frequencies use the tool's units (percentage values in its frequency objects); they must not be confused with fractions. For example, AC/AN can be used to cross-check available native counts, but missing frequency/coverage remains unavailable, not verified absence.

## Three separate kinds of verification

1. **Software:** synthetic ordering, identity, invalid-input and duplicate tests. These do not measure biological accuracy.
2. **Case artifact:** exact native-model membership and indexed VCF/reference reconciliation of every exported allele. These do not establish causality, phase or mechanistic suitability.
3. **Submission:** final CSV/report consistency, deterministic CSV bytes and package hashes. An official score requires actual challenge submission; it has not been measured here.

The repository packaging pass does not rerun the patient baseline. The portable CLI runner is supplied for authorized reproduction; its complete heavy execution has not been newly tested as part of packaging. The builder and validator are exercised against the frozen native output and the actual local inputs. The original analysis log records 5,012,204 VCF records and 364 analyzed genes.

## Manual review policy

`config/adjudication.json` deliberately makes my case-specific decisions visible. The code selects the BUB1B recessive MVA-context hypothesis, excludes the somatic-colorectal BUB1B singleton, and orders remaining native compatible-disease hypotheses by native scores and stable identities. This is not a claim that the same policy is suitable for every rare-disease case. Alternative rows are hypotheses for review, not clinically reportable incidental findings.

The source-native representations of submitted alleles are retained apart from canonical chromosome aliases. No new whole-VCF normalization was performed. Missing phase and source annotation limitations remain unresolved. Shared alleles across different singleton/pair hypotheses are not treated as independent discoveries.

## Dataset citation

Sage Bionetworks. *MVA Hackathon 2026 Data* (2026). Gated dataset, official access page: https://huggingface.co/datasets/SageBio/mva-hackathon-2026-data .

This identifies the actual official access resource. An organizer-specified Synapse citation or identifier, if separately required, must be confirmed from authorized organizer materials before publication; I have not invented a DOI or accession.

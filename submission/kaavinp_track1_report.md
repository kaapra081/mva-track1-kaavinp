---
title: "MVA Track 1: Exomiser analysis and disease-context review"
author: "kaavinp"
date: "September 2026"
geometry: margin=0.8in
fontsize: 10pt
---

# Summary

I analyzed the supplied single-proband GRCh38 variant callset using Exomiser 15.1.0 and release 2602 resources. I then reviewed native genotype hypotheses in their disease and inheritance contexts and encoded my case-specific adjudication in a deterministic exporter. My leading hypothesis is the BUB1B pair chr15:40209701 T>G and chr15:40220612 T>G. The pair is unphased and includes an uncertain-significance allele; I do not claim a confirmed diagnosis or proven trans configuration.

My repository is https://github.com/kaapra081/mva-track1-kaavinp . My Hugging Face username is `kaavinp`, and my method name is `exomiser15-context-review`. No official challenge score has been measured and the package has not been submitted.

# Inputs and executed analysis

I used the authorized challenge VCF and source-grounded proband phenotype information. I retained seven documented proband HPO terms and represented family history separately. The single sequencing sample was mapped to `PROBAND01` for export without rewriting the input VCF. Raw genomic data and the clinical source document are not included in my repository.

I ran Java 21 with Exomiser 15.1.0, GRCh38 transcript/variant data and phenotype release 2602. My frozen `config/analysis.yml` records the effective settings. I used a broad eligible-gene, coding/splice-oriented analysis with `PASS_ONLY`, gene blacklist, failed-variant, allele-balance, consequence, frequency and inheritance filtering, followed by OMIM and HiPhive prioritization. The pathogenicity step retained nonpathogenic predictions for consideration (`keepNonPathogenic: true`). HiPhive included its configured human, mouse, fish and network sources. No parental genotypes or de novo status were inferred.

My configured frequency sources were UK10K and the selected gnomAD exome/genome populations. Computational sources were REVEL, MVP, AlphaMissense and SpliceAI. Native frequency values use the tool's documented units; missing records were retained as unavailable evidence rather than described as verified zero frequency. I did not claim that native Exomiser frequency fields satisfy a separate complete AC/AN/coverage model.

The input SHA-256 was `bec64c68d3ad10d05b8071d07cdf87d217013d66d3ba02e24b505035c9d42175`. The frozen native JSONL SHA-256 was `85b2f11b5150a73d294e4ce3748b4c3c7a62f9346b12e9cb5eb77cb3480c8697`.

# Observed baseline results

The completed run processed 5,012,204 VCF records into 4,962,047 single-allele variants. It retained 1,011 variants after variant filtering and analyzed 364 genes containing 589 inheritance-compatible filtered variants. The full native output contained 421 contributing genotype models.

| Sequential filter | Passed | Failed at this step |
|---|---:|---:|
| Gene blacklist | 4,933,759 | 28,288 |
| Failed-variant filter | 4,701,716 | 232,043 |
| Allele balance | 4,497,268 | 204,448 |
| Variant effect | 23,931 | 4,473,337 |
| Frequency | 1,011 | 22,920 |
| Pathogenicity | 1,011 | 0 |
| Inheritance | 589 | 422 |

The monitored successful process took approximately 80.11 seconds, with peak observed process-tree RSS of 936,720 KiB. These are measurements from this run, not a scalability benchmark. Preprocessing/startup corrections were resolved before the successful full analysis. The analysis completed once; packaging and ranking review reused its output without a new patient run.

# My disease-context adjudication

I preserved the native baseline separately from my reviewed ranking. The native BUB1B dominant singleton had combined score 0.544692 but its compatible disease annotation was “Colorectal cancer, somatic.” The native recessive pair had combined score 0.485305 and compatible MVA disease annotations, with a higher native phenotype score (0.764649 versus 0.546282). I judged the constitutional MVA context more relevant to this case than the somatic-colorectal singleton annotation.

I therefore explicitly promoted the native BUB1B recessive two-allele MVA hypothesis. This is a retrospective, case-specific manual decision, encoded in `config/adjudication.json`; it is not a trained model, an unmodified Exomiser ordering, or validation of a general ranking improvement. I excluded the BUB1B somatic-colorectal model and models without a native compatible disease annotation from my submitted shortlist. Absence of such annotation is not proof that a model is biologically impossible.

Within the remaining context groups I sorted the complete model inventory by native combined score, phenotype score, variant score, gene, mode and allele identity, and deduplicated exact allele-set hypotheses before selecting ten. I did not use JSON emission order as confidence. I assigned strictly decreasing ordinal EPCR values using `1 - (rank - 1)/11`; these values are not calibrated probabilities.

# Candidate hypotheses

| Rank | Gene | Exact GRCh38 allele(s) | EPCR |
|---:|---|---|---:|
| 1 | BUB1B | chr15:40209701 T>G; chr15:40220612 T>G | 1.000000 |
| 2 | FANCD2 | chr3:10046723 AG>A; chr3:10046725 TAAG>T | 0.909091 |
| 3 | HK1 | chr10:69315762 A>G | 0.818182 |
| 4 | LZTR1 | chr22:20996720 C>G | 0.727273 |
| 5 | SERPINA1 | chr14:94379487 CCT>C; chr14:94379492 G>GAC | 0.636364 |
| 6 | COL7A1 | chr3:48584547 C>T | 0.545455 |
| 7 | SH3BP2 | chr4:2827654 C>T | 0.454545 |
| 8 | ESR1 | chr6:151842246 A>G | 0.363636 |
| 9 | RBMX | chrX:136874347 C>G | 0.272727 |
| 10 | MBTPS1 | chr16:84070041 A>G | 0.181818 |

My leading BUB1B hypothesis combines a ClinVar pathogenic/likely-pathogenic stop-gain, p.Leu737Ter, with the rare missense p.Asn1002Lys. The native automatic classification for the latter remains uncertain significance. Computational prediction and phenotype similarity do not establish functional effect. The native phenotype annotations include MVA-relevant growth and tumor features but do not establish an exact explanation for every observation.

All alternative rows are retained research hypotheses. Native compatible-disease annotations and source quality do not constitute independent clinical interpretation of each secondary finding. I do not treat a secondary label as exemption from automated scoring. Pair rows remain unphased or incompletely phased; single-allele rows must be interpreted in their actual genotype/inheritance context rather than presumed to establish a dominant diagnosis.

# Verification and reproduction

My repository includes a portable native-analysis runner, deterministic model exporter, strict CSV validator and synthetic tests. The exporter produces canonical `chr` contigs while retaining source-native coordinates and allele representations. The validator checks schema, finite EPCR, complete pairs, duplicate allele sets, supported allele syntax, exact native-model membership and optional indexed VCF/reference evidence. I independently reconcile submitted alleles using the original genotype and reference rather than inferring correctness from membership alone. The compact repository validation receipt records the observed result of that check.

For packaging, I regenerate the CSV from the frozen native output and compare it with the reviewed artifact. Synthetic permutation and invalid-input tests establish bounded software behavior, not diagnostic sensitivity. The complete original native output stays local, with its digest recorded above. The portable full-analysis wrapper is provided for authorized reproduction; I did not rerun the heavy analysis during repository assembly.

# Limitations

- My ranking is case-specific manual adjudication of an automated baseline, not a blinded benchmark or a claim of general superiority.
- Phase, segregation, functional effect and causality remain unresolved. The leading pair includes a VUS.
- The analysis is coding/splice-oriented and does not comprehensively assess regulatory, structural, mosaic, chromosome-scale or raw-read mechanisms.
- I retain source-native allele representations and explicit contig mapping. Local reference/decoy differences limit broader reference-compatibility claims.
- The source index is older than the VCF modification time; exact submitted-allele lookups are checked independently.
- Presence of DP/GQ/AD and an explicit PASS record is technical evidence, not clinical confirmation.
- No cohort evaluation, clinical sensitivity estimate, empirically calibrated EPCR or official challenge score is claimed.

# AI assistance

I used OpenCode with OpenAI assistance for coding, workflow review and documentation. I report using ChatGPT Plus and having the ChatGPT “Improve the model for everyone” setting turned off. This states my reported account preference; it does not establish a separate API or third-party retention agreement. I treated generated suggestions as assistance rather than independent biological evidence. The workflow used local tools for variant annotation and did not require hosted patient-specific annotation queries.

# Acknowledgement

This work was made possible through the Hackathon, organized by Sage Bionetworks in partnership with the MVA Society, Hugging Face, and BEACON (The Benchmarking, Evaluation, and Assessment Consortium for Science), with prize sponsorship from AWS and Anthropic. We are deeply grateful to the child and their family who generously contributed their data and their story to advance research into this rare disease. We acknowledge their trust in making this Hackathon possible.

# References

1. Sage Bionetworks. *MVA Hackathon 2026 Data* (2026). Official gated access resource: https://huggingface.co/datasets/SageBio/mva-hackathon-2026-data .
2. Sage Bionetworks. *Rare Disease, Real Kid: MVA Hackathon 2026*. Track 1 instructions and official rules: https://huggingface.co/spaces/SageBio/rare-disease-real-kid-mva-hackathon-2026 .
3. Exomiser developers. *Exomiser 15.1.0*. Software release: https://github.com/exomiser/Exomiser/releases/tag/15.1.0 . Documentation: https://exomiser.readthedocs.io/ .
4. NCBI ClinVar. Variation 533901, BUB1B: https://www.ncbi.nlm.nih.gov/clinvar/variation/533901/ . Interpretation in my run used the recorded release 2602 resources, not an assumed current live assertion.
5. Hanks S, et al. Constitutional aneuploidy and cancer predisposition caused by biallelic mutations in BUB1B. *Nature Genetics* (2004), 36:1159–1161. https://doi.org/10.1038/ng1449 .

I cite the actual official dataset access page above. An organizer-specific Synapse citation, if additionally required, still needs confirmation from authorized organizer materials; I have not invented an accession or DOI.

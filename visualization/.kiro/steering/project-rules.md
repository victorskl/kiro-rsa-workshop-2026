---
inclusion: always
---

# Project Rules

## Charts

Always save charts as PNG files in a `charts/` folder. Never create PDF files.

## Patient Data Privacy

This project may contain patient information. Follow these rules at all times:

- Never print more than 5 raw rows of data to the console or any output.
- Never copy raw data rows into new files (e.g. no exports, no snippets, no sample files derived from the raw CSV rows).

## AWS CLI

Pass `--no-cli-pager` to every `aws` command.
Please use my visualize-dataset skill on a different CSV file in the diabetic folder
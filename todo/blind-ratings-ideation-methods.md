# Blind human ratings for the ideation-methods study

| Field | Value |
|-------|-------|
| **Date** | 2026-10-15 |
| **Author** | Arjun Raj (with Claude) |
| **Priority** | high |
| **Status** | open |
| **Category** | validation |
| **Related analyses** | analysis/ideation-methods-across-models |
| **Related data** | outputs/ideas.csv, outputs/ideas_stripped.csv |

## Description

Build a write-once blind rating sheet from the plain prompt, critique and revise, list the obvious then avoid it, and overgenerate then select, for Haiku 5.5 and Opus 5.5, on both questions (stratified by call), and have lab members rate novelty and usefulness.

## Motivation

Every quality score in the report comes from model judges; the usefulness penalties especially need checking by people who run these experiments.

## Proposed Approach

Reuse the earlier study's 03_rating_set.py pattern (write-once, content check, separate key file). About 10 ideas per prompt × model × question = 160 ideas.

## Acceptance Criteria

- [ ] Rating sheet and key written, frozen
- [ ] At least two raters
- [ ] Agreement with the Opus judge reported; headline re-tested on human scores

## Notes

Also consider a combined pipeline (overgenerate then select, then a critique-and-revise round) and adding a critique step to mycelium:ideas.

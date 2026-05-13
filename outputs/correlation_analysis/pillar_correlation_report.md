# Pillar Correlation and Relationship Exploration

This report explores within-pillar relationships across Newlands survey metrics.
Spearman correlation is used as the main relationship measure because many survey metrics are ordinal-like scores, binary fields, or harmonized survey scales. Pearson correlation is included in the CSV output as a secondary linear measure.

Relationship bands used in this report:

- Strong: absolute Spearman correlation >= 0.70
- Moderate: absolute Spearman correlation >= 0.40 and < 0.70
- Weak: absolute Spearman correlation >= 0.20 and < 0.40
- Very weak: absolute Spearman correlation < 0.20

Pairs with fewer than 30 valid paired responses are flagged as low sample size.

## Economic

Metrics in this pillar: 6

Metrics with high missingness:
- Income satisfaction: 73.86% missing
- Confidence in finding a new job: 71.29% missing

Moderate and strong relationships:
- Job satisfaction and Income satisfaction: Spearman 0.44, Pearson 0.44, valid n=270, moderate
- Job satisfaction and Confidence in finding a new job: Spearman 0.41, Pearson 0.46, valid n=268, moderate

Most independent metrics by average absolute within-pillar Spearman correlation:
- Work travel time: average abs Spearman 0.08
- Basic life skills: average abs Spearman 0.14
- Paid working hours: average abs Spearman 0.16

## Environment

Metrics in this pillar: 3

Metrics with high missingness:
- Confidence in water safety: 70.44% missing
- Optimal use of land: 70.34% missing

Moderate and strong relationships:
- Confidence in water safety and Optimal use of land: Spearman 0.50, Pearson 0.51, valid n=311, moderate
- Access to natural environment and Confidence in water safety: Spearman 0.42, Pearson 0.41, valid n=310, moderate

Most independent metrics by average absolute within-pillar Spearman correlation:
- Access to natural environment: average abs Spearman 0.37
- Optimal use of land: average abs Spearman 0.41
- Confidence in water safety: average abs Spearman 0.46

## Social

Metrics in this pillar: 15

Metrics with high missingness:
- Personal mental health: 85.08% missing

Moderate and strong relationships:
- Be yourself in NZ and Be yourself in Newlands: Spearman 0.82, Pearson 0.77, valid n=999, strong
- Life satisfaction and Personal mental health: Spearman 0.72, Pearson 0.70, valid n=157, strong
- Life satisfaction and Meaning and purpose: Spearman 0.68, Pearson 0.68, valid n=850, moderate
- Meaning and purpose and Personal mental health: Spearman 0.65, Pearson 0.64, valid n=157, moderate
- Level of control and Personal mental health: Spearman 0.61, Pearson 0.60, valid n=155, moderate
- Work-life balance and Personal mental health: Spearman 0.53, Pearson 0.53, valid n=145, moderate
- Family wellbeing and Personal mental health: Spearman 0.52, Pearson 0.48, valid n=157, moderate
- Be yourself in Newlands and Life satisfaction: Spearman 0.50, Pearson 0.47, valid n=1004, moderate
- Meaning and purpose and Family wellbeing: Spearman 0.49, Pearson 0.47, valid n=844, moderate
- Be yourself in NZ and Life satisfaction: Spearman 0.49, Pearson 0.47, valid n=1009, moderate

Most independent metrics by average absolute within-pillar Spearman correlation:
- Volunteering time: average abs Spearman 0.09
- Safety: average abs Spearman 0.10
- Leisure time: average abs Spearman 0.13

Direction notes:
- Discrimination should be interpreted carefully: Higher=more severe/problematic.
- Loneliness should be interpreted carefully: Higher=more severe/problematic.

## Cultural

Metrics in this pillar: 5

No metrics in this pillar have missingness above 50%.

Moderate and strong relationships:
- Cultural activities and Cultural knowledge: Spearman 0.46, Pearson 0.47, valid n=1031, moderate

Most independent metrics by average absolute within-pillar Spearman correlation:
- Language: average abs Spearman 0.07
- Sense of belonging: average abs Spearman 0.09
- Te Reo: average abs Spearman 0.17

## Governance

Metrics in this pillar: 7

Metrics with high missingness:
- Voted in local elections 2019: 94.20% missing
- Voted in general election 2020: 94.11% missing
- Voted in general elections 2023: 75.57% missing
- Voted in local elections 2022: 75.48% missing

Moderate and strong relationships:
- Voted in local elections 2019 and Voted in general election 2020: Spearman 0.85, Pearson 0.85, valid n=61, strong
- Trust in NZ government and Trust in local council: Spearman 0.57, Pearson 0.60, valid n=1025, moderate
- Voted in local elections 2022 and Voted in general elections 2023: Spearman 0.54, Pearson 0.54, valid n=257, moderate

Most independent metrics by average absolute within-pillar Spearman correlation:
- Trust in NZ Police: average abs Spearman 0.14
- Voted in general elections 2023: average abs Spearman 0.16
- Voted in local elections 2022: average abs Spearman 0.17

## Disaster

Metrics in this pillar: 4

Metrics with high missingness:
- Place out of Newlands disaster ready: 53.33% missing

No moderate or strong relationships met the valid sample threshold.

Most independent metrics by average absolute within-pillar Spearman correlation:
- Neighbourhood support group: average abs Spearman 0.14
- Out of Newlands during day: average abs Spearman 0.15
- Home disaster ready: average abs Spearman 0.17

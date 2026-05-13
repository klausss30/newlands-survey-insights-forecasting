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
- Income satisfaction: 61.41% missing
- Confidence in finding a new job: 60.76% missing

Moderate and strong relationships:
- Job satisfaction and Income satisfaction: Spearman 0.46, Pearson 0.48, valid n=233, moderate
- Job satisfaction and Confidence in finding a new job: Spearman 0.43, Pearson 0.49, valid n=233, moderate

Most independent metrics by average absolute within-pillar Spearman correlation:
- Work travel time: average abs Spearman 0.07
- Basic life skills: average abs Spearman 0.14
- Paid working hours: average abs Spearman 0.16

## Environment

Metrics in this pillar: 3

Metrics with high missingness:
- Confidence in water safety: 60.92% missing
- Optimal use of land: 60.76% missing

Moderate and strong relationships:
- Confidence in water safety and Optimal use of land: Spearman 0.52, Pearson 0.54, valid n=238, moderate
- Access to natural environment and Confidence in water safety: Spearman 0.41, Pearson 0.39, valid n=237, moderate

Most independent metrics by average absolute within-pillar Spearman correlation:
- Access to natural environment: average abs Spearman 0.38
- Optimal use of land: average abs Spearman 0.44
- Confidence in water safety: average abs Spearman 0.46

## Social

Metrics in this pillar: 15

Metrics with high missingness:
- Personal mental health: 80.13% missing

Moderate and strong relationships:
- Be yourself in NZ and Be yourself in Newlands: Spearman 0.83, Pearson 0.79, valid n=605, strong
- Life satisfaction and Personal mental health: Spearman 0.73, Pearson 0.70, valid n=121, strong
- Life satisfaction and Meaning and purpose: Spearman 0.71, Pearson 0.72, valid n=489, strong
- Meaning and purpose and Personal mental health: Spearman 0.64, Pearson 0.65, valid n=121, moderate
- Level of control and Personal mental health: Spearman 0.57, Pearson 0.56, valid n=120, moderate
- Work-life balance and Personal mental health: Spearman 0.53, Pearson 0.53, valid n=120, moderate
- Family wellbeing and Personal mental health: Spearman 0.50, Pearson 0.45, valid n=121, moderate
- Be yourself in Newlands and Life satisfaction: Spearman 0.50, Pearson 0.48, valid n=609, moderate
- Independence and Level of control: Spearman 0.48, Pearson 0.48, valid n=604, moderate
- Level of control and Life satisfaction: Spearman 0.48, Pearson 0.50, valid n=608, moderate

Most independent metrics by average absolute within-pillar Spearman correlation:
- Volunteering time: average abs Spearman 0.10
- Loneliness: average abs Spearman 0.11
- Safety: average abs Spearman 0.12

Direction notes:
- Discrimination should be interpreted carefully: Higher=more severe/problematic.
- Loneliness should be interpreted carefully: Higher=more severe/problematic.

## Cultural

Metrics in this pillar: 5

No metrics in this pillar have missingness above 50%.

Moderate and strong relationships:
- Cultural activities and Cultural knowledge: Spearman 0.44, Pearson 0.47, valid n=602, moderate

Most independent metrics by average absolute within-pillar Spearman correlation:
- Language: average abs Spearman 0.09
- Sense of belonging: average abs Spearman 0.11
- Te Reo: average abs Spearman 0.19

## Governance

Metrics in this pillar: 7

Metrics with high missingness:
- Voted in local elections 2019: 91.63% missing
- Voted in general election 2020: 91.63% missing
- Voted in local elections 2022: 69.13% missing
- Voted in general elections 2023: 69.13% missing

Moderate and strong relationships:
- Voted in local elections 2019 and Voted in general election 2020: Spearman 0.88, Pearson 0.88, valid n=51, strong
- Trust in NZ government and Trust in local council: Spearman 0.62, Pearson 0.63, valid n=604, moderate
- Voted in local elections 2022 and Voted in general elections 2023: Spearman 0.45, Pearson 0.45, valid n=188, moderate

Most independent metrics by average absolute within-pillar Spearman correlation:
- Trust in NZ Police: average abs Spearman 0.12
- Voted in local elections 2022: average abs Spearman 0.13
- Voted in general elections 2023: average abs Spearman 0.14

## Disaster

Metrics in this pillar: 4

No metrics in this pillar have missingness above 50%.

No moderate or strong relationships met the valid sample threshold.

Most independent metrics by average absolute within-pillar Spearman correlation:
- Neighbourhood support group: average abs Spearman 0.14
- Out of Newlands during day: average abs Spearman 0.17
- Home disaster ready: average abs Spearman 0.18

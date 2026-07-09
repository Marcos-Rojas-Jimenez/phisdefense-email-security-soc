# PhisDefense SOC & Email Security Lab

Defensive cybersecurity case study focused on email security, Blue Team monitoring and SOC-style evidence handling.

## Live Project

- Case study page: https://marcos-rojas-jimenez.github.io/phisdefense-email-security-soc/
- Interactive dashboard: https://phisdefense-email-security-soc.onrender.com

## Project Overview

PhisDefense is a practical email security and SOC monitoring lab built around a real mail security environment.

The project validates defensive controls such as SPF, DKIM, DMARC, DNSSEC, MTA-STS, TLS-RPT, STARTTLS and IMAPS TLS. It also converts technical evidence from server logs into a SOC-style dashboard.

The goal was not only to configure security controls, but to verify them through controlled tests, collect evidence, process events and present the results in a clear dashboard suitable for portfolio and technical review.

## Main Components

- Linux mail security environment
- Postfix SMTP server
- Dovecot for IMAPS TLS validation
- OpenDKIM for DKIM signing and validation
- OpenDMARC for DMARC policy evaluation and rejection
- OpenARC for ARC-related authentication chain support
- DNSSEC, SPF, DKIM, DMARC, MTA-STS and TLS-RPT
- Python and Dash SOC dashboard
- Sanitized SOC datasets for public publication

## Defensive Controls Validated

- SPF pass and fail validation
- DKIM valid, broken and absent scenarios
- DKIM selector rotation
- DMARC policy progression to p=reject
- External spoofing rejection through DMARC
- STARTTLS SMTP validation
- IMAPS TLS validation
- Open relay testing
- SMTP AUTH failure detection
- Recipient unknown events
- Lookalike domain analysis

## SOC Dashboard

The interactive dashboard visualizes processed SOC events and defensive evidence from the lab. It includes KPIs, event categories, tables, SMTP security views, spoofing analysis, timeline views and public reporting status.

The public dashboard uses sanitized data and does not expose credentials, private keys, sensitive IPs, internal paths or full server backups.

Dashboard: https://phisdefense-email-security-soc.onrender.com

## Public Dataset

The public dataset contains sanitized SOC events extracted from the project. It demonstrates the structure, categories and results of the analysis without exposing sensitive information from the original server environment.

Included datasets:

- data/bateria_pruebas.csv
- data/bateria_pruebas_soc.csv
- data/bateria_pruebas_email_threats.csv

## Key Results

- 270 total tests aggregated in the project
- 190 SOC events processed and categorized
- DMARC final policy: p=reject
- Events covering SMTP AUTH failures, recipient unknown, SPF fail, DKIM issues, STARTTLS, IMAPS TLS, open relay testing and spoofing rejection

## Privacy and Sanitization

This public version is sanitized for portfolio use. It does not include:

- Private DKIM keys
- Credentials
- .env files
- Sensitive IP addresses
- Internal server backups
- Full raw logs
- Private operational data

## Skills Demonstrated

- Email security engineering
- Blue Team validation
- SOC-style event classification
- Linux server administration
- Postfix and Dovecot configuration
- SPF, DKIM, DMARC and DNSSEC validation
- MTA-STS and TLS-RPT documentation
- Log analysis and evidence handling
- Python automation
- Dash and Plotly dashboarding
- Public project sanitization and technical documentation

## Repository Structure

```text
.
|-- app.py
|-- index.html
|-- requirements.txt
|-- render.yaml
|-- assets/
|-- data/
|-- docs/
|-- data-samples/
```

## Deployment

The case study page is published with GitHub Pages.

The interactive dashboard is deployed on Render using Dash and Gunicorn.

Render start command:

```bash
gunicorn app:server
```

## Author

Marcos Rojas Jimenez  
Cybersecurity · Blue Team · SOC · Email Security
# Arquivos para o Volume do Databricks

Copiados para `/Volumes/<catalog>/<schema>/data/input` pelo notebook `00_setup_volume`.

- `demand_*.csv` e `services_*.csv`: copias de `big_data/input`, dados **sinteticos** (`synthetic=true`).
- `official/gold_official_context.csv`: 7 indicadores extraidos do texto do relatorio
  CAVALCANTI, L; OLIVEIRA, T. *Dados Consolidados da Imigracao no Brasil 2025*. OBMigra/MJSP, 2026.
  A p.4 do relatorio permite reproduzir texto e dados com citacao da fonte; uso nao comercial.
  Cada linha traz a pagina de origem.
- `official/municipalities_sp.csv`: IBGE, API de Localidades (servicodados.ibge.gov.br), municipios de SP,
  coletado em 2026-11-14. Dado aberto do IBGE; cite o IBGE como fonte.

Nao altere um arquivo depois de ingerido: o COPY INTO lembra os arquivos ja carregados. Publique correcoes com novo nome/data.

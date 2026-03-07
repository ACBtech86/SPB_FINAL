# Migração do Projeto

**Data:** 22/02/2026 13:07:41

## Motivo da Migração

O projeto foi movido de:
```
C:\Users\AntonioBosco\OneDrive - Finvest\�rea de Trabalho\SPBCidade\SPB1\SPB Fontes Producao\BCSrvSqlMq
```

Para:
```
C:\BCSrvSqlMq
```

**Razão:** Problema de encoding com caracteres acentuados no caminho original
("Área de Trabalho") causando erro LNK1201 no Visual Studio linker.

## Arquivos Copiados

Total: 65 arquivos

## Próximos Passos

1. Testar build:
```bash
cd C:\BCSrvSqlMq
powershell -ExecutionPolicy Bypass -File build_test.ps1
```

2. Continuar com Fase 6 (migração de código)

---

**IMPORTANTE:** O diretório original em OneDrive foi mantido como backup.

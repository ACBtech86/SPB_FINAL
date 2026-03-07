# Guia: Instalação do MFC no Visual Studio

**Data:** 22/02/2026
**Problema:** `fatal error C1083: Não é possível abrir arquivo 'afx.h'`
**Causa:** MFC (Microsoft Foundation Classes) não instalado

---

## 📋 O Que é MFC?

MFC é uma biblioteca de classes C++ da Microsoft usada para desenvolvimento de aplicações Windows.
O projeto BCSrvSqlMq depende do MFC para:
- Gerenciamento de janelas e UI
- Classes de coleção (CString, CObArray, etc.)
- Suporte a banco de dados (CRecordset)

---

## 🔧 Como Instalar MFC

### Opção A: Modificar Instalação Existente (Recomendado)

1. **Abrir Visual Studio Installer**
   - Menu Iniciar → Procurar "Visual Studio Installer"
   - Ou baixar de: https://visualstudio.microsoft.com/downloads/

2. **Modificar Instalação**
   - Clicar em "Modify" (Modificar) ao lado do Visual Studio 18 Community

3. **Adicionar Componentes MFC**
   - Aba "Workloads":
     - ✅ Marcar "Desktop development with C++"

   - Aba "Individual components":
     - ✅ C++ MFC for latest v143 build tools (x86 & x64)
     - ✅ C++ MFC for latest v143 build tools with Spectre Mitigations (opcional)
     - ✅ C++ ATL for latest v143 build tools (x86 & x64)

4. **Instalar**
   - Clicar em "Modify" (Modificar)
   - Aguardar instalação (~10-20 minutos dependendo da conexão)

5. **Verificar Instalação**
   - Após concluir, verificar se `afx.h` existe:
   ```powershell
   dir "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\*\atlmfc\include\afx.h"
   ```

---

### Opção B: Reinstalar Visual Studio Build Tools

Se preferir usar apenas Build Tools (sem IDE):

1. Download: https://visualstudio.microsoft.com/downloads/
2. Procurar: "Build Tools for Visual Studio 2022" (ou 2025)
3. Durante instalação, selecionar:
   - ✅ Desktop development with C++
   - ✅ C++ MFC for latest v143 build tools (x86 & x64)

---

## ✅ Após Instalação do MFC

Execute os seguintes comandos para testar:

```powershell
# 1. Navegar até o projeto
cd C:\BCSrvSqlMq

# 2. Limpar build anterior
Remove-Item -Recurse -Force build

# 3. Reconfigurar
powershell -ExecutionPolicy Bypass -File build_test.ps1

# 4. Compilar
powershell -ExecutionPolicy Bypass -File compile.ps1
```

---

## 📊 Checklist de Verificação

Antes de compilar, verificar:

- [ ] Visual Studio 18 instalado
- [ ] Componente "Desktop development with C++" instalado
- [ ] MFC libraries instaladas
- [ ] ATL libraries instaladas (opcional mas recomendado)
- [ ] Windows SDK instalado
- [ ] vcpkg configurado (C:\dev\vcpkg)
- [ ] pugixml instalado via vcpkg
- [ ] OpenSSL instalado via vcpkg

---

## 🎯 Componentes Necessários (Resumo)

| Componente | Status | Localização |
|------------|--------|-------------|
| Visual Studio 18 | ✅ Instalado | C:\Program Files\Microsoft Visual Studio\18 |
| MFC | ❌ NÃO INSTALADO | Precisa instalar |
| vcpkg | ✅ Instalado | C:\dev\vcpkg |
| pugixml | ✅ Instalado | vcpkg |
| OpenSSL | ✅ Instalado | vcpkg |
| Projeto migrado | ✅ Completo | C:\BCSrvSqlMq |

---

## ⏰ Tempo Estimado

- Download componentes MFC: 5-10 minutos
- Instalação MFC: 10-20 minutos
- Verificação e teste: 5 minutos

**Total:** ~20-35 minutos

---

## 📞 Próximos Passos

1. **Instalar MFC** (seguir guia acima)
2. **Verificar instalação** (procurar afx.h)
3. **Recompilar projeto** (build_test.ps1 + compile.ps1)
4. **Continuar com Fase 6** (migração de código)

---

**Status Atual:** ⏸️ Aguardando instalação do MFC

**Última atualização:** 22/02/2026 - 17:00

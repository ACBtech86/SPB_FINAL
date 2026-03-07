# Guia de Setup - Fase 6: Modernização de Bibliotecas

**Data:** 22/02/2026
**Versão:** 1.0.5

---

## 📋 Visão Geral

A Fase 6 substitui duas bibliotecas legadas por equivalentes modernos:

| Biblioteca Atual | Versão | Biblioteca Nova | Versão | Razão |
|-----------------|--------|-----------------|--------|-------|
| **MSXML** (COM) | ~2001 | **pugixml** | Latest | Performance, simplicidade, sem COM |
| **CryptLib** | 2001 | **OpenSSL** | 3.2+ | Segurança, manutenção ativa, padrão |

---

## ⚡ Instalação Rápida

### Opção 1: Script Automatizado (Recomendado)

Execute o script PowerShell fornecido:

```powershell
# Abrir PowerShell como Administrador
cd "c:\Users\AntonioBosco\OneDrive - Finvest\Área de Trabalho\SPBCidade\SPB1\SPB Fontes Producao\BCSrvSqlMq"

# Executar script
.\install_dependencies.ps1
```

O script irá:
- ✅ Instalar vcpkg (se necessário)
- ✅ Instalar pugixml:x64-windows
- ✅ Instalar openssl:x64-windows
- ✅ Atualizar CMakeLists.txt automaticamente
- ✅ Reconfigurar o projeto (opcional)

**Tempo estimado:** 15-20 minutos (depende da conexão de internet)

---

### Opção 2: Instalação Manual

#### Passo 1: Instalar vcpkg

```bash
# Clone vcpkg
cd C:\dev
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg

# Bootstrap
.\bootstrap-vcpkg.bat

# Integrar com Visual Studio
.\vcpkg integrate install
```

#### Passo 2: Instalar Bibliotecas

```bash
# pugixml (rápido ~2 min)
vcpkg install pugixml:x64-windows

# OpenSSL (demorado ~10-15 min)
vcpkg install openssl:x64-windows
```

#### Passo 3: Atualizar CMakeLists.txt

Adicionar no início do arquivo:

```cmake
# vcpkg toolchain
set(CMAKE_TOOLCHAIN_FILE "C:/dev/vcpkg/scripts/buildsystems/vcpkg.cmake")
```

Adicionar após `project()`:

```cmake
# Dependências modernas
find_package(pugixml CONFIG REQUIRED)
find_package(OpenSSL REQUIRED)
```

Atualizar `target_link_libraries()`:

```cmake
target_link_libraries(BCSrvSqlMq
    pugixml
    OpenSSL::SSL
    OpenSSL::Crypto
    # ... outras libs ...
)
```

#### Passo 4: Reconfigurar Projeto

```bash
cmake -B build -S . -G "Visual Studio 17 2022" -A x64
```

---

## 📦 Verificação da Instalação

### Verificar Bibliotecas Instaladas

```bash
cd C:\dev\vcpkg
.\vcpkg list | findstr /i "pugixml openssl"
```

**Saída esperada:**
```
pugixml:x64-windows       1.14#2          Light-weight, simple and fast XML parser for C++
openssl:x64-windows       3.2.4           OpenSSL is an open source project that provides a robust...
```

### Testar Compilação

```bash
cd "c:\Users\AntonioBosco\OneDrive - Finvest\Área de Trabalho\SPBCidade\SPB1\SPB Fontes Producao\BCSrvSqlMq"

# Limpar build anterior
rmdir /s /q build

# Reconfigurar
cmake -B build -S . -G "Visual Studio 17 2022" -A x64

# Compilar
cmake --build build --config Release
```

**Compilação OK?**
- ✅ **SIM:** Pode prosseguir para a migração de código
- ❌ **NÃO:** Verifique os logs de erro e consulte a seção "Troubleshooting" abaixo

---

## 🔧 Troubleshooting

### Erro: "vcpkg: command not found"

**Problema:** vcpkg não está no PATH

**Solução:**
```powershell
# Adicionar vcpkg ao PATH (temporário)
$env:PATH += ";C:\dev\vcpkg"

# Ou permanente (System Properties > Environment Variables)
# Adicionar C:\dev\vcpkg ao PATH do sistema
```

---

### Erro: "Could not find OpenSSL"

**Problema:** CMake não encontra o OpenSSL instalado pelo vcpkg

**Solução 1:** Verificar se CMAKE_TOOLCHAIN_FILE está definido
```cmake
set(CMAKE_TOOLCHAIN_FILE "C:/dev/vcpkg/scripts/buildsystems/vcpkg.cmake")
```

**Solução 2:** Definir manualmente
```bash
cmake -B build -S . -G "Visual Studio 17 2022" -A x64 ^
  -DCMAKE_TOOLCHAIN_FILE=C:/dev/vcpkg/scripts/buildsystems/vcpkg.cmake
```

---

### Erro: "pugixml.hpp: No such file"

**Problema:** Headers não encontrados

**Solução:** Verificar instalação do pugixml
```bash
vcpkg install pugixml:x64-windows --recurse
```

---

### Erro: Compilação de OpenSSL falha

**Problema:** OpenSSL requer Perl e NASM

**Solução:**
1. Instalar Strawberry Perl: https://strawberryperl.com/
2. Instalar NASM: https://www.nasm.us/
3. Reinstalar OpenSSL:
```bash
vcpkg remove openssl:x64-windows
vcpkg install openssl:x64-windows
```

---

### Erro: "Access Denied" ao instalar vcpkg

**Problema:** Sem permissões de administrador

**Solução:**
1. Fechar PowerShell
2. Abrir PowerShell como Administrador (botão direito > "Run as Administrator")
3. Reexecutar o script

---

## 📚 Próximos Passos

Após a instalação bem-sucedida:

1. **Ler documentação detalhada:**
   - [DEPENDENCY_ANALYSIS_PHASE6.md](DEPENDENCY_ANALYSIS_PHASE6.md) - Análise completa de dependências

2. **Migração de código:**
   - Fase 6.2: MSXML → pugixml (~8-12 horas)
   - Fase 6.3: CryptLib → OpenSSL (~20-30 horas)

3. **Testes:**
   - Validar parse de XML
   - Validar operações criptográficas
   - Testes de compatibilidade com Bacen

---

## 📞 Suporte

**Problemas?**
1. Consulte: [DEPENDENCY_ANALYSIS_PHASE6.md](DEPENDENCY_ANALYSIS_PHASE6.md) - Seção "Troubleshooting"
2. Verifique os logs de build em: `build/CMakeFiles/CMakeError.log`
3. Comunidade vcpkg: https://github.com/microsoft/vcpkg/issues

---

## 📊 Checklist de Instalação

Use esta checklist para verificar o progresso:

- [ ] vcpkg instalado e no PATH
- [ ] vcpkg integrate install executado
- [ ] pugixml:x64-windows instalado
- [ ] openssl:x64-windows instalado
- [ ] CMakeLists.txt atualizado com CMAKE_TOOLCHAIN_FILE
- [ ] CMakeLists.txt atualizado com find_package(pugixml)
- [ ] CMakeLists.txt atualizado com find_package(OpenSSL)
- [ ] CMakeLists.txt atualizado com target_link_libraries
- [ ] Projeto reconfigura sem erros (cmake -B build)
- [ ] Projeto compila sem erros (cmake --build build)

**Tudo OK?** ✅ Pronto para migração de código!

---

**Última atualização:** 22/02/2026
**Autor:** Claude Sonnet 4.5

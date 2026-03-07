# vcpkg toolchain (Fase 6: Modernização de Bibliotecas)
# Procura vcpkg na variável de ambiente VCPKG_ROOT ou no caminho padrão
if(DEFINED ENV{VCPKG_ROOT})
    set(CMAKE_TOOLCHAIN_FILE "$ENV{VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake" CACHE STRING "vcpkg toolchain file")
elseif(EXISTS "C:/dev/vcpkg/scripts/buildsystems/vcpkg.cmake")
    set(CMAKE_TOOLCHAIN_FILE "C:/dev/vcpkg/scripts/buildsystems/vcpkg.cmake" CACHE STRING "vcpkg toolchain file")
else()
    message(WARNING "vcpkg não encontrado. Defina VCPKG_ROOT ou instale em C:/dev/vcpkg")
endif()

cmake_minimum_required(VERSION 3.20)
project(BCSrvSqlMq VERSION 1.0.6 LANGUAGES CXX)

# Configuração C++20
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# MFC Support (Shared DLL)
set(CMAKE_MFC_FLAG 2)

# Adicionar includes do ATL/MFC manualmente (necessário para VS 2026/2022)
if(MSVC)
    # Procurar por versões do MSVC que tenham ATL/MFC instalado (VS 2026 e VS 2022)
    file(GLOB MSVC_VERSIONS
        "C:/Program Files/Microsoft Visual Studio/18/*/VC/Tools/MSVC/*"
        "C:/Program Files/Microsoft Visual Studio/2022/*/VC/Tools/MSVC/*"
    )

    set(MSVC_WITH_MFC "")
    foreach(MSVC_VER ${MSVC_VERSIONS})
        if(EXISTS "${MSVC_VER}/atlmfc/include")
            set(MSVC_WITH_MFC "${MSVC_VER}")
            break()
        endif()
    endforeach()

    if(MSVC_WITH_MFC)
        include_directories("${MSVC_WITH_MFC}/atlmfc/include")
        if(CMAKE_SIZEOF_VOID_P EQUAL 8)
            link_directories("${MSVC_WITH_MFC}/atlmfc/lib/x64")
        else()
            link_directories("${MSVC_WITH_MFC}/atlmfc/lib/x86")
        endif()
        message(STATUS "ATL/MFC Found: ${MSVC_WITH_MFC}/atlmfc")
    else()
        message(WARNING "ATL/MFC includes não encontrados em nenhuma versão do MSVC. Verifique se o workload 'Desktop development with C++' está instalado com ATL/MFC.")
    endif()
endif()

# Fase 6: Bibliotecas modernas (pugixml + OpenSSL)
find_package(pugixml CONFIG REQUIRED)
find_package(OpenSSL REQUIRED)

# Definições do Windows
add_compile_definitions(
    _WIN32_WINNT=0x0A00  # Windows 10/11
    WIN32
    _CONSOLE
    _MBCS
    _AFXDLL
    NOCRYPT    # Fase 6: Evitar conflito entre cryptlib.h e wincrypt.h
    NOMINMAX   # Fase 6: Evitar conflito min/max macros do Windows com std::min/std::max
)

# Configuração Debug/Release
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    add_compile_definitions(_DEBUG)
else()
    add_compile_definitions(NDEBUG)
endif()

# Incluir diretórios
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
)

# IBM MQ 9.4.5.0 instalado em C:/Program Files/IBM/MQ
if(EXISTS "C:/Program Files/IBM/MQ/tools/c/include")
    include_directories("C:/Program Files/IBM/MQ/tools/c/include")
    if(CMAKE_SIZEOF_VOID_P EQUAL 8)
        link_directories("C:/Program Files/IBM/MQ/tools/lib64")
    else()
        link_directories("C:/Program Files/IBM/MQ/tools/lib")
    endif()
    set(MQ_FOUND TRUE)
    message(STATUS "IBM MQ Found: C:/Program Files/IBM/MQ")
elseif(EXISTS "C:/Program Files (x86)/IBM/WebSphereMQ/tools/c/include")
    include_directories("C:/Program Files (x86)/IBM/WebSphereMQ/tools/c/include")
    link_directories("C:/Program Files (x86)/IBM/WebSphereMQ/tools/Lib")
    set(MQ_FOUND TRUE)
    message(STATUS "IBM MQ Found (legacy): C:/Program Files (x86)/IBM/WebSphereMQ")
else()
    message(WARNING "IBM MQ não encontrado. Ajuste os paths manualmente.")
    set(MQ_FOUND FALSE)
endif()

# Arquivos fonte
set(SOURCES
    ntservapp.cpp
    ntservice.cpp
    MainSrv.cpp
    InitSrv.cpp
    Monitor.cpp
    ThreadMQ.cpp
    BacenREQ.cpp
    BacenRSP.cpp
    BacenRep.cpp
    BacenSup.cpp
    IFREQ.cpp
    IFRSP.cpp
    IFREP.cpp
    IFSUP.cpp
    BacenAppRS.cpp
    IFAppRS.cpp
    ControleRS.cpp
    STRLogRS.cpp
    OpenSSLWrapper.cpp
)

# Arquivos header
set(HEADERS
    ntservapp.h
    ntservice.h
    ntservmsg.h
    MainSrv.h
    InitSrv.h
    Monitor.h
    ThreadMQ.h
    BacenReq.h
    BacenRsp.h
    BacenRep.h
    BacenSup.h
    IFReq.h
    IFRsp.h
    IFRep.h
    IFSup.h
    BacenAppRS.h
    IFAppRS.h
    ControleRS.h
    STRLogRS.h
    CBCDb.h
    MsgSgr.h
    Resource.h
    OpenSSLWrapper.h
    crypto_compat.h
    cmqc.h
)

# Recursos
set(RESOURCES
    BCSrvSqlMq.rc
)

# Executável principal
add_executable(BCSrvSqlMq ${SOURCES} ${HEADERS} ${RESOURCES})

# Libraries Windows padrão + Fase 6 (pugixml + OpenSSL)
target_link_libraries(BCSrvSqlMq
    # Fase 6: Bibliotecas modernas
    pugixml::pugixml
    OpenSSL::SSL
    OpenSSL::Crypto
    # Windows padrão
    Ws2_32.lib
    kernel32.lib
    user32.lib
    gdi32.lib
    winspool.lib
    comdlg32.lib
    advapi32.lib
    shell32.lib
    ole32.lib
    oleaut32.lib
    uuid.lib
    odbc32.lib
    odbccp32.lib
    ucrt.lib
    msvcrt.lib
    legacy_stdio_definitions.lib
)

# IBM MQ Library
if(MQ_FOUND)
    target_link_libraries(BCSrvSqlMq mqm.lib)
else()
    message(WARNING "MQ library não será linkada automaticamente")
endif()

# CryptLib (biblioteca local) - REMOVIDO - Migrado para OpenSSL
# A migração para OpenSSL permite compilação x64 nativa
# OpenSSL já está linkado nas linhas 161-162 (OpenSSL::SSL e OpenSSL::Crypto)
#if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/CL32.lib")
#    target_link_libraries(BCSrvSqlMq ${CMAKE_CURRENT_SOURCE_DIR}/CL32.lib)
#else()
#    message(WARNING "CL32.lib não encontrada no diretório do projeto")
#endif()

# Opções de compilação
target_compile_options(BCSrvSqlMq PRIVATE
    /W3          # Warning level 3
    /MP          # Multi-processor compilation
    /EHsc        # Exception handling
    /permissive- # Standards conformance
)

# Propriedades adicionais
set_target_properties(BCSrvSqlMq PROPERTIES
    VS_DEBUGGER_WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
)

# Mensagens de configuração
message(STATUS "=====================================")
message(STATUS "BCSrvSqlMq - Build Configuration")
message(STATUS "=====================================")
message(STATUS "C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "MFC Support: Shared DLL")
message(STATUS "IBM MQ Found: ${MQ_FOUND}")
message(STATUS "=====================================")

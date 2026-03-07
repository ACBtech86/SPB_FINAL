# BCMsgSqlMq - x64 Logging DLL
# Created: 2026-02-27

cmake_minimum_required(VERSION 3.20)
project(BCMsgSqlMq)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Define the DLL
add_library(BCMsgSqlMq SHARED
    BCMsgSqlMq.cpp
    BCMsgSqlMq.h
)

# Define export macro
target_compile_definitions(BCMsgSqlMq PRIVATE BCMSGSQLMQ_EXPORTS)

# Set output name to match original DLL
set_target_properties(BCMsgSqlMq PROPERTIES
    OUTPUT_NAME "BCMsgSqlMq"
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_BINARY_DIR}/Release"
)

# Windows specific settings
if(WIN32)
    # Set subsystem
    set_target_properties(BCMsgSqlMq PROPERTIES
        LINK_FLAGS "/SUBSYSTEM:WINDOWS"
    )
endif()
